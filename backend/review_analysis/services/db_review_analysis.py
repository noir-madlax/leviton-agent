from __future__ import annotations

"""Database-integrated Review-Analysis service (v0.1).

This orchestration service reuses the generic four-stage taxonomy pipeline:
  • ReviewExtractionStage      – per-batch aspect extraction
  • ReviewCategorizationStage  – batch aspect categorisation
  • ReviewConsolidationStage   – iterative category consolidation
  • ReviewRefinementStage      – final assignment refinement

Only the DB-persistence glue code lives here – the heavy LLM logic remains
inside the pipeline stage helpers so this module stays fairly small.
"""

import logging
import secrets
from datetime import datetime
from typing import Dict, List, Any, Tuple

from review_analysis.models import (
    ReviewAnalysisRequest,
    Aspect,
    AspectOccurrence,
)
from review_analysis.llm import (  # noqa: F401 – some imported for future stages
    ReviewExtractionStage,
    ReviewExtractionContext,
    ReviewExtractionResult,
    ReviewCategorizationStage,
    ReviewCategorizationStageContext,
    ReviewConsolidationStage,
    ReviewConsolidationStageContext,
    ReviewRefinementStage,
    ReviewRefinementStageContext,
)
from review_analysis.repositories.aspect_repository import AspectRepository
from review_analysis.repositories.aspect_occurrence_repository import (
    AspectOccurrenceRepository,
)
from review_analysis.repositories.aspect_category_repository import (
    AspectCategoryRepository,
)
from core.database.connection import get_supabase_client
from review_analysis.llm.review_extraction_stage import format_reviews_for_prompt
from review_analysis import config as ra_cfg
from core.utils.batching import make_batches
from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO

logger = logging.getLogger(__name__)


class DatabaseReviewAnalysisService:  # noqa: WPS230 – orchestrator is inevitably long
    """Orchestrates Extraction → Categorisation → Consolidation → Refinement."""

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def __init__(self) -> None:
        sb_client = get_supabase_client()

        # Repositories ---------------------------------------------------
        self._aspect_repo = AspectRepository(sb_client)
        self._occ_repo = AspectOccurrenceRepository(sb_client)
        self._cat_repo = AspectCategoryRepository(sb_client)

        # Stage instances are stateless, safe to keep around -------------
        self._extraction_stage = ReviewExtractionStage()
        self._categorisation_stage = ReviewCategorizationStage()
        self._consolidation_stage = ReviewConsolidationStage()
        self._refinement_stage = ReviewRefinementStage()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def analyse(self, request: ReviewAnalysisRequest) -> str:  # noqa: D401
        """Run the full review-analysis pipeline for *request*.

        Returns a unique *analysis_id* that can be used by downstream code to
        look up results (the ID is **not** persisted – we simply use it as a
        convenient correlation handle for log files / storage paths).
        """
        analysis_id = (
            f"ANA_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(2)}"
        )

        logger.info("▶️  Starting review-analysis %s for %d products", analysis_id, len(request.product_ids))

        # ------------------------------------------------------------------
        # 0) Load reviews for all products (SQL ‑> Supabase) -----------------
        # ------------------------------------------------------------------
        sb = get_supabase_client()
        review_rows: List[Dict] = []
        try:
            review_rows = (
                sb.table("product_reviews")
                .select("product_id, review_id, review_title, review_text")
                .in_("product_id", request.product_ids)
                .limit(10_000)  # hard safety cap
                .execute()
                .data
                or []
            )
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to load product reviews: %s", exc)
            raise

        if not review_rows:
            logger.warning("No reviews found – nothing to analyse")
            return analysis_id

        # ------------------------------------------------------------------
        # 1) Extraction Stage  ---------------------------------------------
        # ------------------------------------------------------------------
        # For simplicity we bundle **all** reviews of a product into one batch
        # because the extraction prompt already supports multiple reviews.
        # ------------------------------------------------------------------
        reviews_by_product: Dict[str, List[Dict]] = {}
        for row in review_rows:
            reviews_by_product.setdefault(row["product_id"], []).append(row)

        for product_id, rows in reviews_by_product.items():
            # Deduplicate identical review texts -------------------------
            seen_texts: set[str] = set()
            unique_reviews: List[Dict[str, str]] = []
            for r in rows:
                title = r.get("review_title", "") or ""
                body = r.get("review_text", "") or ""
                dedup_key = f"{title}|||{body}"
                if dedup_key in seen_texts:
                    continue
                seen_texts.add(dedup_key)
                unique_reviews.append(r)

            # Build input string: "RID#review" per prompt spec
            input_block, expected_ids = format_reviews_for_prompt(
                [
                    {"title": r.get("review_title", ""), "text": r.get("review_text", "")}
                    for r in unique_reviews
                ]
            )

            ctx = ReviewExtractionContext(
                product_category=request.product_category,
                formatted_reviews=input_block,
                expected_review_ids=set(expected_ids),
                asin=str(product_id),
                product_title=str(product_id),
            )
            result: ReviewExtractionResult = await self._extraction_stage.execute(ctx)

            # Persist aspects & occurrences ------------------------------
            await self._persist_extraction_result(request.project_id, product_id, result.review_hierarchy)

        # TODO: Categorisation, consolidation, refinement persistence     
        #       The skeleton ends here – add later as needed.              
        logger.info("✅ Review-analysis %s completed extraction stage", analysis_id)

        # ------------------------------------------------------------------
        # 2) Categorisation Stage (per aspect_type) -------------------------
        # ------------------------------------------------------------------
        await self._run_categorisation(request)
        logger.info("✅ Review-analysis %s completed categorisation stage", analysis_id)

        # 3) Consolidation Stage -------------------------------------------
        await self._run_consolidation(request.project_id)
        logger.info("✅ Review-analysis %s completed consolidation stage", analysis_id)

        # 4) Refinement Stage ----------------------------------------------
        await self._run_refinement(request.project_id)
        logger.info("✅ Review-analysis %s completed refinement stage", analysis_id)

        return analysis_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _persist_extraction_result(self, project_id: str, product_id: str, hierarchy: Dict[str, Any]) -> None:  # noqa: D401 – internal
        """Flatten *hierarchy* into aspect / occurrence rows and persist them."""
        from review_analysis.models import ExtractionResult  # local import to avoid cycle

        extraction = ExtractionResult(product_id=product_id, extraction_data=hierarchy)

        aspects: List[Aspect] = []
        occurrences: List[AspectOccurrence] = []

        # Track unique aspects to avoid duplicates
        unique_aspects: Dict[tuple, Aspect] = {}  # Key: (aspect_type, local_id)
        
        # First pass – create unique Aspect rows -------------------------
        for node in extraction.get_all_aspects():
            aspect_key = (node["aspect_type"], node["aspect_id"])
            
            if aspect_key not in unique_aspects:
                unique_aspects[aspect_key] = Aspect(
                    project_id=project_id,
                    product_id=product_id,
                    aspect_type={"physical": "phy", "performance": "perf", "usability": "use"}[node["aspect_type"]],
                    local_id=node["aspect_id"],
                    parent_group_name=node["aspect_category"],
                    detail_text=node["aspect_description"],
                )

        # Convert to list for insertion
        aspects = list(unique_aspects.values())
        
        aspect_pks = await self._aspect_repo.batch_insert(aspects)
        
        # Validate that aspect insertion was successful
        if len(aspect_pks) != len(aspects):
            logger.error(
                f"Aspect insertion failed: expected {len(aspects)} PKs, got {len(aspect_pks)}. "
                f"Aspects: {[a.local_id for a in aspects]}, PKs: {aspect_pks}"
            )
            raise RuntimeError(f"Failed to insert all aspects: expected {len(aspects)}, got {len(aspect_pks)}")
        
        pk_map = {a.local_id: pk for a, pk in zip(aspects, aspect_pks)}
        logger.info(f"Created pk_map: {pk_map}")

        # Second pass – build occurrences ---------------------------------
        for node in extraction.get_all_aspects():
            aspect_id = node["aspect_id"]
            if aspect_id not in pk_map:
                logger.error(f"Missing aspect_id '{aspect_id}' in pk_map. Available keys: {list(pk_map.keys())}")
                raise KeyError(f"aspect_id '{aspect_id}' not found in pk_map")
                
            aspect_pk = pk_map[aspect_id]
            causes_pks = [pk_map.get(cid) for cid in node["reasons"] if pk_map.get(cid) is not None]

            for review_id in node["review_ids"]:
                occ = AspectOccurrence(
                    aspect_pk=aspect_pk,
                    review_id=str(review_id),
                    sentiment=node["sentiment"],
                    causes=causes_pks,
                )
                occurrences.append(occ)

        await self._occ_repo.batch_insert([o.model_dump() for o in occurrences])

    # ------------------------------------------------------------------
    # Categorisation flow
    # ------------------------------------------------------------------

    async def _run_categorisation(self, request: "ReviewAnalysisRequest") -> None:  # noqa: D401
        """Run the categorisation stage for each aspect_type and persist categories."""

        sb = get_supabase_client()
        aspect_type_map = ra_cfg.ASPECT_TYPE_MAP

        for aspect_code, (human_name, aspect_context) in aspect_type_map.items():
            # Gather aspects without a category yet (category_pk is null)
            query = (
                sb.table("review_analysis_aspects")
                .select("aspect_pk, local_id, parent_group_name, detail_text")
                .eq("aspect_type", aspect_code)
                .eq("project_id", request.project_id)
                .is_("category_pk", "null")
            )
            rows = query.execute().data or []

            if not rows:
                continue

            # Batch the rows for prompt size limits
            batches = make_batches(rows, ra_cfg.ASPECTS_PER_CATEGORISATION_PROMPT)

            for batch in batches:
                aspects_for_prompt: List[Tuple[str, str]] = []
                for idx, row in enumerate(batch):
                    prompt_id = str(idx)
                    desc = f"{row['parent_group_name']} – {row['detail_text']}"
                    aspects_for_prompt.append((prompt_id, desc))

                ctx = ReviewCategorizationStageContext(
                    product_category=request.product_category,
                    aspect_type=human_name,
                    aspect_context=aspect_context,
                    input_description="[ID] aspect description",
                    product_categories=set(),
                    aspects=aspects_for_prompt,
                )

                result = await self._categorisation_stage.execute(ctx)

                # Persist categories from this batch
                cat_rows = [
                    {
                        "project_id": request.project_id,
                        "aspect_type": aspect_code,
                        "name": tax.name,
                        "definition": tax.definition,
                        "stage": "categorisation",
                    }
                    for tax in result.taxonomies_categorised
                ]

                if cat_rows:
                    _ = await self._cat_repo.batch_insert(cat_rows)

            # Assignments will be handled in refinement stage later 

    async def _run_consolidation(self, project_id: str) -> None:  # noqa: D401
        """Progressively merge unc­onsolidated categories per aspect_type."""

        sb = get_supabase_client()
        aspect_type_map = ra_cfg.ASPECT_TYPE_MAP

        for aspect_code, (_human, _ctx_desc) in aspect_type_map.items():
            # Pull all categories for this project / aspect
            rows = (
                sb.table("review_analysis_aspect_categories")
                .select("category_pk, name, definition")
                .eq("project_id", project_id)
                .eq("aspect_type", aspect_code)
                .execute()
                .data
                or []
            )

            if len(rows) <= 1:
                continue

            # Build list[TaxonomyDTO]
            cat_dtos = [TaxonomyDTO(name=r["name"], definition=r["definition"]) for r in rows]

            # Split evenly sized batches but **progressively** merge: A + B -> C, C + D -> E ...
            batches = make_batches(cat_dtos, ra_cfg.CATEGORIES_PER_CONSOLIDATION_PROMPT)
            current_consolidated = batches[0]

            for batch in batches[1:]:
                ctx = ReviewConsolidationStageContext(
                    product_category="",
                    taxonomy_a=current_consolidated,
                    taxonomy_b=batch,
                )
                res = await self._consolidation_stage.execute(ctx)
                current_consolidated = [c.taxonomy for c in res.taxonomies_consolidated]

                # TODO: persist mapping between originals and new names (similar to product segmentation)

            # Final consolidated categories in current_consolidated – ensure they exist in DB
            # Simplified: upsert them as stage="final"
            up_rows = [
                {
                    "project_id": project_id,
                    "aspect_type": aspect_code,
                    "name": tax.name,
                    "definition": tax.definition,
                    "stage": "final",
                }
                for tax in current_consolidated
            ]
            await self._cat_repo.batch_insert(up_rows) 

    # ------------------------------------------------------------------
    # Refinement flow
    # ------------------------------------------------------------------

    async def _run_refinement(self, project_id: str) -> None:  # noqa: D401
        """Run final refinement assigning each aspect to consolidated categories."""

        sb = get_supabase_client()
        aspect_type_map = ra_cfg.ASPECT_TYPE_MAP

        for aspect_code, (human_name, aspect_context) in aspect_type_map.items():
            # Load aspects (always include already assigned so OUT_OF_SCOPE can be handled)
            rows = (
                sb.table("review_analysis_aspects")
                .select("aspect_pk, detail_text, category_pk")
                .eq("project_id", project_id)
                .eq("aspect_type", aspect_code)
                .execute()
                .data
                or []
            )
            if not rows:
                continue

            # Load categories (should be stage="final")
            cat_rows = (
                sb.table("review_analysis_aspect_categories")
                .select("category_pk, name, definition")
                .eq("project_id", project_id)
                .eq("aspect_type", aspect_code)
                .execute()
                .data
                or []
            )
            if not cat_rows:
                continue

            cat_list = [TaxonomyDTO(name=r["name"], definition=r["definition"]) for r in cat_rows]
            # Build helper maps
            name_to_pk = {r["name"]: r["category_pk"] for r in cat_rows}

            # Batch aspects
            batches = make_batches(rows, ra_cfg.ASPECTS_PER_REFINEMENT_PROMPT)

            for batch in batches:
                aspects_desc = [r["detail_text"] for r in batch]
                ctx = ReviewRefinementStageContext(
                    product_category="",
                    aspect_type=human_name,
                    aspect_context=aspect_context,
                    categories=cat_list,
                    aspects=aspects_desc,
                )
                res = await self._refinement_stage.execute(ctx)

                # Apply reassignments
                for idx, cat_name in res.reassignments.items():
                    idx_int = int(idx)
                    aspect_row = batch[idx_int]
                    aspect_pk = aspect_row["aspect_pk"]

                    if cat_name == "OUT_OF_SCOPE":
                        continue  # leave category_pk as null

                    cat_pk = name_to_pk.get(cat_name)
                    if cat_pk is None:
                        # Create new category row
                        new_rows = [
                            {
                                "project_id": project_id,
                                "aspect_type": aspect_code,
                                "name": cat_name,
                                "definition": "",  # undefined yet
                                "stage": "refinement",
                            }
                        ]
                        new_ids = await self._cat_repo.batch_insert(new_rows)
                        if new_ids:
                            cat_pk = new_ids[0]
                            name_to_pk[cat_name] = cat_pk
                    if cat_pk:
                        await self._aspect_repo.update_category(aspect_pk, cat_pk) 