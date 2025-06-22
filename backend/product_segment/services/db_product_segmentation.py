"""Database-integrated Product Segmentation service (v6.0).

This module provides the implementation of the end-to-end segmentation flow
with database integration. The service orchestrates three LLM phases:
1. Extraction - extract per-batch taxonomies
2. Consolidation - merge batch taxonomies into a global set
3. Refinement - re-assign products with full taxonomy context

The service currently supports two main operations:
1. create_run - Creates a new segmentation run and associates products
2. execute_run - Processes the run through all stages, tracking progress
"""

import asyncio
import logging
import math
from datetime import datetime
from typing import Any, Dict, List, Optional, Protocol, Sequence
import secrets

from product_segment.models import (
    InteractionType,
    SegmentationStage,
    StartSegmentationRequest,
    ProductSegmentRun,
    ProductSegmentTaxonomy,
    ProductSegmentAssignment,
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
from core.utils.batching import make_batches
from product_segment import config as seg_cfg

try:
    from backend.config import settings
except ModuleNotFoundError:  # pragma: no cover – fallback for direct module execution
    import sys as _sys
    from importlib import import_module as _import_module
    from pathlib import Path as _Path

    _project_root = _Path(__file__).resolve().parents[2]
    _sys.path.append(str(_project_root))
    settings = _import_module("config").settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Typed protocol for the (pluggable) LLM client
# ---------------------------------------------------------------------------

class SegmentationLLMClient(Protocol):
    """Subset of the LLM client interface that the service relies on."""

    async def segment_products(
        self,
        products: Sequence[int],
        *,
        category: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Perform segmentation on the supplied products."""

    async def consolidate_taxonomy(
        self,
        taxonomies: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Consolidate multiple batch-level taxonomies into one unified set."""

    async def refine_assignments(
        self,
        segments: List[Dict[str, Any]],
        taxonomies: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Refine product-to-taxonomy assignments."""

class DatabaseProductSegmentationService:
    """Core orchestration logic for Product Segmentation v6.0."""

    def __init__(
        self,
        run_repo: SegmentationRunRepository,
        segment_repo: ProductSegmentRepository,
        segment_llm_client: SegmentationLLMClient,
        taxonomy_repo: ProductTaxonomyRepository
    ) -> None:
        self._run_repo = run_repo
        self._segment_repo = segment_repo
        self._taxonomy_repo = taxonomy_repo
        self._segment_llm_client = segment_llm_client

    async def create_run(self, request: StartSegmentationRequest) -> str:
        """Create a new segmentation run."""
        run_id = f"RUN_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(2)}"

        # Create run record
        run = ProductSegmentRun(
            id=run_id,
            stage=SegmentationStage.INIT,
            llm_config={},  # Use default config from environment
            processing_params={
                "batch_size": seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT
            }
        )
        await self._run_repo.create(run)

        # Create initial unassigned taxonomy
        unassigned_tax = ProductSegmentTaxonomy(
            run_id=run_id,
            segment_name="__UNASSIGNED__",
            definition="Auto-generated placeholder",
            stage="init"
        )
        unassigned_id = await self._taxonomy_repo.create_taxonomy(unassigned_tax)

        # Create out-of-scope taxonomy
        out_of_scope_tax = ProductSegmentTaxonomy(
            run_id=run_id,
            segment_name="__OUT_OF_SCOPE__",
            definition="Products totally irrelevant to the current category",
            stage="system"
        )
        await self._taxonomy_repo.create_taxonomy(out_of_scope_tax)

        # Create initial assignments
        assignments = [
            ProductSegmentAssignment(
                run_id=run_id,
                product_id=pid,
                taxonomy_id_initial=unassigned_id,
                taxonomy_id_refined=None
            )
            for pid in request.product_ids
        ]
        await self._segment_repo.batch_create_assignments(assignments)

        return run_id

    async def execute_run(self, run_id: str) -> None:
        """Execute a segmentation run to completion."""
        try:
            run = await self._run_repo.get_by_id(run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")

            # Get products for this run
            products = await self._segment_repo.get_run_products(run_id)
            if not products:
                raise ValueError(f"No products found for run {run_id}")

            # Calculate expected LLM calls for progress tracking
            seg_batches = math.ceil(len(products) / seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT)
            consolidation_levels = math.ceil(math.log2(seg_batches))
            consolidation_calls = 2 ** consolidation_levels - 1
            ref_batches = math.ceil(len(products) / seg_cfg.PRODUCTS_PER_REFINEMENT)
            total_calls = seg_batches + consolidation_calls + ref_batches
            calls_done = 0

            # Update run with total calls
            await self._run_repo.update_total_calls(run_id, total_calls)

            # 1. Extraction Stage
            await self._run_repo.update_stage(run_id, SegmentationStage.EXTRACTION)
            batch_taxonomies = []
            all_segments = []
            
            batches = make_batches(products, seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT)
            for batch_idx, batch in enumerate(batches):
                result = await self._segment_llm_client.segment_products(
                    batch,
                    category=run.product_category,
                )

                # Store taxonomies and segments
                taxonomies = [
                    ProductSegmentTaxonomy(
                        run_id=run_id,
                        segment_name=t["category_name"],
                        definition=t.get("definition", ""),
                        stage="extraction"
                    )
                    for t in result.get("taxonomies", [])
                ]
                tax_ids = await self._taxonomy_repo.batch_create_taxonomies(taxonomies)
                
                # Update assignments with initial taxonomy IDs
                for segment in result.get("segments", []):
                    tax_idx = segment["taxonomy_id"] - 1
                    if 0 <= tax_idx < len(tax_ids):
                        await self._segment_repo.update_initial_taxonomy(
                            run_id,
                            segment["product_id"],
                            tax_ids[tax_idx]
                        )

                batch_taxonomies.extend(result.get("taxonomies", []))
                all_segments.extend(result.get("segments", []))
                
                # Update progress
                calls_done += 1
                await self._run_repo.update_calls_done(run_id, calls_done)

            # 2. Consolidation Stage
            await self._run_repo.update_stage(run_id, SegmentationStage.CONSOLIDATION)
            
            current_level = 0
            current_taxonomies = batch_taxonomies

            while len(current_taxonomies) > 1:
                next_level = []
                pairs = [(current_taxonomies[i], current_taxonomies[i + 1]) 
                        for i in range(0, len(current_taxonomies) - 1, 2)]
                
                if len(current_taxonomies) % 2:
                    pairs.append((current_taxonomies[-1], []))

                for pair_idx, (left, right) in enumerate(pairs):
                    result = await self._segment_llm_client.consolidate_taxonomy(
                        [left, right] if right else [left]
                    )

                    next_level.extend(result.get("taxonomies", []))
                    
                    # Update progress
                    calls_done += 1
                    await self._run_repo.update_calls_done(run_id, calls_done)

                current_taxonomies = next_level
                current_level += 1

            consolidated = current_taxonomies[0] if len(current_taxonomies) == 1 else current_taxonomies

            # Store final taxonomies
            final_taxonomies = [
                ProductSegmentTaxonomy(
                    run_id=run_id,
                    segment_name=t["category_name"],
                    definition=t.get("definition", ""),
                    stage="final"
                )
                for t in consolidated
            ]
            await self._taxonomy_repo.batch_create_taxonomies(final_taxonomies)

            # 3. Refinement Stage
            await self._run_repo.update_stage(run_id, SegmentationStage.REFINEMENT)
            
            segment_batches = make_batches(all_segments, seg_cfg.PRODUCTS_PER_REFINEMENT)
            for batch_idx, batch in enumerate(segment_batches):
                result = await self._segment_llm_client.refine_assignments(
                    batch,
                    taxonomies=consolidated
                )

                # Update assignments with refined taxonomy IDs
                for segment in result.get("segments", []):
                    await self._segment_repo.update_refined_taxonomy(
                        run_id,
                        segment["product_id"],
                        segment["taxonomy_id"]
                    )

                # Update progress
                calls_done += 1
                await self._run_repo.update_calls_done(run_id, calls_done)

            # Mark run as completed
            await self._run_repo.update_stage(run_id, SegmentationStage.COMPLETED)

        except Exception as exc:
            logger.exception("Run %s failed: %s", run_id, exc)
            await self._run_repo.update_stage(run_id, SegmentationStage.FAILED)
            raise 