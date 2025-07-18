import asyncio
import logging
import time

import pytest
from httpx import AsyncClient

# FastAPI application
from backend.main import app

# Supabase connection helper (service-level credentials)
from core.database.connection import get_supabase_service_client

# Handle differing httpx versions (>=0.26 drop 'app' arg)
try:
    from httpx import ASGITransport  # httpx >= 0.26
except ImportError:  # noqa: WPS440
    try:
        from httpx._transports.asgi import ASGITransport  # type: ignore
    except ImportError:
        ASGITransport = None  # type: ignore

RESULT_SAMPLE_SIZE = 20
MAX_PRODUCTS = 60

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("product_segment.services").setLevel(logging.INFO)
logging.getLogger("core.utils.llm_utils").setLevel(logging.INFO)


@pytest.mark.asyncio
async def test_segmentation_end_to_end_dimmer_switches():
    """Full integration test – API → DB (Dimmer Switches category).

    1. Fetch all product IDs from *amazon_products* where ``category_l5_id`` ==
       507840.
    2. POST /api/segmentation/product-segment to create a new run.
    3. Poll ``product_segment_runs`` until the stage reaches *completed*.
    4. Assert every assignment has a *refined* taxonomy and at least one
       taxonomy row exists for the run.
    """

    # ------------------------------------------------------------------
    # 1) Collect input product-ids from the real DB
    # ------------------------------------------------------------------
    sb = get_supabase_service_client()  # service-level privileges
    category_l5_id = 507840
    category_name = "Dimmer Switches"

    res = (
        sb.table("product_wide_table")
        .select("id")
        .eq("category_l5_id", category_l5_id)
        .execute()
    )
    assert res.data, f"No products found for category '{category_name}'"
    product_ids = list(set([row["id"] for row in res.data]))
    if len(product_ids) > MAX_PRODUCTS:
        product_ids = product_ids[:MAX_PRODUCTS]

    # ------------------------------------------------------------------
    # 2) Fire off the segmentation run via API
    # ------------------------------------------------------------------
    if ASGITransport is None:
        # Fall back to deprecated but maybe still available signature
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/segmentation/product-segment",
                json={
                    "product_ids": product_ids,
                    "product_category": category_name,
                },
            )
    else:
        try:
            transport = ASGITransport(app=app, lifespan="auto")  # httpx >= 0.26
        except TypeError:  # older signature without lifespan
            transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/segmentation/product-segment",
                json={
                    "product_ids": product_ids,
                    "product_category": category_name,
                },
            )

    # 202 Accepted is expected, Location header contains the run-id
    assert response.status_code == 202, response.text
    location = response.headers.get("Location")
    assert location, "Location header missing in response"
    # Location looks like '/product-segment/<RUN_ID>'
    parts = [p for p in location.split("/") if p]
    run_id = parts[1] if len(parts) >= 2 else None
    assert run_id and run_id.startswith("RUN_"), (
        f"Unexpected run_id extracted from Location: {run_id}")

    # ------------------------------------------------------------------
    # 3) Poll DB until the run completes (or fails / times out)
    # ------------------------------------------------------------------
    timeout_s = 900  # 15 min hard timeout – adjust if necessary
    poll_interval = 10
    stage = None
    deadline = time.time() + timeout_s

    last_report = ""
    while time.time() < deadline:
        run_res = (
            sb.table("product_segment_runs")
            # Only select the current stage – progress counters were removed
            .select("stage")
            .eq("id", run_id)
            .execute()
        )

        if run_res.data:
            row = run_res.data[0]
            stage = row["stage"]

            report = f"Stage: {stage}"
            if report != last_report:
                print(report, flush=True)
                last_report = report

            # ------------------------------------------------------------------
            # Output small sample of results relevant to the current stage
            # ------------------------------------------------------------------
            try:
                if stage == "extraction":
                    tax_sample = (
                        sb.table("product_segment_taxonomies")
                        .select("segment_name,stage")
                        .eq("run_id", run_id)
                        .order("id")
                        .limit(RESULT_SAMPLE_SIZE)
                        .execute()
                    )
                    names = [row["segment_name"] for row in tax_sample.data] if tax_sample.data else []
                    print("  ↳ Sample extracted taxonomies:", names, flush=True)

                elif stage == "consolidation":
                    tax_sample = (
                        sb.table("product_segment_taxonomies")
                        .select("segment_name,stage")
                        .eq("run_id", run_id)
                        .order("id")
                        .limit(RESULT_SAMPLE_SIZE)
                        .execute()
                    )
                    names = [f"{row['segment_name']} ({row['stage']})" for row in tax_sample.data] if tax_sample.data else []
                    print("  ↳ Sample consolidated taxonomies:", names, flush=True)

                elif stage == "refinement":
                    assign_sample = (
                        sb.table("product_segment_assignments")
                        .select("product_id,taxonomy_id_refined")
                        .eq("run_id", run_id)
                        .limit(RESULT_SAMPLE_SIZE)
                        .execute()
                    )
                    sample_rows = [
                        {
                            "product_id": row["product_id"],
                            "taxonomy_id_refined": row["taxonomy_id_refined"],
                        }
                        for row in assign_sample.data or []
                    ]
                    print("  ↳ Sample refined assignments:", sample_rows, flush=True)
                elif stage == "completed":
                    # Show a glimpse of the final consolidated + refined taxonomies
                    tax_sample = (
                        sb.table("product_segment_taxonomies")
                        .select("segment_name,stage")
                        .eq("run_id", run_id)
                        .order("id")
                        .limit(RESULT_SAMPLE_SIZE)
                        .execute()
                    )
                    names = [f"{row['segment_name']} ({row['stage']})" for row in tax_sample.data] if tax_sample.data else []
                    print("  ↳ Final taxonomies:", names, flush=True)
            except Exception as exc:  # noqa: BLE001
                # Non-fatal – just log sample query failures
                print(f"  ↳ Failed to fetch sample data: {exc}", flush=True)

            if stage == "completed":
                break
            if stage == "failed":
                pytest.fail(f"Segmentation run {run_id} failed (stage=failed)")

        await asyncio.sleep(poll_interval)

    assert stage == "completed", (
        f"Segmentation run did not reach 'completed' within {timeout_s}s (last stage={stage})"
    )

    # ------------------------------------------------------------------
    # 4) Validate refined assignments & taxonomies
    # ------------------------------------------------------------------
    assign_res = (
        sb.table("product_segment_assignments")
        .select("product_id,taxonomy_id_refined")
        .eq("run_id", run_id)
        .execute()
    )
    assignments = assign_res.data or []

    # Expect one assignment per product
    assert len(assignments) == len(product_ids), (
        "Mismatch between input products and assignments in DB"
    )
    assert all(a["taxonomy_id_refined"] is not None for a in assignments), (
        "Some products are missing a refined taxonomy assignment"
    )

    # Ensure no product is still mapped to the placeholder "__UNASSIGNED__" taxonomy
    unassigned_tax_res = (
        sb.table("product_segment_taxonomies")
        .select("id")
        .eq("run_id", run_id)
        .eq("segment_name", "__UNASSIGNED__")
        .limit(1)
        .execute()
    )
    if unassigned_tax_res.data:
        unassigned_id = unassigned_tax_res.data[0]["id"]
        assert all(a["taxonomy_id_refined"] != unassigned_id for a in assignments), (
            "Some products remain assigned to the '__UNASSIGNED__' taxonomy after consolidation"
        )

    tax_res = (
        sb.table("product_segment_taxonomies")
        .select("id,segment_name")
        .eq("run_id", run_id)
        .execute()
    )
    assert tax_res.data, "No taxonomy rows were persisted for the run"

    # ------------------------------------------------------------------
    # 5) Log a small sample of *final* assignments (product title → taxonomy)
    # ------------------------------------------------------------------
    try:
        tax_map = {row["id"]: row.get("segment_name") for row in tax_res.data or []}

        final_sample = (
            sb.table("product_segment_assignments")
            .select("product_id,taxonomy_id_refined")
            .eq("run_id", run_id)
            .limit(RESULT_SAMPLE_SIZE)
            .execute()
        )

        prod_ids_sample = [row["product_id"] for row in final_sample.data or []]

        if prod_ids_sample:
            prod_rows = (
                sb.table("product_wide_table")
                .select("id,title")
                .in_("id", prod_ids_sample)
                .execute()
            )

            if prod_rows.data:
                prod_title_map = {row["id"]: row["title"] for row in prod_rows.data}

            print("\n📦 Final assignment sample (up to", RESULT_SAMPLE_SIZE, "rows):", flush=True)
            for row in final_sample.data or []:
                pid = row["product_id"]
                tax_id = row["taxonomy_id_refined"]
                title = prod_title_map.get(pid, "<unknown title>")
                tax_name = tax_map.get(tax_id, "<unknown taxonomy>")
                print(f"  • {pid}: '{title[:60]}' → {tax_name}", flush=True)
    except Exception as exc:  # noqa: BLE001
        print(f"⚠️  Failed to log final assignment sample: {exc}", flush=True) 