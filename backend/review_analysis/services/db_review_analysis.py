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
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple, Optional, Callable, Awaitable

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
from review_analysis.llm.hierarchy_merger import merge_hierarchies_batch_with_mappings
from review_analysis import review_analysis_config as ra_cfg
from core.utils.batching import make_batches
from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO, StageProtocolError
from core.utils.llm_utils import LLMCallError

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


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

    async def analyse(
        self, request: ReviewAnalysisRequest, progress_callback: Optional[ProgressCallback] = None
    ) -> str:  # noqa: D401
        """Run the full review-analysis pipeline for *request*.

        Returns a unique *analysis_id* that can be used by downstream code to
        look up results (the ID is **not** persisted – we simply use it as a
        convenient correlation handle for log files / storage paths).
        """
        analysis_id = (
            f"ANA_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(2)}"
        )
        
        async def _send_progress(step: str, status: str, **kwargs):
            if progress_callback:
                payload = {"step": step, "status": status, **kwargs}
                await progress_callback(payload)

        logger.info("▶️  Starting review-analysis %s for %d products", analysis_id, len(request.product_ids))

        # ------------------------------------------------------------------
        # 0) Load all available reviews (SQL ‑> Supabase) ---------------------
        # ------------------------------------------------------------------
        sb = get_supabase_client()
        review_rows: List[Dict] = []
        
        logger.info(f"📥 Loading all available reviews for {len(request.product_ids)} products")
        
        try:
            review_rows = (
                sb.table("product_reviews")
                .select("product_id, review_id, review_title, review_text, rating")
                .in_("product_id", request.product_ids)
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
            
        logger.info(f"✅ Loaded {len(review_rows)} reviews from {len(request.product_ids)} products")

        # ------------------------------------------------------------------
        # 1) Extraction Stage with Progress Tracking  ----------------------
        # ------------------------------------------------------------------
        extraction_start_time = datetime.now(timezone.utc)
        
        # For simplicity we bundle **all** reviews of a product into one batch
        # because the extraction prompt already supports multiple reviews.
        # ------------------------------------------------------------------
        reviews_by_product: Dict[str, List[Dict]] = {}
        for row in review_rows:
            reviews_by_product.setdefault(row["product_id"], []).append(row)

        total_products = len(reviews_by_product)
        total_batches_estimated = 0
        
        # Pre-calculate total batches for progress tracking
        for product_id, rows in reviews_by_product.items():
            unique_count = len(set(f"{r.get('review_title', '')}|||{r.get('review_text', '')}" for r in rows))
            batch_count = (unique_count + ra_cfg.REVIEWS_PER_EXTRACTION_PROMPT - 1) // ra_cfg.REVIEWS_PER_EXTRACTION_PROMPT
            total_batches_estimated += batch_count
            
        # 🔥 Update database with total batch counts
        await _send_progress("extraction", "in_progress", progress_current=0, progress_total=total_batches_estimated, details={"message": f"Starting extraction ({total_products} products)..."})
        
        # Update the run record with batch totals
        if progress_callback:
            await progress_callback({
                "step": "initialization",
                "status": "in_progress", 
                "details": {
                    "extraction_batches_total": total_batches_estimated,
                    "total_products": total_products,
                    "message": f"Initialized: {total_products} products, {total_batches_estimated} extraction batches"
                }
            })
            
        logger.info(f"🚀 Starting extraction: {total_products} products, ~{total_batches_estimated} LLM calls estimated")
        
        current_product_idx = 0
        current_batch_global = 0
        
        for product_id, rows in reviews_by_product.items():
            current_product_idx += 1
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

            # Split reviews into batches for prompt size management -------
            review_batches = make_batches(unique_reviews, ra_cfg.REVIEWS_PER_EXTRACTION_PROMPT)
            
            # Process each batch of reviews for this product -------------
            all_hierarchies: List[Dict[str, Any]] = []
            all_review_mappings: List[Dict[int, str]] = []  # Track review ID mappings for each batch
            
            for batch_idx, batch in enumerate(review_batches):
                current_batch_global += 1
                
                # --- ETA Calculation ---
                eta_seconds = None
                if current_batch_global > 0:
                    elapsed_seconds = (datetime.now(timezone.utc) - extraction_start_time).total_seconds()
                    avg_time_per_batch = elapsed_seconds / current_batch_global
                    remaining_batches = total_batches_estimated - current_batch_global
                    if remaining_batches > 0:
                        eta_seconds = int(avg_time_per_batch * remaining_batches)

                # Progress logging
                progress_pct = (current_batch_global / total_batches_estimated) * 100 if total_batches_estimated > 0 else 0
                logger.info(f"🔄 Extraction batch {current_batch_global}/{total_batches_estimated} ({progress_pct:.1f}%) - Product {current_product_idx}/{total_products}, batch {batch_idx + 1}/{len(review_batches)} for analysis {analysis_id}")
                
                # Enhanced details for frontend display
                details = {
                    "message": f"Extraction ({current_batch_global}/{total_batches_estimated} batches)",
                    "current_product": current_product_idx,
                    "total_products": total_products,
                    "current_batch": current_batch_global,
                    "total_batches": total_batches_estimated,
                    "progress_percentage": round(progress_pct, 1),
                    "extraction_batches_done": current_batch_global,
                    "extraction_batches_total": total_batches_estimated
                }
                if eta_seconds is not None:
                    details["eta_seconds"] = eta_seconds

                await _send_progress(
                    "extraction", 
                    "in_progress", 
                    progress_current=current_batch_global,
                    progress_total=total_batches_estimated,
                    details=details
                )
                
                # Create review ID mapping for this batch (batch_index -> actual_review_id)
                review_id_mapping = {
                    idx: review["review_id"] 
                    for idx, review in enumerate(batch)
                }
                all_review_mappings.append(review_id_mapping)
                
                # Build input string: "RID#review" per prompt spec (still uses 0,1,2...)
                input_block, expected_ids = format_reviews_for_prompt(
                    [
                        {"title": r.get("review_title", ""), "text": r.get("review_text", "")}
                        for r in batch
                    ]
                )

                ctx = ReviewExtractionContext(
                    product_category=request.product_category,
                    formatted_reviews=input_block,
                    expected_review_ids=set(expected_ids),
                    asin=str(product_id),
                    product_title=str(product_id),
                )
                
                # Try extraction with validation error handling
                try:
                    result: ReviewExtractionResult = await self._extraction_stage.execute(ctx)
                    all_hierarchies.append(result.review_hierarchy)
                    logger.info(f"✅ Batch {batch_idx + 1}/{len(review_batches)} extraction succeeded for product {product_id}")
                    
                except (LLMCallError, StageProtocolError) as exc:
                    # LLM validation failed - create placeholder entry for progress tracking
                    logger.warning(f"🚨 LLM validation failed for batch {batch_idx + 1}/{len(review_batches)} of product {product_id}: {exc}")
                    
                    # Create placeholder hierarchy with error aspects for progress tracking
                    error_hierarchy = await self._create_error_placeholder_hierarchy(
                        batch, review_id_mapping, str(exc)
                    )
                    all_hierarchies.append(error_hierarchy)
                    logger.info(f"📝 Created error placeholder for batch {batch_idx + 1}/{len(review_batches)} of product {product_id}")

            # Merge all batch hierarchies with proper index offsetting ----
            merged_hierarchy, global_review_mapping = merge_hierarchies_batch_with_mappings(
                all_hierarchies, all_review_mappings
            )

            # Persist aspects & occurrences with actual review IDs --------
            await self._persist_extraction_result(request.project_id, product_id, merged_hierarchy, global_review_mapping)

        # TODO: Categorisation, consolidation, refinement persistence     
        #       The skeleton ends here – add later as needed.              
        logger.info("✅ Review-analysis %s completed extraction stage", analysis_id)
        await _send_progress("extraction", "completed", progress_current=total_batches_estimated, progress_total=total_batches_estimated)

        # ------------------------------------------------------------------
        # 2) Categorisation Stage (per aspect_type) -------------------------
        # ------------------------------------------------------------------
        await _send_progress("categorization", "in_progress", details={
            "message": "Categorization (organizing aspects)",
            "current_product": total_products,
            "total_products": total_products
        })
        await self._run_categorisation(request)
        logger.info("✅ Review-analysis %s completed categorisation stage", analysis_id)
        await _send_progress("categorization", "completed")

        # 3) Consolidation Stage -------------------------------------------
        await _send_progress("consolidation", "in_progress", details={
            "message": "Consolidation (merging categories)",
            "current_product": total_products,
            "total_products": total_products
        })
        await self._run_consolidation(request.project_id)
        logger.info("✅ Review-analysis %s completed consolidation stage", analysis_id)
        await _send_progress("consolidation", "completed")

        # 4) Refinement Stage ----------------------------------------------
        await _send_progress("refinement", "in_progress", details={
            "message": f"Refinement ({total_products}/{total_products} assigned)",
            "current_product": total_products,
            "total_products": total_products
        })
        await self._run_refinement(request.project_id)
        logger.info("✅ Review-analysis %s completed refinement stage", analysis_id)
        await _send_progress("refinement", "completed")

        return analysis_id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _create_error_placeholder_hierarchy(
        self,
        batch: List[Dict],
        review_id_mapping: Dict[int, str],
        error_message: str
    ) -> Dict[str, Any]:
        """Create a placeholder hierarchy when LLM validation fails.
        
        This ensures progress tracking sees 'aspects' even when extraction fails,
        by creating error placeholder entries that can be tracked in the database.
        """
        logger.info(f"🏗️ Creating error placeholder hierarchy for {len(batch)} reviews")
        
        # Create minimal error placeholder hierarchy with one aspect per review
        placeholder_hierarchy = {
            "phy": {
                "extraction_errors": {}
            },
            "perf": {},
            "use": {}
        }
        
        # Create one error aspect per review for progress tracking
        for idx, review in enumerate(batch):
            review_id = review_id_mapping.get(idx, f"unknown_{idx}")
            error_detail = f"LLM_EXTRACTION_ERROR: {error_message[:100]}..."
            
            # Create a unique aspect ID for this error
            aspect_key = f"ERROR_{idx}@{error_detail}"
            
            # Add to placeholder hierarchy
            placeholder_hierarchy["phy"]["extraction_errors"][aspect_key] = {
                "+": [],  # No positive sentiment for errors
                "-": [idx]  # Mark as negative sentiment with this review ID
            }
        
        logger.info(f"📝 Created placeholder hierarchy with {len(batch)} error aspects")
        return placeholder_hierarchy

    async def _persist_extraction_result(self, project_id: str, product_id: str, hierarchy: Dict[str, Any], review_mapping: Dict[int, str]) -> None:  # noqa: D401
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
                # Check if this is an error placeholder aspect
                is_error_aspect = node["aspect_id"].startswith("ERROR_")
                aspect_detail = node["aspect_description"]
                
                if is_error_aspect:
                    # Mark error aspects clearly in the database
                    aspect_detail = f"[EXTRACTION_FAILED] {aspect_detail}"
                    logger.info(f"📝 Creating error aspect entry: {node['aspect_id']}")
                
                unique_aspects[aspect_key] = Aspect(
                    project_id=project_id,
                    product_id=product_id,
                    aspect_type={"physical": "phy", "performance": "perf", "usability": "use"}[node["aspect_type"]],
                    local_id=node["aspect_id"],
                    parent_group_name=node["aspect_category"],
                    detail_text=aspect_detail,
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

            for review_index in node["review_ids"]:
                # Convert batch index to actual review ID using the mapping
                actual_review_id = review_mapping.get(review_index)
                if actual_review_id is None:
                    logger.error(f"Missing review index {review_index} in review_mapping. Available keys: {list(review_mapping.keys())}")
                    raise KeyError(f"review_index {review_index} not found in review_mapping")
                
                occ = AspectOccurrence(
                    aspect_pk=aspect_pk,
                    review_id=str(actual_review_id),
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
            # Include error aspects for consistent progress tracking
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

            # Separate error aspects from normal aspects for different handling
            normal_aspects = []
            error_aspects = []
            
            for row in rows:
                if row['detail_text'].startswith('[EXTRACTION_FAILED]'):
                    error_aspects.append(row)
                else:
                    normal_aspects.append(row)

            # Process normal aspects through categorisation
            if normal_aspects:
                await self._process_normal_categorisation(
                    normal_aspects, request, aspect_code, human_name, aspect_context
                )

            # Handle error aspects by creating a special error category
            if error_aspects:
                await self._process_error_categorisation(
                    error_aspects, request, aspect_code
                )

    async def _process_normal_categorisation(
        self, 
        aspects: List[Dict], 
        request: "ReviewAnalysisRequest", 
        aspect_code: str, 
        human_name: str, 
        aspect_context: str
    ) -> None:
        """Process normal aspects through LLM categorisation."""
        # Batch the rows for prompt size limits
        batches = make_batches(aspects, ra_cfg.ASPECTS_PER_CATEGORISATION_PROMPT)

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

            try:
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
                    inserted_pks = await self._cat_repo.batch_insert(cat_rows)
                    logger.info(f"✅ Processed {len(cat_rows)} categories for {aspect_code}, got {len(inserted_pks)} PKs")
                    
                    # Log any missing PKs for debugging
                    if len(inserted_pks) != len(cat_rows):
                        missing_count = len(cat_rows) - len(inserted_pks)
                        logger.warning(f"⚠️ {missing_count} categories may have failed insertion (likely duplicates) for {aspect_code}")
                        category_names = [row["name"] for row in cat_rows]
                        logger.debug(f"📝 Category names attempted: {category_names}")

            except (LLMCallError, StageProtocolError) as exc:
                # Categorisation LLM validation failed - create placeholder category
                logger.warning(f"🚨 Categorisation LLM validation failed for {aspect_code}: {exc}")
                await self._create_placeholder_category(
                    request.project_id, aspect_code, "categorisation", str(exc)
                )

    async def _process_error_categorisation(
        self,
        error_aspects: List[Dict],
        request: "ReviewAnalysisRequest", 
        aspect_code: str
    ) -> None:
        """Handle error aspects by creating a special error category."""
        try:
            # Use get_or_create to avoid duplicates
            error_category_pk = await self._cat_repo.get_or_create_category(
                project_id=request.project_id,
                aspect_type=aspect_code,
                name="EXTRACTION_ERRORS",
                stage="categorisation",
                definition=f"Aspects that failed LLM extraction validation for {aspect_code} type"
            )
            logger.info(f"📝 Got/created error category (PK: {error_category_pk}) for {len(error_aspects)} failed {aspect_code} aspects")
        except Exception as exc:
            logger.exception(f"❌ Failed to get/create error category for {aspect_code}: {exc}")
            raise

    async def _create_placeholder_category(
        self,
        project_id: str,
        aspect_code: str,
        stage: str,
        error_message: str
    ) -> None:
        """Create a placeholder category when LLM categorisation fails."""
        try:
            # Use get_or_create to avoid duplicates
            placeholder_category_pk = await self._cat_repo.get_or_create_category(
                project_id=project_id,
                aspect_type=aspect_code,
                name=f"CATEGORISATION_FAILED_{stage.upper()}",
                stage=stage,
                definition=f"Placeholder category for failed LLM categorisation: {error_message[:100]}..."
            )
            logger.info(f"📝 Got/created placeholder category (PK: {placeholder_category_pk}) for failed {aspect_code} categorisation")
        except Exception as exc:
            logger.exception(f"❌ Failed to get/create placeholder category for {aspect_code}: {exc}")
            raise

    async def _run_consolidation(self, project_id: str) -> None:  # noqa: D401
        """Progressively merge unc­onsolidated categories per aspect_type."""

        sb = get_supabase_client()
        aspect_type_map = ra_cfg.ASPECT_TYPE_MAP

        for aspect_code, (_human, _ctx_desc) in aspect_type_map.items():
            # Pull ONLY categorisation stage categories for this project / aspect
            rows = (
                sb.table("review_analysis_aspect_categories")
                .select("category_pk, name, definition")
                .eq("project_id", project_id)
                .eq("aspect_type", aspect_code)
                .eq("stage", "categorisation")
                .execute()
                .data
                or []
            )

            if len(rows) <= 1:
                # Not enough categories to consolidate, just copy to final stage
                if rows:
                    final_rows = [
                        {
                            "project_id": project_id,
                            "aspect_type": aspect_code,
                            "name": rows[0]["name"],
                            "definition": rows[0]["definition"],
                            "stage": "final",
                        }
                    ]
                    await self._cat_repo.batch_insert(final_rows)
                continue

            # Build list[TaxonomyDTO] - exclude error categories from consolidation
            cat_dtos = []
            error_categories = []
            
            for r in rows:
                if r["name"].startswith(("EXTRACTION_ERRORS", "CATEGORISATION_FAILED")):
                    error_categories.append(r)
                else:
                    cat_dtos.append(TaxonomyDTO(name=r["name"], definition=r["definition"]))

            if not cat_dtos:
                # Only error categories exist, copy them to final stage
                final_rows = [
                    {
                        "project_id": project_id,
                        "aspect_type": aspect_code,
                        "name": cat["name"],
                        "definition": cat["definition"],
                        "stage": "final",
                    }
                    for cat in error_categories
                ]
                if final_rows:
                    await self._cat_repo.batch_insert(final_rows)
                continue

            # Split evenly sized batches but **progressively** merge: A + B -> C, C + D -> E ...
            batches = make_batches(cat_dtos, ra_cfg.CATEGORIES_PER_CONSOLIDATION_PROMPT)
            current_consolidated = batches[0]

            try:
                for batch in batches[1:]:
                    ctx = ReviewConsolidationStageContext(
                        product_category="",
                        taxonomy_a=current_consolidated,
                        taxonomy_b=batch,
                    )
                    res = await self._consolidation_stage.execute(ctx)
                    current_consolidated = [c.taxonomy for c in res.taxonomies_consolidated]

                    # TODO: persist mapping between originals and new names (similar to product segmentation)

                # Insert final consolidated categories with stage="final"
                final_rows = [
                    {
                        "project_id": project_id,
                        "aspect_type": aspect_code,
                        "name": tax.name,
                        "definition": tax.definition,
                        "stage": "final",
                    }
                    for tax in current_consolidated
                ]
                
                # Also add error categories to final stage
                error_final_rows = [
                    {
                        "project_id": project_id,
                        "aspect_type": aspect_code,
                        "name": cat["name"],
                        "definition": cat["definition"],
                        "stage": "final",
                    }
                    for cat in error_categories
                ]
                
                all_final_rows = final_rows + error_final_rows
                if all_final_rows:
                    await self._cat_repo.batch_insert(all_final_rows)
                    logger.info(f"✅ Consolidated {len(final_rows)} categories + {len(error_final_rows)} error categories for {aspect_code}")

            except (LLMCallError, StageProtocolError) as exc:
                # Consolidation LLM validation failed - copy categories to final stage as-is
                logger.warning(f"🚨 Consolidation LLM validation failed for {aspect_code}: {exc}")
                final_rows = [
                    {
                        "project_id": project_id,
                        "aspect_type": aspect_code,
                        "name": tax.name,
                        "definition": tax.definition,
                        "stage": "final",
                    }
                    for tax in cat_dtos
                ] + [
                    {
                        "project_id": project_id,
                        "aspect_type": aspect_code,
                        "name": cat["name"],
                        "definition": cat["definition"],
                        "stage": "final",
                    }
                    for cat in error_categories
                ]
                if final_rows:
                    await self._cat_repo.batch_insert(final_rows)

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
                .select("aspect_pk, detail_text, category_pk, parent_group_name")
                .eq("project_id", project_id)
                .eq("aspect_type", aspect_code)
                .execute()
                .data
                or []
            )
            if not rows:
                continue

            # Load categories from stage="final" only
            cat_rows = (
                sb.table("review_analysis_aspect_categories")
                .select("category_pk, name, definition")
                .eq("project_id", project_id)
                .eq("aspect_type", aspect_code)
                .eq("stage", "final")
                .execute()
                .data
                or []
            )
            if not cat_rows:
                continue

            # Separate normal and error categories
            normal_categories = []
            error_category_pk = None
            
            for cat in cat_rows:
                if cat["name"].startswith(("EXTRACTION_ERRORS", "CATEGORISATION_FAILED")):
                    error_category_pk = cat["category_pk"]
                else:
                    normal_categories.append(cat)

            # Separate normal and error aspects
            normal_aspects = []
            error_aspects = []
            
            for row in rows:
                if row['detail_text'].startswith('[EXTRACTION_FAILED]'):
                    error_aspects.append(row)
                else:
                    normal_aspects.append(row)

            # Assign error aspects directly to error category
            if error_aspects and error_category_pk:
                for aspect in error_aspects:
                    await self._aspect_repo.update_category(aspect["aspect_pk"], error_category_pk)
                logger.info(f"📝 Assigned {len(error_aspects)} error aspects to error category for {aspect_code}")

            # Process normal aspects through refinement if we have normal categories
            if normal_aspects and normal_categories:
                cat_list = [TaxonomyDTO(name=r["name"], definition=r["definition"]) for r in normal_categories]
                name_to_pk = {r["name"]: r["category_pk"] for r in normal_categories}

                # Create OUT_OF_SCOPE category for this aspect type
                try:
                    out_of_scope_pk = await self._cat_repo.get_or_create_category(
                        project_id=project_id,
                        aspect_type=aspect_code,
                        name="OUT_OF_SCOPE",
                        stage="final",
                        definition=f"Aspects that do not fit well into any category for {aspect_code} type"
                    )
                    name_to_pk["OUT_OF_SCOPE"] = out_of_scope_pk
                    logger.info(f"📝 Got/created OUT_OF_SCOPE category (PK: {out_of_scope_pk}) for {aspect_code}")
                except Exception as exc:
                    logger.warning(f"⚠️ Failed to create OUT_OF_SCOPE category for {aspect_code}: {exc}")
                    out_of_scope_pk = None

                # Batch aspects
                batches = make_batches(normal_aspects, ra_cfg.ASPECTS_PER_REFINEMENT_PROMPT)

                for batch in batches:
                    aspects_desc = [r["detail_text"] for r in batch]
                    original_categories = [r["parent_group_name"] if r["parent_group_name"] else None for r in batch]
                    ctx = ReviewRefinementStageContext(
                        product_category="",
                        aspect_type=human_name,
                        aspect_context=aspect_context,
                        categories=cat_list,
                        aspects=aspects_desc,
                        original_categories=original_categories,
                    )
                    
                    try:
                        res = await self._refinement_stage.execute(ctx)

                        # Track which aspects were assigned by the LLM
                        assigned_indices = set()
                        
                        # Apply reassignments from LLM
                        for idx, cat_name in res.reassignments.items():
                            idx_int = int(idx)
                            assigned_indices.add(idx_int)
                            aspect_row = batch[idx_int]
                            aspect_pk = aspect_row["aspect_pk"]

                            if cat_name == "OUT_OF_SCOPE":
                                # Assign to OUT_OF_SCOPE category
                                out_of_scope_pk = name_to_pk.get("OUT_OF_SCOPE")
                                if out_of_scope_pk:
                                    success = await self._aspect_repo.update_category(aspect_pk, out_of_scope_pk)
                                    if not success:
                                        logger.warning(f"⚠️ Failed to assign aspect {aspect_pk} to OUT_OF_SCOPE category")
                                else:
                                    logger.warning(f"⚠️ OUT_OF_SCOPE category not available for aspect {aspect_pk}")
                                continue

                            cat_pk = name_to_pk.get(cat_name)
                            if cat_pk is None:
                                # Create new category using get_or_create to avoid duplicates
                                try:
                                    cat_pk = await self._cat_repo.get_or_create_category(
                                        project_id=project_id,
                                        aspect_type=aspect_code,
                                        name=cat_name,
                                        stage="refinement",
                                        definition=""  # undefined yet
                                    )
                                    name_to_pk[cat_name] = cat_pk
                                    logger.info(f"📝 Created new refinement category: {cat_name} (PK: {cat_pk})")
                                except Exception as create_exc:
                                    logger.warning(f"⚠️ Failed to create refinement category {cat_name}: {create_exc}")
                                    cat_pk = None
                            
                            if cat_pk:
                                success = await self._aspect_repo.update_category(aspect_pk, cat_pk)
                                if not success:
                                    logger.warning(f"⚠️ Failed to update aspect {aspect_pk} to category {cat_pk} ({cat_name})")
                            else:
                                logger.warning(f"⚠️ No category PK available for aspect {aspect_pk}, leaving unassigned")
                        
                        # Handle aspects that weren't assigned by the LLM
                        unassigned_count = len(batch) - len(assigned_indices)
                        if unassigned_count > 0:
                            logger.warning(f"🚨 LLM didn't assign {unassigned_count}/{len(batch)} aspects in batch - applying fallback assignments")
                            
                            # Use first available category as fallback
                            fallback_category = normal_categories[0] if normal_categories else None
                            if fallback_category:
                                fallback_pk = fallback_category["category_pk"]
                                fallback_name = fallback_category["name"]
                                successful_fallbacks = 0
                                
                                for idx in range(len(batch)):
                                    if idx not in assigned_indices:
                                        aspect_row = batch[idx]
                                        aspect_pk = aspect_row["aspect_pk"]
                                        success = await self._aspect_repo.update_category(aspect_pk, fallback_pk)
                                        if success:
                                            successful_fallbacks += 1
                                        else:
                                            logger.warning(f"⚠️ Failed to assign aspect {aspect_pk} to fallback category")
                                
                                logger.info(f"📝 Applied fallback assignment: {successful_fallbacks} aspects → '{fallback_name}' for {aspect_code}")
                            else:
                                logger.error(f"❌ No fallback category available - {unassigned_count} aspects remain unassigned")
                                
                    except (LLMCallError, StageProtocolError) as exc:
                        # Refinement LLM validation failed - assign to first available category or error category
                        logger.warning(f"🚨 Refinement LLM validation failed for {aspect_code}: {exc}")
                        
                        # Determine fallback category
                        fallback_category_pk = None
                        fallback_category_name = "UNKNOWN"
                        
                        if error_category_pk:
                            fallback_category_pk = error_category_pk
                            fallback_category_name = "EXTRACTION_ERRORS"
                        elif normal_categories:
                            fallback_category_pk = normal_categories[0]["category_pk"]
                            fallback_category_name = normal_categories[0]["name"]
                        else:
                            # No categories available - create a generic failure category
                            try:
                                fallback_category_pk = await self._cat_repo.get_or_create_category(
                                    project_id=project_id,
                                    aspect_type=aspect_code,
                                    name="REFINEMENT_FAILED",
                                    stage="final",
                                    definition=f"Aspects that failed refinement for {aspect_code} type due to LLM validation errors"
                                )
                                fallback_category_name = "REFINEMENT_FAILED"
                                logger.info(f"📝 Created fallback refinement category (PK: {fallback_category_pk}) for {aspect_code}")
                            except Exception as fallback_exc:
                                logger.exception(f"❌ Failed to create fallback category for {aspect_code}: {fallback_exc}")
                        
                        # Assign all batch aspects to fallback category
                        if fallback_category_pk:
                            successful_updates = 0
                            for aspect in batch:
                                success = await self._aspect_repo.update_category(aspect["aspect_pk"], fallback_category_pk)
                                if success:
                                    successful_updates += 1
                                else:
                                    logger.warning(f"⚠️ Failed to update aspect {aspect['aspect_pk']} to fallback category")
                            
                            logger.info(f"📝 Assigned {successful_updates}/{len(batch)} aspects to fallback category '{fallback_category_name}' for {aspect_code}")
                        else:
                            logger.error(f"❌ No fallback category available for {aspect_code} - {len(batch)} aspects remain unassigned") 