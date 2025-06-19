"""Unit-tests for the *Phase 3* segmentation service.

These tests purposefully avoid external I/O. Instead, they compose the service
with *in-memory* fakes for the repository layer, storage backend, and the LLM
client.

The goal is to validate that the orchestrator – ``DatabaseProductSegmentationService``
– performs the correct control-flow and state transitions:

1. A run is created and stored.
2. Products are attached to the run.
3. ``execute_run`` batches the items, calls the LLM stub, stores the raw
   interaction, writes the derived ``product_segments``, updates progress, and
   finally marks the run *completed*.
"""

import sys
import asyncio
import tempfile
import shutil
from typing import Any, Dict, List, Optional
import pytest

# ---------------------------------------------------------------------------
# Provide a tiny stub for the `supabase` package so that importing the real
# repository modules (which type-hint the `Client`) does not fail on machines
# where the SDK is not installed.
# ---------------------------------------------------------------------------

if "supabase" not in sys.modules:  # pragma: no cover – test helper
    import types

    supabase_stub = types.ModuleType("supabase")

    class _DummyClient:  # pylint: disable=too-few-public-methods
        """Placeholder supabase client used only for type annotations."""

    supabase_stub.Client = _DummyClient  # type: ignore[attr-defined]
    sys.modules["supabase"] = supabase_stub

# After stubbing, *now* import the real application modules -----------------------------------

from backend.product_segmentation.models import (
    SegmentationStatus,
    StartSegmentationRequest,
    ProductSegment,
)
from backend.product_segmentation.services.db_product_segmentation import (
    DatabaseProductSegmentationService,
)
from backend.product_segmentation.storage.llm_storage import LLMStorageService
from backend.product_segmentation.repositories.segmentation_run_repository import (
    SegmentationRunRepository,
)
from backend.product_segmentation.repositories.product_segment_repository import (
    ProductSegmentRepository,
)
from backend.product_segmentation.repositories.product_taxonomy_repository import (
    ProductTaxonomyRepository,
)
from backend.product_segmentation.repositories.llm_interaction_repository import (
    LLMInteractionRepository,
)

# ---------------------------------------------------------------------------
# In-memory fakes (keep them minimal – only what tests require)
# ---------------------------------------------------------------------------


class _InMemRunRepo(SegmentationRunRepository):
    def __init__(self) -> None:  # type: ignore[no-super-call]
        self._data: Dict[str, Any] = {}

    async def create(self, run_data):  # type: ignore[override]
        self._data[run_data.id] = run_data
        return run_data

    async def get_by_id(self, run_id):  # type: ignore[override]
        return self._data.get(run_id)

    async def update_progress(self, run_id: str, processed_products: int, total_products: int = None) -> bool:  # type: ignore[override]
        run = self._data[run_id]
        run.processed_products = processed_products
        if total_products is not None:
            run.total_products = total_products
        return True

    async def update_status(self, run_id, status):  # type: ignore[override]
        run = self._data[run_id]
        run.status = status
        return True

    async def complete_run(self, run_id, result_summary):  # type: ignore[override]
        run = self._data[run_id]
        run.status = SegmentationStatus.COMPLETED
        run.result_summary = result_summary
        return True


class _InMemSegmentRepo(ProductSegmentRepository):
    """In-memory fake of ProductSegmentRepository."""

    def __init__(self) -> None:  # type: ignore[no-super-call]
        # Bypass parent __init__ (needs Supabase client)
        self._segments: List[Dict[str, Any]] = []

    async def create_run_products(self, run_id: str, product_ids: List[int]) -> bool:
        """Create product list for a run."""
        self._segments.extend([{"run_id": run_id, "product_id": pid} for pid in product_ids])
        return True

    async def get_run_products(self, run_id: str) -> List[int]:  # type: ignore[override]
        return [s["product_id"] for s in self._segments if s["run_id"] == run_id]

    async def batch_create_segments(self, segments):  # type: ignore[override]
        """Store segments in memory."""
        for segment in segments:
            if isinstance(segment, dict):
                self._segments.append(segment)
            else:
                self._segments.append(segment.model_dump())
        return True

    async def get_segments_by_run(self, run_id: str) -> List[Dict[str, Any]]:  # type: ignore[override]
        """Get segments for a run."""
        return [s for s in self._segments if s["run_id"] == run_id]

    async def batch_create_refined_segments(self, segments):  # type: ignore[override]
        """Store refined segments in memory."""
        return await self.batch_create_segments(segments)


class _StubLLM:
    """Stub LLM client that returns deterministic responses."""

    def __init__(self, fail_consolidation: bool = False, fail_refinement: bool = False):
        self.fail_consolidation = fail_consolidation
        self.fail_refinement = fail_refinement

    async def segment_products(self, products, *, category: Optional[str] = None, **kwargs):  # type: ignore[override]
        """Return deterministic segmentation."""
        return {
            "segments": [
                {"product_id": pid, "taxonomy_id": 1, "category_name": "Category A"}
                for pid in products
            ],
            "taxonomies": [
                {
                    "category_name": "Category A",
                    "definition": "First category",
                    "product_count": len(products)
                }
            ],
            "cache_key": "stub_segment_1"
        }

    async def consolidate_taxonomy(self, taxonomies, **kwargs):  # type: ignore[override]
        """Return deterministic consolidation."""
        if self.fail_consolidation:
            raise RuntimeError("Simulated consolidation failure")
        return {
            "consolidated": taxonomies[0] if taxonomies else {},
            "cache_key": "stub_consolidate_1"
        }

    async def refine_assignments(self, segments, taxonomies=None, **kwargs):  # type: ignore[override]
        """Return deterministic refinement."""
        if self.fail_refinement:
            raise RuntimeError("Simulated refinement failure")
        return {
            "segments": segments,
            "cache_key": "stub_refine_1"
        }


class _InMemTaxonomyRepo(ProductTaxonomyRepository):
    """In-memory fake of ProductTaxonomyRepository."""

    def __init__(self) -> None:  # type: ignore[no-super-call]
        # Bypass parent __init__ (needs Supabase client)
        self._taxonomies: List[Dict[str, Any]] = []

    async def batch_create(self, run_id: str, taxonomies: List[Dict[str, Any]]) -> bool:  # type: ignore[override]
        """Store taxonomies in memory."""
        self._taxonomies.extend(taxonomies)
        return True

    async def get_taxonomies_by_run(self, run_id):  # type: ignore[override]
        # Return everything for simplicity; real impl would filter
        return self._taxonomies


class _InMemInteractionRepo(LLMInteractionRepository):
    def __init__(self) -> None:  # type: ignore[no-super-call]
        self._data: list[Any] = []

    async def batch_create_interactions(self, interactions):  # type: ignore[override]
        self._data.extend(interactions)
        return True

    async def get_by_run(self, run_id):  # type: ignore[override]
        return self._data


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------


def _setup_service(
    temp_dir: str,
    fail_consolidation: bool = False,
    fail_refinement: bool = False
) -> DatabaseProductSegmentationService:
    storage = LLMStorageService.create_local(temp_dir)
    return DatabaseProductSegmentationService(
        _InMemRunRepo(),
        _InMemSegmentRepo(),
        storage,
        _StubLLM(fail_consolidation, fail_refinement),
        _InMemTaxonomyRepo(),
        _InMemInteractionRepo(),
    )


# ---------------------------------------------------------------------------
# Actual test cases
# ---------------------------------------------------------------------------


def test_create_and_execute_run():
    temp_dir = tempfile.mkdtemp(prefix="ps_service_tests_")

    async def _run() -> None:
        service = _setup_service(temp_dir)

        # 1️⃣ Create run
        request = StartSegmentationRequest(
            product_ids=[10, 20, 30, 40],
            category="Lighting",
            batch_size=20  # Optional but we provide it for testing
        )
        run_id = await service.create_run(request)
        assert run_id.startswith("RUN_")

        # 2️⃣ Execute run – should complete without error
        await service.execute_run(run_id)

        # Validate internal state of fake repos
        run_repo: _InMemRunRepo = service._run_repo  # type: ignore[attr-defined]
        run = await run_repo.get_by_id(run_id)
        assert run.status == SegmentationStatus.COMPLETED
        assert run.processed_products == len(request.product_ids)

        seg_repo: _InMemSegmentRepo = service._segment_repo  # type: ignore[attr-defined]
        assert len(seg_repo._segments) == len(request.product_ids)

        interaction_repo: _InMemInteractionRepo = service._interaction_repo  # type: ignore[attr-defined]
        # For 4 products with batch_size=20 we expect 1 interaction record
        assert len(interaction_repo._data) == 1
        assert interaction_repo._data[0].cache_key is None or isinstance(interaction_repo._data[0].cache_key, str)

    try:
        asyncio.run(_run())
    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_execute_run_consolidation_failure():
    """Test that consolidation failure fails the entire run."""
    temp_dir = tempfile.mkdtemp(prefix="ps_service_tests_")
    try:
        service = _setup_service(temp_dir, fail_consolidation=True)

        request = StartSegmentationRequest(
            product_ids=[1, 2, 3],
            batch_size=2  # Small batch size to force multiple batches
        )
        run_id = await service.create_run(request)
        await service.execute_run(run_id)

        run = await service._run_repo.get_by_id(run_id)
        assert run.status == SegmentationStatus.FAILED

    finally:
        shutil.rmtree(temp_dir)


@pytest.mark.asyncio
async def test_execute_run_refinement_failure():
    """Test that refinement failure fails the entire run."""
    temp_dir = tempfile.mkdtemp(prefix="ps_service_tests_")
    try:
        service = _setup_service(temp_dir, fail_refinement=True)

        request = StartSegmentationRequest(
            product_ids=[1, 2, 3],
            batch_size=2  # Small batch size to force multiple batches
        )
        run_id = await service.create_run(request)
        await service.execute_run(run_id)

        run = await service._run_repo.get_by_id(run_id)
        assert run.status == SegmentationStatus.FAILED

    finally:
        shutil.rmtree(temp_dir)


def run_service_tests() -> bool:  # pragma: no cover – called from test_runner
    """Run all service tests in sequence.

    This function is called by the stand-alone test runner script to execute
    the service test suite in isolation.  The runner uses this boolean return
    value to set its exit code.

    Returns
    -------
    bool
        True if all tests pass, False if any test fails.
    """
    try:
        test_create_and_execute_run()
        asyncio.run(test_execute_run_consolidation_failure())
        asyncio.run(test_execute_run_refinement_failure())
        return True
    except Exception as exc:
        print(f"Service tests failed: {exc}", file=sys.stderr)
        return False 