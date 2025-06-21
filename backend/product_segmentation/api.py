"""REST API router (v6.2) for the *product_segmentation* engine.

This module implements the **final** public surface specified in
``backend/product_segmentation/README_product_segmentation.md``.

Endpoints
---------
1. ``POST /product-segmentation``
   Start a new segmentation run for an explicit list of Amazon ``product_ids``.

   Request body::

       {
         "product_ids": [123, 456, 789],
         "product_category": "Dimmer Switches"
       }

   Response::

       HTTP/1.1 202 Accepted
       Location: /product-segmentation/RUN_<ISO>_<hash>/stream

2. ``GET /product-segmentation/{run_id}/stream``
   Server-Sent Events (``text/event-stream``) that emits *progress* events::

       progress: {"run_id":"RUN_…","percent":37.5}

   The stream closes automatically once the run reaches *completed* or *failed*.

3. ``GET /product-segmentation/{run_id}/segments``
   Return the **final taxonomy assignment** *and* the complete taxonomy list::

       {
         "run_id": "RUN_…",
         "taxonomies": [
           {"id": 1, "segment_name": "Premium Switches", "definition": "High-end smart dimmers", "product_count": 42},
           …
         ],
         "segments": [
           {"product_id": 123, "taxonomy_id": 1},
           …
         ]
       }

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


@router.get("/{run_id}/stream")
async def stream_progress(
    run_id: str,
    request: Request,
    service: DatabaseProductSegmentationService = Depends(_get_service),
):
    """Server-Sent Events stream that pushes progress updates (v6.2)."""

    async def _event_generator():  # noqa: D401 – nested helper
        last_percent: float = -1.0

        while True:
            # Detect client disconnect early.
            if await request.is_disconnected():
                break

            run = await service._run_repo.get_by_id(run_id)  # type: ignore[attr-defined,protected-access]
            if run is None:
                # We cannot raise inside generator → yield *once* then stop.
                payload = {
                    "run_id": run_id,
                    "error": "Segmentation run not found",
                }
                yield f"event: error\ndata: {json.dumps(payload)}\n\n"
                break

            percent = _progress_percent(run)
            if percent != last_percent:
                payload = {
                    "run_id": run_id,
                    "percent": percent,
                    "stage": getattr(run, "stage", SegmentationStage.INIT),
                }
                yield f"event: progress\ndata: {json.dumps(payload)}\n\n"
                last_percent = percent

            if getattr(run, "stage", None) in (SegmentationStage.COMPLETED, SegmentationStage.FAILED):
                break

            await asyncio.sleep(0.5)

    return StreamingResponse(_event_generator(), media_type="text/event-stream")


# ---------------------------------------------------------------------------
# New endpoint – final segments per product
# ---------------------------------------------------------------------------


@router.get("/{run_id}/segments")
async def get_final_segments(
    run_id: str,
    service: DatabaseProductSegmentationService = Depends(_get_service),
) -> JSONResponse:
    """Return the *final* taxonomy assignment for every product in a run.

    The endpoint looks for refined segments first; if none exist it falls back
    to the initial segmentation result.
    """

    # Retrieve run – mainly to validate existence
    run = await service._run_repo.get_by_id(run_id)  # type: ignore[attr-defined,protected-access]
    if run is None:
        raise HTTPException(status_code=404, detail="Segmentation run not found")

    # Preferred: refined segments
    segments = await service._segment_repo.get_refined_segments_by_run(run_id)  # type: ignore[attr-defined]

    # -------------------------------
    # Build output ------------------
    # -------------------------------
    segment_payload = [
        {
            "product_id": s.product_id if hasattr(s, "product_id") else s.get("product_id"),
            "taxonomy_id": s.taxonomy_id if hasattr(s, "taxonomy_id") else s.get("taxonomy_id"),
        }
        for s in segments
    ]

    taxonomy_payload: List[Dict[str, Any]] = []
    taxonomies = await service._taxonomy_repo.get_taxonomies_by_run(run_id)  # type: ignore[attr-defined]
    taxonomy_payload = [
        {
            "id": t.id if hasattr(t, "id") else idx,
            "segment_name": t.segment_name if hasattr(t, "segment_name") else t.get("segment_name"),
            "definition": t.definition if hasattr(t, "definition") else t.get("definition"),
            "product_count": t.product_count if hasattr(t, "product_count") else t.get("product_count"),
        }
        for idx, t in enumerate(taxonomies, start=1)
    ]

    payload = {
        "run_id": run_id,
        "segments": segment_payload,
        "taxonomies": taxonomy_payload,
    }

    return JSONResponse(payload, status_code=status.HTTP_200_OK) 