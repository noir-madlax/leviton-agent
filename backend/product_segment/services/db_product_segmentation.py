"""Database-integrated Product Segmentation service (v7.0)

Re-implemented to leverage the generic three-stage taxonomy pipeline used by
unit-tests:
  • ProductExtractionStage     – per-batch taxonomy extraction
  • ProductConsolidationStage  – progressive taxonomy consolidation
  • ProductRefinementStage     – batched assignment refinement

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

import asyncio
import logging
import math
import secrets
from datetime import datetime
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Awaitable,
)

from core.utils.batching import make_batches
from product_segment import config as seg_cfg
from product_segment.llm import (
    TaxonomyDTO,
    ProductExtractionStageResult,
    ProductExtractionStageContext,
    ProductExtractionStage,
    ConsolidatedTaxonomyDTO,
    ProductConsolidationStageResult,
    ProductConsolidationStageContext,
    ProductConsolidationStage,
    ProductRefinementStageResult,
    ProductRefinementStageContext,
    ProductRefinementStage,
    deduplicate_taxonomies,
    deduplicate_taxonomy_batches,
    print_deduplication_summary,
    DeduplicationResult,
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

from core.database.connection import get_supabase_service_client

logger = logging.getLogger(__name__)


async def get_product_title(product_id: int) -> str:
    """Fetch product title from product_wide_table by product ID."""
    try:
        sb_client = get_supabase_service_client()
        result = (
            sb_client.table("product_wide_table")
            .select("title")
            .eq("id", product_id)
            .single()
            .execute()
        )
        return result.data.get("title", f"Product {product_id}") if result.data else f"Product {product_id}"
    except Exception as e:
        logger.warning(f"Failed to get title for product {product_id}: {e}")
        return f"Product {product_id}"


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
        title_fetcher: Optional[Callable[[int], Awaitable[str]]] = None,
    ) -> None:
        self._run_repo = run_repo
        self._segment_repo = segment_repo
        self._taxonomy_repo = taxonomy_repo
        # Fallback title-fetcher just converts the product-id to a placeholder str.
        async def _default_title_fetcher(pid: int) -> str:
            return f"Product {pid}"

        self._title_fetcher = title_fetcher or _default_title_fetcher

        # Stage instances are **stateless**, safe to keep around.
        self._extraction_stage = ProductExtractionStage()
        self._consolidation_stage = ProductConsolidationStage()
        self._refinement_stage = ProductRefinementStage()

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

            # --- Fetch product titles for the current batch ---
            product_titles = await asyncio.gather(
                *[self._title_fetcher(pid) for pid in product_ids]
            )
            product_id_titles = list(zip(product_ids, product_titles))
            # ------------------------------------------------------------------
            # Calculate rough call budget (pre-extraction)
            # ------------------------------------------------------------------
            total_products = len(product_ids)
            seg_batches = math.ceil(
                len(product_titles) / seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT
            )
            ref_batches = math.ceil(len(product_titles) / seg_cfg.PRODUCTS_PER_REFINEMENT)
            # Consolidation calls are approximated pessimistically (n-1)
            consolidation_calls_est = max(0, seg_batches - 1)
            
            # 🔥 Update run with total counts before starting
            await self._run_repo.update_run_progress(
                run_id,
                total_products=total_products,
                extraction_batches_total=seg_batches,
                consolidation_batches_total=consolidation_calls_est,
                refinement_batches_total=ref_batches,
            )
            
            logger.info(f"🚀 Starting product segmentation run {run_id}: {total_products} products, {seg_batches} extraction batches, {consolidation_calls_est} consolidation batches, {ref_batches} refinement batches")

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
            extraction_batches = make_batches(
                product_id_titles, seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT
            )
            batch_taxonomies: List[List[TaxonomyDTO]] = []

            for batch_idx, batch in enumerate(extraction_batches):
                batch_product_ids = [pid for pid, _ in batch]
                batch_titles = [title for _, title in batch]

                ctx = ProductExtractionStageContext(
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

                # 🔥 Update progress after each extraction batch
                batches_done = batch_idx + 1
                await self._run_repo.update_run_progress(run_id, extraction_batches_done=batches_done)
                
                progress_pct = (batches_done / seg_batches) * 100
                logger.info(f"🔄 Extraction batch {batches_done}/{seg_batches} ({progress_pct:.1f}%) completed for run {run_id}")

            # ------------------------------------------------------------------
            # 2) Consolidation Stage
            # ------------------------------------------------------------------
            await self._run_repo.update_stage(run_id, SegmentationStage.CONSOLIDATION)

            # Deduplicate inside + across batches to minimise LLM calls
            dedup_batches = deduplicate_taxonomy_batches(batch_taxonomies)
            if not dedup_batches:
                raise RuntimeError("No taxonomies extracted – cannot consolidate")

            current_consolidated: List[TaxonomyDTO] = dedup_batches[0]
            consolidation_batch_idx = 0
            for batch_idx, batch in enumerate(dedup_batches[1:]):
                ctx = ProductConsolidationStageContext(
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

                # 🔥 Update progress after each consolidation batch
                consolidation_batch_idx = batch_idx + 1
                await self._run_repo.update_run_progress(run_id, consolidation_batches_done=consolidation_batch_idx)
                
                progress_pct = (consolidation_batch_idx / consolidation_calls_est) * 100 if consolidation_calls_est > 0 else 100
                logger.info(f"🔄 Consolidation batch {consolidation_batch_idx}/{consolidation_calls_est} ({progress_pct:.1f}%) completed for run {run_id}")

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
            refinement_batch_idx = 0
            for offset in range(0, len(product_titles), batch_size):
                batch_titles = product_titles[offset : offset + batch_size]

                ctx = ProductRefinementStageContext(
                    product_category=run.processing_params.get('product_category', ''),
                    taxonomies=final_taxonomies,
                    input_texts=batch_titles,
                )
                res = await self._refinement_stage.execute(ctx)

                # Persist assignments --------------------------------------
                for local_idx, new_tax_name in res.assignments.items():
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

                # 🔥 Update progress after each refinement batch
                refinement_batch_idx += 1
                await self._run_repo.update_run_progress(run_id, refinement_batches_done=refinement_batch_idx)
                
                progress_pct = (refinement_batch_idx / ref_batches) * 100
                logger.info(f"🔄 Refinement batch {refinement_batch_idx}/{ref_batches} ({progress_pct:.1f}%) completed for run {run_id}")

            # ------------------------------------------------------------------
            # Update segment_name in assignments table
            # ------------------------------------------------------------------
            await self._update_final_segment_names(run_id, product_id_to_taxonomy)

            # ------------------------------------------------------------------
            # Done!
            # ------------------------------------------------------------------
            final_assigned_count = len([
                tax for tax in product_id_to_taxonomy.values()
                if tax != "__UNASSIGNED__"
            ])
            await self._run_repo.update_run_progress(
                run_id,
                processed_products=final_assigned_count,
            )
            await self._run_repo.update_stage(run_id, SegmentationStage.COMPLETED)

        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Run %s failed: %s", run_id, exc)
            await self._run_repo.update_stage(run_id, SegmentationStage.FAILED)
            raise

    async def _update_final_segment_names(self, run_id: str, product_id_to_taxonomy: Dict[int, str]) -> None:
        """Update segment_name in assignments table based on final taxonomy mapping."""
        
        # Invert the map for easier lookup
        taxonomy_to_product_ids: Dict[str, List[int]] = {}
        for pid, tax_name in product_id_to_taxonomy.items():
            taxonomy_to_product_ids.setdefault(tax_name, []).append(pid)
            
        # Batch updates by segment name
        for tax_name, pids in taxonomy_to_product_ids.items():
            if tax_name == "__UNASSIGNED__":
                continue
            await self._segment_repo.batch_update_segment_name(run_id, pids, tax_name)

 