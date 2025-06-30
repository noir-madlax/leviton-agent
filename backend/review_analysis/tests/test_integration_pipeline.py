import os
import sys
import importlib
import pytest
import time
import asyncio
from pathlib import Path

# Insert the *project root* (two levels above ``backend/``) into ``sys.path`` so
# that ``import backend`` resolves regardless of the current working directory.
# parents[3] -> <repo_root>/ (leviton-agent)
root_dir = Path(__file__).resolve().parents[3]
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi import FastAPI
from httpx import AsyncClient
from dataclasses import asdict

# Ensure the global 'config' module resolves to backend.config to satisfy
# core.database.connection imports before review_analysis modules load.
if 'config' not in sys.modules:
    sys.modules['config'] = importlib.import_module('backend.config')

from review_analysis.api import router as review_router
from review_analysis.models import ReviewAnalysisRequest
from core.database.connection import get_supabase_service_client

pytestmark = pytest.mark.integration

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
    pytest.skip("Supabase credentials not set – integration test skipped", allow_module_level=True)

# Handle differing httpx versions (>=0.26 drop 'app' arg)
try:
    from httpx import ASGITransport  # httpx >= 0.26
except ImportError:  # noqa: WPS440
    try:
        from httpx._transports.asgi import ASGITransport  # type: ignore
    except ImportError:
        ASGITransport = None  # type: ignore

@pytest.mark.asyncio
async def test_full_review_analysis_pipeline() -> None:
    """Run full pipeline against real Supabase and assert rows are written."""

    sb_client = get_supabase_service_client()

    # project and product list
    project_id = "INTEGRATION_TEST_PROJ"
    product_category = "Dimmer Switches"
    product_ids = ["B08PKMT2DV", "B0771BC2YH", "B004DZONXI"]

    # Ensure we have reviews for these products
    reviews = (
        sb_client.table("product_reviews")
        .select("product_id")
        .in_("product_id", product_ids)
        .limit(1)
        .execute()
        .data
    )
    if not reviews:
        pytest.skip("Required ASIN sample reviews not present in database", allow_module_level=False)

    # --- call API --------------------------------------------------------
    app = FastAPI()
    app.include_router(review_router)

    req = ReviewAnalysisRequest(
        project_id=project_id,
        product_ids=product_ids,
        product_category=product_category,
    )

    # ------------------------------------------------------------------
    # Fire request via ASGITransport-compatible AsyncClient (httpx >=0.26)
    # ------------------------------------------------------------------
    if ASGITransport is None:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            resp = await ac.post("/review-analysis", json=asdict(req))
    else:
        try:
            transport = ASGITransport(app=app, lifespan="auto")  # httpx >=0.26
        except TypeError:  # older signature without lifespan
            transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.post("/review-analysis", json=asdict(req))

    assert resp.status_code == 202, resp.text
    analysis_id = resp.json().get("analysis_id")
    assert analysis_id, "analysis_id missing in response"

    # ------------------------------------------------------------------
    # Poll DB for progress & print small samples, similar to segmentation
    # ------------------------------------------------------------------
    timeout_s = 600  # 10 min hard timeout
    poll_interval = 10
    deadline = time.time() + timeout_s

    aspects_done = False
    cat_categorised = False
    cat_final = False

    last_report = ""

    while time.time() < deadline:
        stage_parts = []

        # Aspects inserted? -------------------------------------------
        aspects = (
            sb_client.table("review_analysis_aspects")
            .select("aspect_pk, detail_text, category_pk")
            .eq("project_id", project_id)
            .limit(20)
            .execute()
            .data
        )
        if aspects and not aspects_done:
            sample = [a["detail_text"] for a in aspects[:5]]
            print("Extracted aspects sample:", sample, flush=True)
            aspects_done = True

        # Categories categorised --------------------------------------
        categories_cat = (
            sb_client.table("review_analysis_aspect_categories")
            .select("name, stage")
            .eq("project_id", project_id)
            .eq("stage", "categorisation")
            .limit(20)
            .execute()
            .data
        )
        if categories_cat and not cat_categorised:
            names = [c["name"] for c in categories_cat[:5]]
            print("Categorised categories sample:", names, flush=True)
            cat_categorised = True

        # Final categories --------------------------------------------
        categories_final = (
            sb_client.table("review_analysis_aspect_categories")
            .select("name")
            .eq("project_id", project_id)
            .eq("stage", "final")
            .limit(20)
            .execute()
            .data
        )
        if categories_final and not cat_final:
            names = [c["name"] for c in categories_final[:5]]
            print("Final consolidated categories sample:", names, flush=True)
            cat_final = True

        # All done? ----------------------------------------------------
        if aspects_done and cat_final:
            # Ensure majority aspects assigned
            unassigned = (
                sb_client.table("review_analysis_aspects")
                .select("aspect_pk")
                .eq("project_id", project_id)
                .is_("category_pk", "null")
                .limit(1)
                .execute()
                .data
            )
            if not unassigned:
                break

        # progress message throttle
        report = f"aspects: {'Y' if aspects_done else 'N'}, final cats: {'Y' if cat_final else 'N'}"
        if report != last_report:
            print(report, flush=True)
            last_report = report

        await asyncio.sleep(poll_interval)

    assert aspects_done, "No aspects persisted"
    assert cat_final, "No final categories persisted"

    # Clean up
    sb_client.table("review_analysis_aspects").delete().eq("project_id", project_id).execute()
    sb_client.table("review_analysis_aspect_categories").delete().eq("project_id", project_id).execute()
    sb_client.table("product_review_analysis").delete().eq("project_id", project_id).execute()
    sb_client.table("product_reviews").delete().eq("product_id", product_ids[0]).execute() 