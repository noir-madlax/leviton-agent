"""REST API router (v6.2) for the *product_segmentation* engine.

This module implements the **final** public surface specified in
``backend/product_segmentation/README_product_segmentation.md``.

Endpoints
---------
``POST /product-segmentation``
   Start a new segmentation run for an explicit list of Amazon ``product_ids``.

   Request body::

       {
         "product_ids": [123, 456, 789],
         "product_category": "Dimmer Switches"
       }

   Response::

       HTTP/1.1 202 Accepted
       Location: /product-segmentation/RUN_<ISO>_<hash>/stream

Backward-compatibility notes
---------------------------
• The legacy ``/api/segmentation/*`` routes have been removed.
• ``segment_name`` has been consolidated into the database schema; clients
  should now provide only ``product_category`` in the create-run request.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, List, Dict

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, Response, status
from fastapi.responses import StreamingResponse, JSONResponse

from product_segmentation.models import (
    StartSegmentationRequest,
    SegmentationStage,
)
from product_segmentation.services.db_product_segmentation import DatabaseProductSegmentationService


async def _get_service(request: Request) -> DatabaseProductSegmentationService:  # noqa: D401
    """FastAPI dependency that injects a *singleton* segmentation service."""

    return request.app.state.segmentation_service  # type: ignore[attr-defined]


# ---------------------------------------------------------------------------
# Router & endpoint implementations
# ---------------------------------------------------------------------------

router = APIRouter(prefix="/product-segmentation", tags=["product-segmentation"])


# ---------------------------------------------------------------------------
# Request/response models for the *new* API layer only. We keep them **local**
# to avoid rippling changes through the service code.
# ---------------------------------------------------------------------------


class CreateSegmentationRunRequest(StartSegmentationRequest):
    """Request body for ``POST /product-segmentation`` (v6.2).

    Public field names follow README §5.1.  The *product_category* indicates
    the high-level Amazon category of all supplied products.
    """

    product_category: str  # noqa: D401 – public field required by spec

    model_config = {
        "populate_by_name": True,
    }

    # Aliases so we can pass through to the service without changes.
    @property
    def category(self) -> str:  # pragma: no cover – alias expected by service
        return self.product_category


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

    # Location → progress stream -------------------------------------------
    headers = {"Location": f"/product-segmentation/{run_id}/stream"}
    return Response(status_code=status.HTTP_202_ACCEPTED, headers=headers)