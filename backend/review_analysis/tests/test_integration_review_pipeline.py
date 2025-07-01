import os
import sys
import importlib
import pytest
import time
import asyncio
import logging
from datetime import datetime
from pathlib import Path

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

def log_with_timestamp(message: str, level: str = "INFO") -> None:
    """Helper function to log messages with consistent timestamp format."""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    print(f"[{timestamp}] {message}", flush=True)  # Force immediate output
    if level.upper() == "INFO":
        logger.info(f"[{timestamp}] {message}")
    elif level.upper() == "ERROR":
        logger.error(f"[{timestamp}] {message}")
    elif level.upper() == "WARNING":
        logger.warning(f"[{timestamp}] {message}")
    elif level.upper() == "DEBUG":
        logger.debug(f"[{timestamp}] {message}")

# Fix the config module collision by ensuring we import the main backend config
print("🔧 Setting up path and config resolution...", flush=True)
backend_root = Path(__file__).resolve().parent.parent
if str(backend_root) not in sys.path:
    sys.path.insert(0, str(backend_root))

# Ensure main config is used instead of review_analysis config
main_config_path = backend_root / "config.py"
if main_config_path.exists():
    import config as main_config
    sys.modules['config'] = main_config
    print("✅ Main config module set up", flush=True)

print("📦 Starting imports...", flush=True)
from httpx import AsyncClient
from dataclasses import asdict

# Import the main app like the working test does
print("📦 Importing main app...", flush=True)
try:
    from main import app
    print("✅ Main app imported", flush=True)
except Exception as e:
    print(f"❌ Import failed: {e}", flush=True)
    raise

print("📦 Importing review_analysis modules...", flush=True)
try:
    from review_analysis.models import ReviewAnalysisRequest
    print("✅ review_analysis.models imported", flush=True)
    from core.database.connection import get_supabase_service_client
    print("✅ core.database.connection imported", flush=True)
except Exception as e:
    print(f"❌ Import failed: {e}", flush=True)
    raise

pytestmark = pytest.mark.integration

print("🔍 Checking environment variables...", flush=True)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")

print(f"SUPABASE_URL present: {'✅' if SUPABASE_URL else '❌'}", flush=True)
print(f"SUPABASE_SERVICE_KEY present: {'✅' if SUPABASE_SERVICE_KEY else '❌'}", flush=True)

if not (SUPABASE_URL and SUPABASE_SERVICE_KEY):
    print("❌ Supabase credentials not set – skipping test", flush=True)
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
    
    print("🎬 TEST FUNCTION STARTED", flush=True)
    test_start_time = time.time()
    log_with_timestamp("🚀 Starting full review analysis pipeline integration test")

    print("🔌 Creating Supabase client...", flush=True)
    try:
        sb_client = get_supabase_service_client()
        print("✅ Supabase client created successfully", flush=True)
        log_with_timestamp("✅ Supabase client initialized successfully")
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}", flush=True)
        raise

    # project and product list
    project_id = "INTEGRATION_TEST_PROJ"
    product_category = "Dimmer Switches"
    product_ids = ["B08PKMT2DV", "B0771BC2YH", "B004DZONXI"]
    
    print(f"📋 Test parameters set: project_id={project_id}, category={product_category}", flush=True)
    log_with_timestamp(f"📋 Test parameters - Project ID: {project_id}, Category: {product_category}, Product IDs: {product_ids}")

    # Ensure we have reviews for these products
    print("🔍 About to query for existing reviews...", flush=True)
    log_with_timestamp("🔍 Checking for existing reviews in database...")
    reviews_check_start = time.time()
    
    try:
        print("🔍 Executing product_reviews query...", flush=True)
        reviews = (
            sb_client.table("product_reviews")
            .select("product_id")
            .in_("product_id", product_ids)
            .limit(1)
            .execute()
            .data
        )
        print(f"✅ Reviews query completed, found {len(reviews)} results", flush=True)
        reviews_check_time = time.time() - reviews_check_start
    except Exception as e:
        print(f"❌ Reviews query failed: {e}", flush=True)
        raise
    
    if not reviews:
        print("❌ No reviews found - skipping test", flush=True)
        log_with_timestamp("❌ Required ASIN sample reviews not present in database", "ERROR")
        pytest.skip("Required ASIN sample reviews not present in database", allow_module_level=False)
    
    print(f"✅ Found {len(reviews)} reviews", flush=True)
    log_with_timestamp(f"✅ Found reviews in database (check took {reviews_check_time:.2f}s)")

    # --- Clean up any existing test data --------------------------------
    print("🧹 Starting cleanup phase...", flush=True)
    cleanup_start_time = time.time()
    log_with_timestamp(f"🧹 Starting cleanup of existing test data for project_id: {project_id}")
    
    try:
        # First, get a complete count of what exists
        print("🔍 Getting complete inventory of existing data...", flush=True)
        
        existing_aspects_count = sb_client.table("review_analysis_aspects").select("aspect_pk", count="exact").eq("project_id", project_id).execute()
        aspects_total = existing_aspects_count.count if hasattr(existing_aspects_count, 'count') else len(existing_aspects_count.data)
        print(f"📊 Found {aspects_total} total aspects for project {project_id}", flush=True)
        log_with_timestamp(f"📊 Found {aspects_total} total aspects for project {project_id}")
        
        existing_categories_count = sb_client.table("review_analysis_aspect_categories").select("category_pk", count="exact").eq("project_id", project_id).execute()
        categories_total = existing_categories_count.count if hasattr(existing_categories_count, 'count') else len(existing_categories_count.data)
        print(f"📊 Found {categories_total} total categories for project {project_id}", flush=True)
        log_with_timestamp(f"📊 Found {categories_total} total categories for project {project_id}")
        
        if aspects_total > 0 or categories_total > 0:
            print(f"🚨 FOUND EXISTING DATA! This will cause duplicate key errors. Failing test immediately.", flush=True)
            log_with_timestamp(f"🚨 FOUND EXISTING DATA! {aspects_total} aspects and {categories_total} categories found", "ERROR")
            raise AssertionError(f"Test environment is dirty: {aspects_total} aspects and {categories_total} categories still exist from previous runs. Clean the database manually before running this test.")
        
        print("✅ Database is clean - no existing test data found", flush=True)
        log_with_timestamp("✅ Database is clean - no existing test data found")
        
        cleanup_time = time.time() - cleanup_start_time
        print(f"✅ Cleanup verification completed in {cleanup_time:.2f}s", flush=True)
        log_with_timestamp(f"✅ Cleanup verification completed in {cleanup_time:.2f}s")
        
    except AssertionError:
        # Re-raise assertion errors
        raise
    except Exception as e:
        cleanup_time = time.time() - cleanup_start_time
        print(f"❌ Cleanup verification failed: {e} (took {cleanup_time:.2f}s)", flush=True)
        log_with_timestamp(f"❌ Cleanup verification failed: {e} (took {cleanup_time:.2f}s)", "ERROR")
        raise

    # --- call API --------------------------------------------------------
    print("🏗️ Setting up API call...", flush=True)
    log_with_timestamp("🏗️ Setting up FastAPI application and request...")
    # Use the main app instead of creating a new one
    # app = FastAPI()
    # app.include_router(review_router)

    req = ReviewAnalysisRequest(
        project_id=project_id,
        product_ids=product_ids,
        product_category=product_category,
    )
    print(f"📝 Request object created", flush=True)
    log_with_timestamp(f"📝 Request created: {asdict(req)}")

    # ------------------------------------------------------------------
    # Fire request via ASGITransport-compatible AsyncClient (httpx >=0.26)
    # ------------------------------------------------------------------
    api_call_start = time.time()
    print("🌐 About to send API request...", flush=True)
    log_with_timestamp("🌐 Sending API request to start review analysis pipeline...")
    
    if ASGITransport is None:
        print("🔧 Using legacy AsyncClient", flush=True)
        log_with_timestamp("🔧 Using legacy httpx AsyncClient (no ASGITransport)")
        async with AsyncClient(app=app, base_url="http://test") as ac:
            print("📤 Sending POST request...", flush=True)
            resp = await ac.post("/api/v1/review-analysis", json=asdict(req))
            print(f"📥 Got response: {resp.status_code}", flush=True)
    else:
        print("🔧 Using modern AsyncClient with ASGITransport", flush=True)
        log_with_timestamp("🔧 Using modern httpx AsyncClient with ASGITransport")
        try:
            transport = ASGITransport(app=app, lifespan="auto")  # httpx >=0.26
        except TypeError:  # older signature without lifespan
            transport = ASGITransport(app=app)

        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            print("📤 Sending POST request...", flush=True)
            resp = await ac.post("/api/v1/review-analysis", json=asdict(req))
            print(f"📥 Got response: {resp.status_code}", flush=True)

    api_call_time = time.time() - api_call_start
    log_with_timestamp(f"📡 API call completed in {api_call_time:.2f}s with status: {resp.status_code}")
    
    assert resp.status_code == 202, resp.text
    analysis_id = resp.json().get("analysis_id")
    assert analysis_id, "analysis_id missing in response"
    log_with_timestamp(f"✅ Pipeline started successfully with analysis_id: {analysis_id}")

    # ------------------------------------------------------------------
    # Poll DB for progress & print small samples, similar to segmentation
    # ------------------------------------------------------------------
    timeout_s = 900  # 15 min timeout to accommodate slower aspect assignment
    poll_interval = 10
    no_progress_timeout = 480  # 8 minutes - fail if no progress
    deadline = time.time() + timeout_s
    polling_start_time = time.time()
    last_change_time = time.time()
    
    log_with_timestamp(f"⏰ Starting progress polling with {timeout_s}s timeout and {poll_interval}s intervals")
    log_with_timestamp(f"🚨 No-progress timeout: {no_progress_timeout}s (will fail if no changes detected)")

    aspects_done = False
    cat_categorised = False
    cat_final = False

    last_report = ""
    poll_count = 0
    last_aspects_count = 0
    last_categories_count = 0
    last_assigned_count = 0

    def create_progress_bar(current: int, total: int, width: int = 30) -> str:
        """Create a simple text progress bar."""
        if total == 0:
            return f"[{'─' * width}] 0/0 (0%)"
        
        percentage = min(100, (current / total) * 100)
        filled = int((current / total) * width)
        bar = '█' * filled + '░' * (width - filled)
        return f"[{bar}] {current}/{total} ({percentage:.1f}%)"

    while time.time() < deadline:
        poll_count += 1
        poll_start = time.time()
        stage_parts = []
        
        # Check for no-progress timeout first
        time_since_last_change = time.time() - last_change_time
        if time_since_last_change > no_progress_timeout:
            log_with_timestamp(f"🚨 NO PROGRESS TIMEOUT! No changes detected for {time_since_last_change:.1f}s (limit: {no_progress_timeout}s)", "ERROR")
            raise TimeoutError(f"Pipeline stalled - no progress for {time_since_last_change:.1f} seconds")
        
        log_with_timestamp(f"🔄 Poll #{poll_count} - Checking pipeline progress... (no-progress timer: {time_since_last_change:.1f}s/{no_progress_timeout}s)")

        # Aspects inserted? -------------------------------------------
        aspects_query_start = time.time()
        aspects = (
            sb_client.table("review_analysis_aspects")
            .select("aspect_pk, detail_text, category_pk")
            .eq("project_id", project_id)
            .limit(20)
            .execute()
            .data
        )
        aspects_query_time = time.time() - aspects_query_start
        
        current_aspects_count = len(aspects)
        
        # Count assigned aspects
        assigned_count = sum(1 for a in aspects if a["category_pk"] is not None)
        unassigned_count = current_aspects_count - assigned_count
        
        # Check for changes and update progress tracking
        changes_detected = False
        if current_aspects_count != last_aspects_count:
            log_with_timestamp(f"📊 Aspects count changed: {last_aspects_count} → {current_aspects_count} (query: {aspects_query_time:.2f}s)")
            last_aspects_count = current_aspects_count
            changes_detected = True
            
        if assigned_count != last_assigned_count:
            progress_bar = create_progress_bar(assigned_count, current_aspects_count)
            log_with_timestamp(f"🎯 Assignment progress: {last_assigned_count} → {assigned_count} assigned | {progress_bar}")
            last_assigned_count = assigned_count
            changes_detected = True
            
        # Always log current assignment status
        if current_aspects_count > 0:
            progress_bar = create_progress_bar(assigned_count, current_aspects_count)
            log_with_timestamp(f"📈 Current status: {progress_bar} | {assigned_count} assigned, {unassigned_count} unassigned")
        
        if aspects and not aspects_done:
            sample = [a["detail_text"][:50] + "..." if len(a["detail_text"]) > 50 else a["detail_text"] for a in aspects[:5]]
            log_with_timestamp(f"🎯 MILESTONE: Extracted aspects detected! Sample of {len(sample)}/{len(aspects)}: {sample}")
            aspects_done = True
            changes_detected = True

        # Categories categorised --------------------------------------
        categories_cat_query_start = time.time()
        categories_cat = (
            sb_client.table("review_analysis_aspect_categories")
            .select("name, stage")
            .eq("project_id", project_id)
            .eq("stage", "categorisation")
            .limit(20)
            .execute()
            .data
        )
        categories_cat_query_time = time.time() - categories_cat_query_start
        
        if categories_cat and not cat_categorised:
            names = [c["name"] for c in categories_cat[:5]]
            log_with_timestamp(f"🏷️ MILESTONE: Categorised categories detected! Count: {len(categories_cat)}, Sample: {names} (query: {categories_cat_query_time:.2f}s)")
            cat_categorised = True
            changes_detected = True

        # Final categories --------------------------------------------
        categories_final_query_start = time.time()
        categories_final = (
            sb_client.table("review_analysis_aspect_categories")
            .select("name")
            .eq("project_id", project_id)
            .eq("stage", "final")
            .limit(20)
            .execute()
            .data
        )
        categories_final_query_time = time.time() - categories_final_query_start
        
        current_final_categories_count = len(categories_final)
        if current_final_categories_count != last_categories_count:
            log_with_timestamp(f"📊 Final categories count changed: {last_categories_count} → {current_final_categories_count} (query: {categories_final_query_time:.2f}s)")
            last_categories_count = current_final_categories_count
            changes_detected = True
        
        if categories_final and not cat_final:
            names = [c["name"] for c in categories_final[:5]]
            log_with_timestamp(f"🎉 MILESTONE: Final consolidated categories detected! Count: {len(categories_final)}, Sample: {names}")
            cat_final = True
            changes_detected = True

        # Update no-progress timer if any changes were detected this poll
        if changes_detected:
            last_change_time = time.time()
            log_with_timestamp(f"✅ Progress detected - resetting no-progress timer")

        # All done? ----------------------------------------------------
        if aspects_done and cat_final:
            log_with_timestamp("🔍 Checking for unassigned aspects...")
            unassigned_check_start = time.time()
            unassigned = (
                sb_client.table("review_analysis_aspects")
                .select("aspect_pk")
                .eq("project_id", project_id)
                .is_("category_pk", "null")
                .limit(1)
                .execute()
                .data
            )
            unassigned_check_time = time.time() - unassigned_check_start
            
            if not unassigned:
                elapsed_time = time.time() - polling_start_time
                log_with_timestamp(f"🎯 PIPELINE COMPLETE! All aspects assigned to categories (unassigned check: {unassigned_check_time:.2f}s, total polling time: {elapsed_time:.2f}s)")
                break
            else:
                log_with_timestamp(f"⏳ Still have unassigned aspects, continuing to poll...")

        # progress message throttle
        elapsed_polling = time.time() - polling_start_time
        poll_time = time.time() - poll_start
        progress_status = f"aspects: {'✅' if aspects_done else '❌'}, final cats: {'✅' if cat_final else '❌'}"
        if current_aspects_count > 0:
            assignment_pct = (assigned_count / current_aspects_count * 100) if current_aspects_count > 0 else 0
            progress_status += f", assignment: {assignment_pct:.1f}%"
        
        report = f"Poll #{poll_count} | Elapsed: {elapsed_polling:.1f}s | {progress_status} | Poll time: {poll_time:.2f}s"
        
        if report != last_report:
            log_with_timestamp(report)
            last_report = report

        remaining_time = deadline - time.time()
        no_progress_remaining = no_progress_timeout - time_since_last_change
        log_with_timestamp(f"⏱️ Sleeping for {poll_interval}s... (remaining timeout: {remaining_time:.1f}s, no-progress timeout: {no_progress_remaining:.1f}s)")
        await asyncio.sleep(poll_interval)

    # Final validation and detailed results
    total_elapsed = time.time() - test_start_time
    polling_elapsed = time.time() - polling_start_time
    
    log_with_timestamp(f"📊 FINAL VALIDATION - Total test time: {total_elapsed:.2f}s, Polling time: {polling_elapsed:.2f}s")
    
    assert aspects_done, "No aspects persisted"
    assert cat_final, "No final categories persisted"
    
    # Get final counts for reporting
    final_aspects = sb_client.table("review_analysis_aspects").select("aspect_pk").eq("project_id", project_id).execute().data
    final_categories = sb_client.table("review_analysis_aspect_categories").select("category_pk").eq("project_id", project_id).eq("stage", "final").execute().data
    
    log_with_timestamp(f"✅ TEST PASSED! Final results: {len(final_aspects)} aspects, {len(final_categories)} final categories")

        # Clean up
    log_with_timestamp("🧹 Starting final cleanup...")
    cleanup_final_start = time.time()
    
    try:
        # Clean up test data
        aspects_deleted = sb_client.table("review_analysis_aspects").delete().eq("project_id", project_id).execute()
        categories_deleted = sb_client.table("review_analysis_aspect_categories").delete().eq("project_id", project_id).execute()
        
        # Verify cleanup
        remaining_aspects = sb_client.table("review_analysis_aspects").select("aspect_pk", count="exact").eq("project_id", project_id).execute()
        remaining_categories = sb_client.table("review_analysis_aspect_categories").select("category_pk", count="exact").eq("project_id", project_id).execute()
        
        aspects_remaining = remaining_aspects.count if hasattr(remaining_aspects, 'count') else len(remaining_aspects.data)
        categories_remaining = remaining_categories.count if hasattr(remaining_categories, 'count') else len(remaining_categories.data)
        
        if aspects_remaining > 0 or categories_remaining > 0:
            log_with_timestamp(f"🚨 CLEANUP FAILED! {aspects_remaining} aspects and {categories_remaining} categories remain", "ERROR")
            raise AssertionError(f"Final cleanup failed: {aspects_remaining} aspects and {categories_remaining} categories remain")
        
        log_with_timestamp("✅ Final cleanup completed successfully - all test data removed")
    except Exception as e:
        log_with_timestamp(f"❌ Final cleanup failed: {e}", "ERROR")
        raise
    
    cleanup_final_time = time.time() - cleanup_final_start
    final_total_time = time.time() - test_start_time
    
    log_with_timestamp(f"🎉 TEST COMPLETED SUCCESSFULLY! Cleanup: {cleanup_final_time:.2f}s, Total time: {final_total_time:.2f}s") 