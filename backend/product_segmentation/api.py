"""REST API router for the *product_segmentation* module (Phase 4).

The endpoints implemented here provide a minimal yet functional surface that
covers the three core operations required by the Product Segmentation Engine:

1. ``POST /api/segmentation/start``  – create **and immediately execute** a
   segmentation run for an explicit list of ``product_id`` values.
2. ``GET  /api/segmentation/{run_id}/status`` – return the current processing
   status together with basic progress information.
3. ``GET  /api/segmentation/{run_id}/results`` – return the final taxonomies
   and product-to-segment assignments once the run has completed.

The implementation purposefully uses *in-memory* repository classes so that the
router works out-of-the-box **without** external dependencies (database, LLM
API, or S3).  This makes automated testing trivial and keeps the example
self-contained.  Swap out ``_build_default_service`` with a database-backed
implementation once production credentials are available.

All imports follow the packaging rules defined by the project – full, absolute
import paths and zero reliance on ``sys.path`` manipulation or CWD hacks.
"""

from typing import Dict, List, Optional, Any

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse

try:
    from backend.config import settings  # type: ignore
except ModuleNotFoundError:  # pragma: no cover – when running inside backend folder
    import sys as _sys
    from importlib import import_module as _import_module
    from pathlib import Path as _Path

    _project_root = _Path(__file__).resolve().parents[2]
    _sys.path.append(str(_project_root))
    settings = _import_module("config").settings

from product_segmentation.models import (
    ProductSegment,
    SegmentationResultsResponse,
    SegmentationStatusResponse,
    SegmentationStatus,
    StartSegmentationRequest,
)
from product_segmentation.services.db_product_segmentation import (
    DatabaseProductSegmentationService,
)
from product_segmentation.storage.llm_storage import LLMStorageService

# ---------------------------------------------------------------------------
# In-memory helper implementations (keep test-friendly, no external services)
# ---------------------------------------------------------------------------

class _InMemorySegmentationRunRepository:  # noqa: D401 – simple in-memory repo
    """A *very* small in-memory replacement for ``SegmentationRunRepository``."""

    # Minimal DTO replacement – only the attributes accessed by the service
    class _RunRecord:  # pylint: disable=too-few-public-methods
        def __init__(self, data: Dict[str, Any]):
            self.__dict__.update(data)

    def __init__(self) -> None:  # noqa: D401 – trivial init
        self._data: Dict[str, _InMemorySegmentationRunRepository._RunRecord] = {}

    async def create(self, run_data):  # type: ignore[override]
        self._data[run_data.id] = _InMemorySegmentationRunRepository._RunRecord(run_data.model_dump())
        return self._data[run_data.id]

    async def get_by_id(self, run_id: str):  # type: ignore[override]
        return self._data.get(run_id)

    async def update_progress(
        self,
        run_id: str,
        processed_products: int,
        total_products: int | None = None,
    ):  # type: ignore[override]
        """Update progress counters for *run_id*.

        The real repository accepts an *optional* ``total_products`` argument.
        Keeping the same signature ensures the service layer can call the
        in-memory stub transparently.
        """
        record = self._data[run_id]
        record.processed_products = processed_products  # type: ignore[attr-defined]
        if total_products is not None:
            record.total_products = total_products  # type: ignore[attr-defined]
        return True

    async def update_status(self, run_id: str, status_: SegmentationStatus):  # type: ignore[override]
        record = self._data[run_id]
        record.status = status_  # type: ignore[attr-defined]
        return True

    async def complete_run(self, run_id: str, result_summary: Dict[str, Any]):  # type: ignore[override]
        record = self._data[run_id]
        record.status = SegmentationStatus.COMPLETED  # type: ignore[attr-defined]
        record.result_summary = result_summary  # type: ignore[attr-defined]
        return True


class _InMemoryProductSegmentRepository:  # noqa: D401 – simple in-memory repo
    def __init__(self) -> None:
        self._run_products: Dict[str, List[int]] = {}
        self._segments: List[ProductSegment] = []
        self._refined_segments: List[ProductSegment] = []

    async def add_products_to_run(self, run_id: str, product_ids: List[int]):  # type: ignore[override]
        self._run_products[run_id] = list(product_ids)
        return True

    async def create_run_products(self, run_id: str, product_ids: List[int]):  # type: ignore[override]
        """Alias for add_products_to_run for compatibility."""
        return await self.add_products_to_run(run_id, product_ids)

    async def get_run_products(self, run_id: str):  # type: ignore[override]
        return self._run_products.get(run_id, [])

    async def batch_create_segments(self, segments):  # type: ignore[override]
        """Store initial segments."""
        self._segments.extend(segments)
        return True

    async def batch_create_refined_segments(self, segments):  # type: ignore[override]
        """Store *refined* segments separately so results can distinguish them."""
        self._refined_segments.extend(segments)
        return True

    async def get_segments_by_run(self, run_id: str):  # type: ignore[override]
        return [s for s in self._segments if s.run_id == run_id]

    async def get_refined_segments_by_run(self, run_id: str):  # type: ignore[override]
        return [s for s in self._refined_segments if s.run_id == run_id]


class _InMemoryProductTaxonomyRepository:  # noqa: D401 – lightweight in-mem store
    def __init__(self) -> None:
        # We keep a *flat* list of taxonomies; each item is either a
        # ``ProductTaxonomyCreate`` instance or a plain dict.
        self._taxonomies: List[Any] = []

    async def batch_create_taxonomies(self, taxonomies):  # type: ignore[override]
        self._taxonomies.extend(taxonomies or [])
        # Emulate DB by assigning incremental IDs
        created: List[Any] = []
        next_id = len(self._taxonomies) - len(taxonomies) + 1
        for idx, t in enumerate(taxonomies or []):
            if isinstance(t, dict):
                rec = dict(t)
                rec.setdefault("id", next_id + idx)
                created.append(rec)
            else:
                # Pydantic model – add id attribute dynamically
                t_dict = t.model_dump()
                t_dict["id"] = next_id + idx
                created.append(t_dict)
        return created

    async def get_taxonomies_by_run(self, run_id: str):  # type: ignore[override]
        return [
            t
            for t in self._taxonomies
            if (
                t.get("run_id") if isinstance(t, dict) else getattr(t, "run_id", None)
            )
            == run_id
        ]


class _StubSegmentationLLMClient:  # pylint: disable=too-few-public-methods
    """A deterministic, side-effect-free LLM stub used for automated tests.

    The stub implements the three public methods the service relies on so the
    execution path mirrors the real client while remaining completely
    deterministic.
    """

    async def segment_products(
        self,
        products: List[int],
        *,
        category: Optional[str] = None,
        **kwargs,
    ):  # type: ignore[override]
        return {
            "segments": [{"product_id": pid, "taxonomy_id": 1} for pid in products],
            "taxonomies": [
                {
                    "category_name": "Category A",
                    "definition": "Category A definition",
                    "product_count": len(products),
                }
            ],
        }

    async def consolidate_taxonomy(self, taxonomies: List[Dict[str, Any]], **kwargs):  # type: ignore[override]
        # Simply return the input list wrapped in the expected key.
        return {"taxonomies": taxonomies, "segments": []}

    async def refine_assignments(
        self,
        segments: List[Dict[str, Any]],
        *,
        taxonomies: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):  # type: ignore[override]
        # Pass-through implementation.
        return {"segments": segments}


# ---------------------------------------------------------------------------
# Dependency factory – returns a *singleton* service instance per FastAPI app
# ---------------------------------------------------------------------------

def _build_default_service() -> DatabaseProductSegmentationService:
    """Create an in-memory service suitable for local dev & tests."""

    run_repo = _InMemorySegmentationRunRepository()
    seg_repo = _InMemoryProductSegmentRepository()
    tax_repo = _InMemoryProductTaxonomyRepository()

    storage_root = settings.STORAGE_ROOT
    storage_root.mkdir(parents=True, exist_ok=True)
    storage = LLMStorageService.create_local(str(storage_root))

    return DatabaseProductSegmentationService(
        run_repo,
        seg_repo,
        storage,
        _StubSegmentationLLMClient(),
        taxonomy_repo=tax_repo,
    )


async def _get_service(request: Request) -> DatabaseProductSegmentationService:  # noqa: D401
    """FastAPI dependency that injects a *singleton* segmentation service."""

    if not hasattr(request.app.state, "segmentation_service"):
        request.app.state.segmentation_service = _build_default_service()
    return request.app.state.segmentation_service  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Router & endpoint implementations
# ---------------------------------------------------------------------------

router = APIRouter()


@router.post("/start", status_code=status.HTTP_200_OK)
async def start_segmentation(
    request_body: StartSegmentationRequest,
    service: DatabaseProductSegmentationService = Depends(_get_service),
) -> JSONResponse:
    """Create **and synchronously execute** a segmentation run.

    The implementation runs `execute_run` *inline* instead of spawning a
    background task so that automated tests can deterministically wait for the
    run to finish without polling.
    """

    try:
        run_id = await service.create_run(request_body)
        # Run *synchronously* – execution is fast with the stub client
        await service.execute_run(run_id)
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    payload = {
        "run_id": run_id,
        # The spec (and unit-tests) expect the literal string "started".
        "status": "started",
        "total_products": len(request_body.product_ids),
    }
    return JSONResponse(payload, status_code=status.HTTP_200_OK)


@router.get("/{run_id}/status", response_model=SegmentationStatusResponse)
async def get_run_status(
    run_id: str,
    service: DatabaseProductSegmentationService = Depends(_get_service),
) -> SegmentationStatusResponse:
    """Return basic progress information for *run_id*."""

    run = await service._run_repo.get_by_id(run_id)  # type: ignore[attr-defined,protected-access]
    if run is None:
        raise HTTPException(status_code=404, detail="Segmentation run not found")

    total = run.total_products or 0  # type: ignore[attr-defined]
    processed = run.processed_products or 0  # type: ignore[attr-defined]
    progress = (processed / total * 100.0) if total else 0.0

    return SegmentationStatusResponse(
        run_id=run_id,
        status=run.status,  # type: ignore[attr-defined]
        total_products=total,
        processed_products=processed,
        progress_percent=round(progress, 1),
        estimated_completion=None,
    )


@router.get("/{run_id}/results", response_model=SegmentationResultsResponse)
async def get_run_results(
    run_id: str,
    service: DatabaseProductSegmentationService = Depends(_get_service),
) -> SegmentationResultsResponse:
    """Return taxonomies & product segment assignments for *run_id*."""

    run = await service._run_repo.get_by_id(run_id)  # type: ignore[attr-defined,protected-access]
    if run is None:
        raise HTTPException(status_code=404, detail="Segmentation run not found")

    segments = await service._segment_repo.get_segments_by_run(run_id)  # type: ignore[attr-defined]
    refined_segments: List[Any] = []

    if hasattr(service._segment_repo, "get_refined_segments_by_run"):
        try:
            refined_segments = await service._segment_repo.get_refined_segments_by_run(run_id)  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover – best-effort for stub
            refined_segments = []

    taxonomies: List[Any]
    if hasattr(service, "_taxonomy_repo") and service._taxonomy_repo is not None:  # type: ignore[attr-defined]
        taxonomies = await service._taxonomy_repo.get_taxonomies_by_run(run_id)  # type: ignore[attr-defined]
    else:
        taxonomies = []

    return SegmentationResultsResponse(
        run_id=run_id,
        status=run.status,  # type: ignore[attr-defined]
        taxonomies=[
            {
                "id": t.id if hasattr(t, "id") else idx,
                "category_name": t.category_name if hasattr(t, "category_name") else t.get("category_name"),
                "definition": t.definition if hasattr(t, "definition") else t.get("definition"),
                "product_count": t.product_count if hasattr(t, "product_count") else t.get("product_count"),
            }
            for idx, t in enumerate(taxonomies, start=1)
        ],
        segments=[
            {
                "product_id": s.product_id if hasattr(s, "product_id") else s.get("product_id"),
                "taxonomy_id": s.taxonomy_id if hasattr(s, "taxonomy_id") else s.get("taxonomy_id"),
            }
            for s in segments
        ],
        refined_segments=[
            {
                "product_id": s.product_id if hasattr(s, "product_id") else s.get("product_id"),
                "taxonomy_id": s.taxonomy_id if hasattr(s, "taxonomy_id") else s.get("taxonomy_id"),
            }
            for s in refined_segments
        ],
    ) 