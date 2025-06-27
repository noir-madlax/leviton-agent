"""Database-integrated Product Segmentation service (v7.0)

Re-implemented to leverage the generic three-stage taxonomy pipeline used by
unit-tests:
  • ExtractionStage         – per-batch taxonomy extraction
  • ConsolidationStage      – progressive taxonomy consolidation
  • RefinementStage         – batched assignment refinement

All LLM interaction happens inside these stage helpers, mirroring the exact
control-flow exercised by
  backend/product_segment/tests/llm/test_taxonomy_extraction.py,
  backend/product_segment/tests/llm/test_taxonomy_consolidation.py and
  backend/product_segment/tests/llm/test_taxonomy_refinement.py

The service retains the same public interface (create_run / execute_run) and
continues to persist intermediate artefacts through the provided Supabase
repositories.
"""

from __future__ import annotations

import logging
import math
import secrets
from datetime import datetime
from typing import Callable, Dict, List, Optional

from core.utils.batching import make_batches
from product_segment import config as seg_cfg
from product_segment.llm.taxonomy_consolidation import (
    ConsolidationStage,
    ConsolidationStageContext,
)
from product_segment.llm.taxonomy_dedup_uitl import (
    deduplicate_taxonomy_batches,
)
from product_segment.llm.taxonomy_extraction import (
    ExtractionStage,
    ExtractionStageContext,
    TaxonomyDTO,
)
from product_segment.llm.taxonomy_refinement import (
    RefinementStage,
    RefinementStageContext,
)
from product_segment.models import (
    ProductSegmentAssignment,
    ProductSegmentRun,
    ProductSegmentTaxonomy,
    SegmentationStage,
    StartSegmentationRequest,
)
from product_segment.repositories.product_segment_assignment_repository import (
    ProductSegmentRepository,
)
from product_segment.repositories.product_segment_run_repository import (
    SegmentationRunRepository,
)
from product_segment.repositories.product_segment_taxonomy_repository import (
    ProductTaxonomyRepository,
)

logger = logging.getLogger(__name__)


class DatabaseProductSegmentationService:  # noqa: WPS230 – orchestrator is inevitably long
    """Orchestrates Extraction → Consolidation → Refinement using LLM stages."""

    # ---------------------------------------------------------------------
    # Construction helpers
    # ---------------------------------------------------------------------

    def __init__(
        self,
        run_repo: SegmentationRunRepository,
        segment_repo: ProductSegmentRepository,
        taxonomy_repo: ProductTaxonomyRepository,
        *,
        title_fetcher: Optional[Callable[[int], str]] = None,
    ) -> None:
        self._run_repo = run_repo
        self._segment_repo = segment_repo
        self._taxonomy_repo = taxonomy_repo
        # Fallback title-fetcher just converts the product-id to a placeholder str.
        self._title_fetcher: Callable[[int], str] = title_fetcher or (lambda pid: f"Product {pid}")

        # Stage instances are **stateless**, safe to keep around.
        self._extraction_stage = ExtractionStage()
        self._consolidation_stage = ConsolidationStage()
        self._refinement_stage = RefinementStage()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def create_run(self, request: StartSegmentationRequest) -> str:
        """Insert DB rows for a new segmentation run and its placeholder data."""
        run_id = (
            f"RUN_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(2)}"
        )

        # 1) Run row ----------------------------------------------------------------
        run = ProductSegmentRun(
            id=run_id,
            project_id=request.project_id,
            stage=SegmentationStage.INIT,
            llm_config={},  # default global config
            processing_params={"batch_size": seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT,
                               "product_category": request.product_category},
        )
        await self._run_repo.create(run)

        # 2) Special taxonomies ------------------------------------------------------
        unassigned_id = await self._taxonomy_repo.create_taxonomy(
            ProductSegmentTaxonomy(
                run_id=run_id,
                segment_name="__UNASSIGNED__",
                definition="Auto-generated placeholder",
                stage="init",
            )
        )

        # 3) Assignment rows ---------------------------------------------------------
        # 处理ASIN字符串到product_id的转换 - 批量查询优化
        converted_product_ids = []
        asin_list = [pid for pid in request.product_ids if isinstance(pid, str)]
        int_list = [pid for pid in request.product_ids if isinstance(pid, int)]
        
        # 批量查询所有ASIN
        if asin_list:
            try:
                from core.database.connection import get_supabase_client
                supabase = get_supabase_client()
                result = supabase.table('product_wide_table')\
                    .select('id, platform_id')\
                    .in_('platform_id', asin_list)\
                    .execute()
                
                if result.data:
                    asin_to_id = {row['platform_id']: row['id'] for row in result.data}
                    for asin in asin_list:
                        if asin in asin_to_id:
                            converted_product_ids.append(asin_to_id[asin])
                        else:
                            logger.warning(f"No product found for ASIN {asin}")
                else:
                    logger.warning(f"No products found for ASINs: {asin_list}")
            except Exception as e:
                logger.error(f"Error converting ASINs to product_ids: {e}")
        
        # 添加已经是整数的product_id
        converted_product_ids.extend(int_list)
        
        assignments = [
            ProductSegmentAssignment(
                run_id=run_id,
                project_id=request.project_id,
                product_id=pid,
                taxonomy_id_initial=unassigned_id,
                taxonomy_id_refined=unassigned_id,
                segment_name=None
            )
            for pid in converted_product_ids
        ]
        await self._segment_repo.batch_create_assignments(assignments)

        return run_id

    # ------------------------------------------------------------------
    # Main orchestration
    # ------------------------------------------------------------------

    async def execute_run(self, run_id: str) -> None:  # noqa: C901 – complexity expected
        """Run Extraction → Consolidation → Refinement end-to-end."""
        try:
            run = await self._run_repo.get_by_id(run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")

            # ------------------------------------------------------------------
            # Gather input data
            # ------------------------------------------------------------------
            product_ids: List[int] = await self._segment_repo.get_run_products(run_id)
            if not product_ids:
                raise ValueError(f"No products found for run {run_id}")

            product_titles: List[str] = [self._title_fetcher(pid) for pid in product_ids]

            # ------------------------------------------------------------------
            # Calculate rough call budget (pre-extraction)
            # ------------------------------------------------------------------
            seg_batches = math.ceil(
                len(product_titles) / seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT
            )
            ref_batches = math.ceil(len(product_titles) / seg_cfg.PRODUCTS_PER_REFINEMENT)
            # Consolidation calls are approximated pessimistically (n-1)
            consolidation_calls_est = max(0, seg_batches - 1)
            calls_done = 0


            # Mapping helpers -----------------------------------------------------
            taxonomy_name_to_id: Dict[str, int] = {}
            product_id_to_taxonomy: Dict[int, str] = {}
            # Tracks every *direct* merge seen during consolidation. Key = old
            # taxonomy name, value = the immediate merge target.  Will be
            # collapsed to its canonical (final) representative after all
            # consolidation passes finish.
            raw_merge_map: Dict[str, str] = {}

            # ------------------------------------------------------------------
            # 1) Extraction Stage
            # ------------------------------------------------------------------
            await self._run_repo.update_stage(run_id, SegmentationStage.EXTRACTION)

            # Pair (id, title) to keep them together through the shuffling in make_batches
            product_pairs: List[tuple[int, str]] = list(zip(product_ids, product_titles))
            extraction_batches = make_batches(
                product_pairs, seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT
            )
            batch_taxonomies: List[List[TaxonomyDTO]] = []

            for batch_idx, batch in enumerate(extraction_batches):
                batch_product_ids = [pid for pid, _ in batch]
                batch_titles = [title for _, title in batch]

                ctx = ExtractionStageContext(
                    product_category=run.processing_params.get('product_category', ''),
                    input_texts=batch_titles,
                )
                result = await self._extraction_stage.execute(ctx)

                # Insert new taxonomies (extraction stage)
                new_tax_entries: List[ProductSegmentTaxonomy] = []
                for tax in result.taxonomies_extracted:
                    if tax.name not in taxonomy_name_to_id:
                        new_tax_entries.append(
                            ProductSegmentTaxonomy(
                                run_id=run_id,
                                segment_name=tax.name,
                                definition=tax.definition,
                                stage="extraction",
                            )
                        )
                if new_tax_entries:
                    new_ids = await self._taxonomy_repo.batch_create_taxonomies(
                        new_tax_entries
                    )
                    for entry, tid in zip(new_tax_entries, new_ids):
                        taxonomy_name_to_id[entry.segment_name] = tid

                # Persist initial assignments
                for local_idx, taxonomy_name in result.assignments_initial.items():
                    product_id = batch_product_ids[local_idx]
                    product_id_to_taxonomy[product_id] = taxonomy_name
                    taxonomy_id = taxonomy_name_to_id.get(taxonomy_name)
                    if taxonomy_id:
                        await self._segment_repo.update_initial_taxonomy(
                            run_id, product_id, taxonomy_id
                        )
                        # Default refined assignment to the initial taxonomy –
                        # this ensures every product has a *refined* category
                        # even when the refinement stage performs **no**
                        # reassignments.
                        await self._segment_repo.update_refined_taxonomy(
                            run_id, product_id, taxonomy_id,
                        )

                batch_taxonomies.append(result.taxonomies_extracted)

            # ------------------------------------------------------------------
            # 2) Consolidation Stage
            # ------------------------------------------------------------------
            await self._run_repo.update_stage(run_id, SegmentationStage.CONSOLIDATION)

            # Deduplicate inside + across batches to minimise LLM calls
            dedup_batches = deduplicate_taxonomy_batches(batch_taxonomies)
            if not dedup_batches:
                raise RuntimeError("No taxonomies extracted – cannot consolidate")

            current_consolidated: List[TaxonomyDTO] = dedup_batches[0]
            for batch in dedup_batches[1:]:
                ctx = ConsolidationStageContext(
                    product_category=run.processing_params.get('product_category', ''),
                    taxonomy_a=current_consolidated,
                    taxonomy_b=batch,
                )
                res = await self._consolidation_stage.execute(ctx)
                current_consolidated = [c.taxonomy for c in res.taxonomies_consolidated]

                # ------------------------------------------------------------------
                # Record mapping old_name → new_name for *every* merge so we can
                # later rewrite product assignments in one shot.
                # ------------------------------------------------------------------
                for cons in res.taxonomies_consolidated:
                    new_name = cons.taxonomy.name
                    # Identity mapping for the consolidated category itself –
                    # needed so _canonical below terminates for untouched names.
                    raw_merge_map.setdefault(new_name, new_name)

                    for orig in cons.original_taxonomies:
                        raw_merge_map[orig.name] = new_name

            final_taxonomies: List[TaxonomyDTO] = current_consolidated

            # Persist final taxonomies -----------------------------------------
            new_final_entries: List[ProductSegmentTaxonomy] = []
            for tax in final_taxonomies:
                if tax.name not in taxonomy_name_to_id:
                    new_final_entries.append(
                        ProductSegmentTaxonomy(
                            run_id=run_id,
                            segment_name=tax.name,
                            definition=tax.definition,
                            stage="final",
                        )
                    )
            if new_final_entries:
                new_ids = await self._taxonomy_repo.batch_create_taxonomies(
                    new_final_entries
                )
                for entry, tid in zip(new_final_entries, new_ids):
                    taxonomy_name_to_id[entry.segment_name] = tid

            # ------------------------------------------------------------------
            # Build *canonical* mapping (follow chains A→B→C→… ⇒ A→C, B→C, …)
            # and update all in-memory & persisted assignments exactly once.
            # ------------------------------------------------------------------

            def _canonical(name: str) -> str:
                """Collapse raw_merge_map chains to their final representative."""
                seen: set[str] = set()
                while raw_merge_map.get(name) and raw_merge_map[name] != name:
                    if name in seen:  # should not happen, safeguard against loops
                        break
                    seen.add(name)
                    name = raw_merge_map[name]
                return name

            canonical_map: Dict[str, str] = {k: _canonical(k) for k in raw_merge_map}

            # Rewrite in-memory mapping and batch DB updates for changed products
            for pid, old_name in list(product_id_to_taxonomy.items()):
                new_name = canonical_map.get(old_name, old_name)

                if new_name == old_name:
                    continue  # unchanged

                product_id_to_taxonomy[pid] = new_name

                # Ensure the consolidated taxonomy exists in DB → taxonomy_name_to_id
                if new_name not in taxonomy_name_to_id:
                    new_tid = await self._taxonomy_repo.create_taxonomy(
                        ProductSegmentTaxonomy(
                            run_id=run_id,
                            segment_name=new_name,
                            definition="",  # definition already captured in final_taxonomies or unknown
                            stage="final",
                        )
                    )
                    taxonomy_name_to_id[new_name] = new_tid

                tax_id = taxonomy_name_to_id[new_name]

                # Persist both initial & refined taxonomy columns so that the
                # database reflects the consolidated taxonomy *before* the
                # refinement stage begins.
                await self._segment_repo.update_initial_taxonomy(run_id, pid, tax_id)
                await self._segment_repo.update_refined_taxonomy(run_id, pid, tax_id)

            # ------------------------------------------------------------------
            # 3) Refinement Stage
            # ------------------------------------------------------------------
            await self._run_repo.update_stage(run_id, SegmentationStage.REFINEMENT)

            batch_size = seg_cfg.PRODUCTS_PER_REFINEMENT
            for offset in range(0, len(product_titles), batch_size):
                batch_titles = product_titles[offset : offset + batch_size]
                batch_assignments = {}
                for idx, title in enumerate(batch_titles):
                    global_product_idx = offset + idx
                    product_id = product_ids[global_product_idx]
                    batch_assignments[idx] = product_id_to_taxonomy.get(
                        product_id, "__UNASSIGNED__"
                    )

                ctx = RefinementStageContext(
                    product_category=run.processing_params.get('product_category', ''),
                    taxonomies=final_taxonomies,
                    current_assignments=batch_assignments,
                    input_texts=batch_titles,
                )
                res = await self._refinement_stage.execute(ctx)

                # Persist reassignments --------------------------------------
                for local_idx, new_tax_name in res.reassignments.items():
                    global_idx = offset + local_idx
                    product_id = product_ids[global_idx]

                    # Ensure taxonomy exists in DB
                    if new_tax_name not in taxonomy_name_to_id:
                        new_id = await self._taxonomy_repo.create_taxonomy(
                            ProductSegmentTaxonomy(
                                run_id=run_id,
                                segment_name=new_tax_name,
                                definition="",  # definition unknown at this point
                                stage="refined",
                            )
                        )
                        taxonomy_name_to_id[new_tax_name] = new_id

                    taxonomy_id = taxonomy_name_to_id[new_tax_name]
                    await self._segment_repo.update_refined_taxonomy(
                        run_id, product_id, taxonomy_id
                    )

            # ------------------------------------------------------------------
            # Update segment_name in assignments table
            # ------------------------------------------------------------------
            await self._update_final_segment_names(run_id, product_id_to_taxonomy)

            # ------------------------------------------------------------------
            # Done!
            # ------------------------------------------------------------------
            await self._run_repo.update_stage(run_id, SegmentationStage.COMPLETED)

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Run %s failed: %s", run_id, exc)
            await self._run_repo.update_stage(run_id, SegmentationStage.FAILED)
            raise

    async def _update_final_segment_names(self, run_id: str, product_id_to_taxonomy: Dict[int, str]) -> None:
        """更新最终的细分名称到assignments表"""
        for product_id, segment_name in product_id_to_taxonomy.items():
            await self._segment_repo.update_segment_name(run_id, product_id, segment_name) 