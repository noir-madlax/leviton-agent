from __future__ import annotations

"""FastAPI router for Review Analysis module."""

import logging
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from review_analysis.models import ReviewAnalysisRequest
from review_analysis.services.db_review_analysis import DatabaseReviewAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/review-analysis", tags=["review-analysis"])


async def _get_service() -> DatabaseReviewAnalysisService:  # noqa: D401
    """Lazy singleton injection for the review-analysis service."""

    if not hasattr(_get_service, "_instance"):
        _get_service._instance = DatabaseReviewAnalysisService()  # type: ignore[attr-defined]
    return _get_service._instance  # type: ignore[return-value]


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def start_review_analysis(
    body: ReviewAnalysisRequest,
    bg: BackgroundTasks,
    service: DatabaseReviewAnalysisService = Depends(_get_service),
) -> dict[str, Any]:
    """Kick off review analysis asynchronously and return analysis_id."""

    try:
        analysis_id = await service.analyse(body)
    except Exception as exc:  # pylint: disable=broad-except
        logger.exception("Review analysis failed to start: %s", exc)
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    # Nothing else to return yet – client can poll another endpoint later
    return {"analysis_id": analysis_id} 