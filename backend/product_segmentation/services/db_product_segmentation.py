"""Database-integrated Product Segmentation service (Phase 3).

This module provides the first working implementation of the end-to-end
segmentation flow **without** any external I/O so that it can be unit-tested
locally. The design purposely avoids calls to the real Supabase client or the
OpenAI SDK – those collaborators are injected and can be substituted with
in-memory fakes during testing.

The service currently supports three operations:

1. ``create_run`` – Creates a new ``segmentation_runs`` record and associates
   the explicit list of product IDs with the run.
2. ``execute_run`` – Batches the previously provided products, calls the
   injected ``segment_llm_client`` for each batch, persists the resulting segments and
   interaction logs, and finally marks the run as *completed*.
3. ``main()`` – A tiny CLI shim so the module can be executed in isolation
   using ``python -m backend.product_segmentation.services.db_product_segmentation``.

The public API is intentionally *async* so that the real implementation can run
LLM calls concurrently, but the current logic runs sequentially for
simplicity.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol, Sequence
import secrets

import pandas as pd

from product_segmentation.models import (
    InteractionType,
    ProductSegmentCreate,
    SegmentationRunCreate,
    SegmentationStatus,
    StartSegmentationRequest,
    ProductTaxonomyCreate,
    LLMInteractionIndexCreate,
    RefinedProductSegmentCreate,
)
from product_segmentation.repositories.product_segment_repository import (
    ProductSegmentRepository,
)
from product_segmentation.repositories.segmentation_run_repository import (
    SegmentationRunRepository,
)
from product_segmentation.repositories.product_taxonomy_repository import (
    ProductTaxonomyRepository,
)
from product_segmentation.repositories.llm_interaction_repository import (
    LLMInteractionRepository,
)
from product_segmentation.storage.llm_storage import LLMStorageService
from product_segmentation.utils.taxonomy import merge_batch_taxonomies
from product_segmentation.utils.batching import make_batches
from utils import config as llm_cfg
from product_segmentation import config as seg_cfg

try:
    from backend.config import settings  # type: ignore
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
        model: str,
        temperature: float,
    ) -> Dict[str, Any]:
        """Perform segmentation on the supplied ``products``.

        The concrete implementation decides the exact response schema, but it
        MUST return a mapping that contains at least a ``segments`` list where
        every element is a mapping with **product_id**, **taxonomy_id**
        """

    async def consolidate_taxonomy(
        self,
        taxonomies: List[Dict[str, Any]],
        *,
        model: str,
        temperature: float,
    ) -> Dict[str, Any]:
        """Consolidate multiple batch-level taxonomies into one unified set."""

    async def refine_assignments(
        self,
        segments: List[Dict[str, Any]],
        taxonomies: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Refine product-to-taxonomy assignments."""


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------


def _generate_run_id() -> str:
    """Generate a unique run ID matching the README convention."""
    ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    short = uuid.uuid4().hex[:4]
    return f"RUN_{ts}_{short}"


# ---------------------------------------------------------------------------
# Service implementation
# ---------------------------------------------------------------------------


class DatabaseProductSegmentationService:
    """Core orchestration logic for Phase 3.*"""

    def __init__(
        self,
        run_repo: SegmentationRunRepository,
        segment_repo: ProductSegmentRepository,
        storage: LLMStorageService,
        segment_llm_client: SegmentationLLMClient,
        taxonomy_repo: Optional[ProductTaxonomyRepository] = None,
        interaction_repo: Optional[LLMInteractionRepository] = None,
    ) -> None:
        self._run_repo = run_repo
        self._segment_repo = segment_repo
        self._taxonomy_repo = taxonomy_repo  # may be ``None`` in unit tests
        self._storage = storage
        self._segment_llm_client = segment_llm_client
        self._interaction_repo = interaction_repo

    # ---------------------------------------------------------------------
    # Public high-level API
    # ---------------------------------------------------------------------

    async def create_run(self, request: StartSegmentationRequest) -> str:
        """Create a new segmentation run."""
        run_id = f"RUN_{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}_{secrets.token_hex(2)}"

        # Create run record
        run = SegmentationRunCreate(
            id=run_id,
            total_products=len(request.product_ids),
            category=request.category,
            llm_config={},  # Use default config from environment
            processing_params={
                "batch_size": request.batch_size or seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT
            }
        )
        await self._run_repo.create(run)

        # Create product list
        await self._segment_repo.create_run_products(run_id, request.product_ids)

        return run_id

    async def execute_run(self, run_id: str) -> None:
        """Execute a segmentation run to completion."""
        try:
            run = await self._run_repo.get_by_id(run_id)
            if run is None:
                raise ValueError(f"Run {run_id} not found")

            products = await self._segment_repo.get_run_products(run_id)
            if not products:
                raise ValueError(f"No products found for run {run_id}")

            # Split products into batches for initial segmentation
            batches = make_batches(products, seg_cfg.PRODUCTS_PER_TAXONOMY_PROMPT)
            logger.info("Split %d products into %d batches", len(products), len(batches))

            # Process each batch
            batch_taxonomies = []
            all_segments = []
            for batch_idx, batch in enumerate(batches):
                logger.info("Processing batch %d/%d (%d products)", batch_idx + 1, len(batches), len(batch))
                
                result = await self._segment_llm_client.segment_products(
                    batch,
                    category=run.category,
                )
                
                logger.debug("Batch %d raw LLM result: %s", batch_idx + 1, str(result)[:300].replace("\n", " "))
                
                # Store interaction log
                await self._storage.store_interaction(
                    run_id,
                    InteractionType.SEGMENTATION.value,
                    request_data={"products": batch},
                    response_data=result,
                    batch_id=batch_idx + 1,
                    metadata={"cache_key": result.get("cache_key")},
                )

                # Store interaction index
                if self._interaction_repo is not None:
                    idx = LLMInteractionIndexCreate(
                        run_id=run_id,
                        interaction_type=InteractionType.SEGMENTATION,
                        batch_id=batch_idx + 1,
                        attempt=1,
                        file_path=f"{run_id}/interactions/{InteractionType.SEGMENTATION.value}_batch_{batch_idx + 1}_attempt_1.json",
                        cache_key=result.get("cache_key"),
                    )
                    await self._interaction_repo.batch_create_interactions([idx])
                
                # ------------------------------------------------------------------
                # ❶ Persist batch-level taxonomies first so we get **real** IDs.
                # ------------------------------------------------------------------
                taxonomy_name_to_id: Dict[str, int] = {}
                batch_tax_list = result.get("taxonomies", [])
                if batch_tax_list and self._taxonomy_repo is not None:
                    tax_creates = [
                        ProductTaxonomyCreate(
                            run_id=run_id,
                            category_name=t["category_name"],
                            definition=t.get("definition", ""),
                            product_count=t.get("product_count", 0),
                        )
                        for t in batch_tax_list
                    ]
                    inserted = await self._taxonomy_repo.batch_create_taxonomies(tax_creates)
                    # Build mapping from name → actual PK id (fallback to 1-based order).
                    if inserted:
                        for row in inserted:
                            name = row.category_name if hasattr(row, "category_name") else row.get("category_name")
                            taxonomy_name_to_id[name] = row.id if hasattr(row, "id") else row.get("id")
                else:
                    # In-memory mode → derive IDs deterministically (1-based order)
                    for idx, t in enumerate(batch_tax_list, 1):
                        taxonomy_name_to_id[t["category_name"]] = idx

                # Keep taxonomies for later consolidation
                batch_taxonomies.extend(batch_tax_list)

                # ------------------------------------------------------------------
                # ❷ Persist *segments* referencing the freshly inserted taxonomy IDs.
                # ------------------------------------------------------------------
                for seg in result.get("segments", []):
                    # Prefer the explicit category_name in segment if present.
                    cat_name = seg.get("category_name")
                    if not cat_name:
                        idx = seg["taxonomy_id"] - 1
                        if 0 <= idx < len(batch_tax_list):
                            cat_name = batch_tax_list[idx]["category_name"]
                    if cat_name:
                        seg["category_name"] = cat_name
                        # Replace taxonomy_id with actual DB id when available.
                        seg["taxonomy_id"] = taxonomy_name_to_id.get(cat_name, seg["taxonomy_id"])
                if result.get("segments"):
                    segments = [
                        ProductSegmentCreate(
                            run_id=run_id,
                            product_id=s["product_id"],
                            taxonomy_id=s["taxonomy_id"],
                        )
                        for s in result["segments"]
                    ]
                    await self._segment_repo.batch_create_segments(segments)
                    all_segments.extend(result["segments"])

                    logger.debug("Batch %d: inserted %d segments", batch_idx + 1, len(segments))

                # Update progress - use actual number of processed products
                processed = sum(len(b) for b in batches[:batch_idx + 1])
                await self._run_repo.update_progress(run_id, processed, len(products))

                logger.debug("Batch %d: inserted %d tax rows, mapping=%s", batch_idx + 1, len(taxonomy_name_to_id), taxonomy_name_to_id)

            # Consolidate taxonomies
            consolidated_taxonomies = await self._consolidate_taxonomies(
                batch_taxonomies,
                run_id
            )
            
            # Store final taxonomies
            if self._taxonomy_repo:
                taxonomies = [
                    ProductTaxonomyCreate(
                        run_id=run_id,
                        category_name=t["category_name"],
                        definition=t.get("definition", ""),
                        product_count=t.get("product_count", 0)
                    )
                    for t in consolidated_taxonomies
                ]
                await self._taxonomy_repo.batch_create_taxonomies(taxonomies)

            # Refine assignments
            refined_segments = await self._refine_assignments(
                run_id,
                all_segments,
                consolidated_taxonomies,
                run.llm_config
            )

            # Store refined segments
            if refined_segments:
                refined_creates = [
                    RefinedProductSegmentCreate(
                        run_id=run_id,
                        product_id=s["product_id"],
                        taxonomy_id=s["taxonomy_id"],
                    )
                    for s in refined_segments
                ]
                await self._segment_repo.batch_create_refined_segments(refined_creates)

            # Mark run as completed
            await self._run_repo.update_status(run_id, SegmentationStatus.COMPLETED)

        except Exception as exc:
            logger.exception("Run %s failed: %s", run_id, exc)
            await self._run_repo.update_status(run_id, SegmentationStatus.FAILED)
            raise

    async def _consolidate_taxonomies(
        self,
        batch_taxonomies: List[Dict[str, Any]],
        run_id: str,
    ) -> List[Dict[str, Any]]:
        """Consolidate taxonomies from multiple batches.

        Parameters
        ----------
        batch_taxonomies
            List of taxonomies to consolidate.
        run_id
            Run ID for logging.

        Returns
        -------
        List[Dict[str, Any]]
            Consolidated taxonomies.
        """
        if not batch_taxonomies:
            return []

        if len(batch_taxonomies) == 1:
            return batch_taxonomies

        # Process batches in pairs
        result = await self._segment_llm_client.consolidate_taxonomy(batch_taxonomies)

        # Store interaction
        await self._storage.store_interaction(
            run_id,
            InteractionType.CONSOLIDATE_TAXONOMY.value,
            {"taxonomies": batch_taxonomies},
            result,
        )

        return result["taxonomies"]

    async def _refine_assignments(
        self,
        run_id: str,
        segments: List[Dict[str, Any]],
        taxonomies: List[Dict[str, Any]],
        llm_config: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Refine segment assignments using consolidated taxonomy."""
        if not segments or not taxonomies:
            return []

        # Split segments into refinement batches
        segment_batches = make_batches(segments, seg_cfg.PRODUCTS_PER_REFINEMENT)
        
        # Process each refinement batch
        refined = []
        for batch_idx, batch in enumerate(segment_batches):
            result = await self._segment_llm_client.refine_assignments(
                batch,
                taxonomies=taxonomies,
            )

            # Store interaction log
            await self._storage.store_interaction(
                run_id,
                InteractionType.REFINE_ASSIGNMENTS.value,
                request_data={"segments": batch, "taxonomies": taxonomies},
                response_data=result,
                batch_id=batch_idx + 1,
                metadata={"cache_key": result.get("cache_key")},
            )

            # Store interaction index
            if self._interaction_repo is not None:
                idx = LLMInteractionIndexCreate(
                    run_id=run_id,
                    interaction_type=InteractionType.REFINE_ASSIGNMENTS,
                    batch_id=batch_idx + 1,
                    attempt=1,
                    file_path=f"{run_id}/interactions/{InteractionType.REFINE_ASSIGNMENTS.value}_batch_{batch_idx + 1}_attempt_1.json",
                    cache_key=result.get("cache_key"),
                )
                await self._interaction_repo.batch_create_interactions([idx])

            if "segments" in result:
                refined.extend(result["segments"])

        return refined


# ---------------------------------------------------------------------------
# CLI helper – *demo purposes only*
# ---------------------------------------------------------------------------


async def _demo() -> None:  # pragma: no cover – manual invocation helper
    """Run the service in demo mode with in-memory dependencies."""

    from types import SimpleNamespace
    import tempfile
    import shutil
    from product_segmentation.tests.stubs import StubLLM

    # ---------------------------------------------------------------------
    # In-memory repo implementations
    # ---------------------------------------------------------------------

    class _InMemRunRepo(SegmentationRunRepository):
        def __init__(self) -> None:  # type: ignore[no-super-call]
            # Bypass parent __init__ (needs Supabase client)
            self._data: Dict[str, Any] = {}

        async def create(self, run_data):  # type: ignore[override]
            self._data[run_data.id] = run_data
            return run_data

        async def get_by_id(self, run_id):  # type: ignore[override]
            return self._data.get(run_id)

        async def update_progress(self, run_id: str, processed_products: int, total_products: Optional[int] = None) -> bool:  # type: ignore[override]
            run = self._data[run_id]
            run.processed_products = processed_products
            if total_products is not None:
                run.total_products = total_products
            return True

        async def update_status(self, run_id, status):  # type: ignore[override]
            run = self._data[run_id]
            run.status = status
            return True

    class _InMemSegmentRepo(ProductSegmentRepository):
        def __init__(self) -> None:  # type: ignore[no-super-call]
            self._run_products: Dict[str, List[int]] = {}
            self._segments: List[Any] = []
            self._refined_segments: List[Any] = []

        # ------------------------------------------------------------------
        # Run-product helpers
        # ------------------------------------------------------------------
        async def create_run_products(self, run_id: str, product_ids: List[int]) -> bool:  # type: ignore[override]
            """Mimic persistent repo by storing the product list in-memory."""
            self._run_products[run_id] = list(product_ids)
            return True

        # Backwards-compat helper (legacy name used elsewhere)
        async def add_products_to_run(self, run_id: str, product_ids: List[int]) -> bool:  # type: ignore[override]
            return await self.create_run_products(run_id, product_ids)

        async def get_run_products(self, run_id):  # type: ignore[override]
            return self._run_products.get(run_id, [])

        # ------------------------------------------------------------------
        # Segment helpers
        # ------------------------------------------------------------------
        async def batch_create_segments(self, segments):  # type: ignore[override]
            self._segments.extend(segments)
            return True

        async def batch_create_refined_segments(self, segments):  # type: ignore[override]
            self._refined_segments.extend(segments)
            return True

    class _InMemTaxonomyRepo(ProductTaxonomyRepository):
        def __init__(self) -> None:  # type: ignore[no-super-call]
            self._taxonomies: List[Any] = []

        async def batch_create_taxonomies(self, taxonomies: List[ProductTaxonomyCreate]):  # type: ignore[override]
            self._taxonomies.extend(taxonomies)
            # Assign incremental IDs for each new taxonomy
            created: List[Any] = []
            start_id = len(self._taxonomies) - len(taxonomies) + 1
            for idx, t in enumerate(taxonomies):
                rec = t.model_dump()
                rec["id"] = start_id + idx
                created.append(rec)
            return created

    class _InMemInteractionRepo(LLMInteractionRepository):
        def __init__(self) -> None:  # type: ignore[no-super-call]
            self._interactions: List[Any] = []

        async def batch_create_interactions(self, interactions: List[LLMInteractionIndexCreate]) -> bool:  # type: ignore[override]
            self._interactions.extend(interactions)
            return True

        async def get_by_cache_key(self, cache_key: str) -> Optional[Any]:  # type: ignore[override]
            for interaction in self._interactions:
                if interaction.cache_key == cache_key:
                    return interaction
            return None

    # ---------------------------------------------------------------------
    # Wire dependencies
    # ---------------------------------------------------------------------

    storage_root = settings.STORAGE_ROOT
    storage_root.mkdir(parents=True, exist_ok=True)
    storage = LLMStorageService.create_local(str(storage_root))

    service = DatabaseProductSegmentationService(
        _InMemRunRepo(),
        _InMemSegmentRepo(),
        storage,
        StubLLM(),
        taxonomy_repo=_InMemTaxonomyRepo(),
        interaction_repo=_InMemInteractionRepo(),
    )

    request = StartSegmentationRequest(product_ids=[1, 2, 3], category="Demo")
    run_id = await service.create_run(request)
    await service.execute_run(run_id)
    print("Demo run", run_id, "completed – logs in", storage_root)


def main() -> None:  # pragma: no cover
    """Entry-point for manual smoke-testing."""
    asyncio.run(_demo())


if __name__ == "__main__":
    main() 