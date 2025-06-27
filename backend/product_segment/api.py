"""REST API router (v6.2) for the *product_segment* engine.

This module implements the **final** public surface specified in
``backend/product_segment/README_product_segmentation.md``.

Endpoints
---------
``POST /product-segment``
   Start a new segmentation run for an explicit list of Amazon ``product_ids``.

   Request body::

       {
         "product_ids": [123, 456, 789],
         "product_category": "Dimmer Switches"
       }

   Response::

       HTTP/1.1 202 Accepted
       Location: /product-segment/RUN_<ISO>_<hash>

Backward-compatibility notes
---------------------------
• The legacy ``/api/segmentation/*`` routes have been removed.
• ``segment_name`` has been consolidated into the database schema; clients
  should now provide only ``product_category`` in the create-run request.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status

from product_segment.models import StartSegmentationRequest

# Supabase connection & repositories
from core.database.connection import get_supabase_service_client
from product_segment.repositories.product_segment_assignment_repository import (
    ProductSegmentRepository,
)
from product_segment.repositories.product_segment_run_repository import (
    SegmentationRunRepository,
)
from product_segment.repositories.product_segment_taxonomy_repository import (
    ProductTaxonomyRepository,
)
from product_segment.services.db_product_segmentation import DatabaseProductSegmentationService


async def _get_service(request: Request) -> DatabaseProductSegmentationService:  # noqa: D401
    """FastAPI dependency that injects a *singleton* segmentation service."""

    if not hasattr(request.app.state, "product_segment_service"):
        # Lazy one-time construction when first requested
        sb_client = get_supabase_service_client()

        run_repo = SegmentationRunRepository(sb_client)
        assignment_repo = ProductSegmentRepository(sb_client)
        taxonomy_repo = ProductTaxonomyRepository(sb_client)

        request.app.state.product_segment_service = DatabaseProductSegmentationService(
            run_repo=run_repo,
            segment_repo=assignment_repo,
            taxonomy_repo=taxonomy_repo,
        )

    return request.app.state.product_segment_service  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Router & endpoint implementations
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/product-segment", tags=["product-segment"])


# ---------------------------------------------------------------------------
# Request/response models for the *new* API layer only. We keep them **local**
# to avoid rippling changes through the service code.
# ---------------------------------------------------------------------------


class CreateSegmentationRunRequest(StartSegmentationRequest):
    """Local wrapper identical to :class:`StartSegmentationRequest`.

    Exists only so the public OpenAPI schema can evolve independently from
    the service contract.  All field/alias handling is already implemented in
    the base dataclass – no additional properties required here.
    """


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def _progress_percent(run_obj: Any) -> float:
    """Derive a *single* progress percentage from a run DB/DTO record.

    If the newer stage-specific counters are present we compute the value
    according to the formula in README §5.3, otherwise we fall back to the
    simple *processed_products / total_products* ratio so the endpoint still
    works with stub repositories.
    """

    # New schema – calls_done / calls_total ---------------------------------
    calls_done = getattr(run_obj, "seg_batches_done", None)
    calls_total = getattr(run_obj, "seg_batches_total", None)

    if calls_done is not None and calls_total:
        # Consolidation ------------------------------------------------------
        c_done = getattr(run_obj, "con_batches_done", 0)
        c_total = getattr(run_obj, "con_batches_total", 0)
        calls_done += c_done
        calls_total += c_total

        # Refinement ---------------------------------------------------------
        r_done = getattr(run_obj, "ref_batches_done", 0)
        r_total = getattr(run_obj, "ref_batches_total", 0)
        calls_done += r_done
        calls_total += r_total

        if calls_total:
            return round((calls_done / calls_total) * 100, 1)

    # Legacy fallback --------------------------------------------------------
    total = getattr(run_obj, "total_products", 0) or 0
    processed = getattr(run_obj, "processed_products", 0) or 0
    return round((processed / total * 100.0), 1) if total else 0.0


# ---------------------------------------------------------------------------
# Endpoint implementations (v6.2)
# ---------------------------------------------------------------------------


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_and_start_run(
    request_body: CreateSegmentationRunRequest,
    background_tasks: BackgroundTasks,
    service: DatabaseProductSegmentationService = Depends(_get_service),
) -> Response:
    """Create **and asynchronously execute** a segmentation run (v6.2).

    • Returns *202 Accepted* with a ``Location`` header – no JSON body.
    • ``service.execute_run`` is scheduled as a background task so API
      responsiveness does not depend on LLM latency.
    """

    # --- create run --------------------------------------------------------
    try:
        run_id = await service.create_run(request_body)  # type: ignore[arg-type]
    except Exception as exc:  # pylint: disable=broad-except
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # --- trigger processing asynchronously ---------------------------------
    background_tasks.add_task(service.execute_run, run_id)

    # Location header points to the run resource (no longer /stream endpoint)
    headers = {"Location": f"/product-segment/{run_id}"}
    return Response(status_code=status.HTTP_202_ACCEPTED, headers=headers)