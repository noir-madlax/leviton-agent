import os
import sys
import pytest
import time
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Configure logging with timestamps
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Enable detailed logging for LLM calls
llm_logger = logging.getLogger('core.utils.llm_utils')
llm_logger.setLevel(logging.INFO)

# Enable detailed logging for review analysis service
service_logger = logging.getLogger('review_analysis.services.db_review_analysis')
service_logger.setLevel(logging.INFO)

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
from dataclasses import asdict

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




def cleanup_test_data(sb_client, project_id: str, fail_on_existing: bool = False) -> bool:
    """
    Comprehensive cleanup of test data from review analysis tables.
    
    Args:
        sb_client: Supabase client
        project_id: Project ID to clean up
        fail_on_existing: If True, raise error when existing data found
        
    Returns:
        bool: True if cleanup was needed and performed, False if already clean
    """
    log_with_timestamp(f"🧹 Starting cleanup for project_id: {project_id}")
    
    try:
        # Step 1: Check what exists
        log_with_timestamp("🔍 Checking for existing data...")
        
        # Check projects table
        projects_count = sb_client.table("projects").select("id", count="exact").eq("id", project_id).execute()
        projects_total = projects_count.count if hasattr(projects_count, 'count') else len(projects_count.data)
        
        # Check review_analysis_runs
        runs_count = sb_client.table("review_analysis_runs").select("id", count="exact").eq("project_id", project_id).execute()
        runs_total = runs_count.count if hasattr(runs_count, 'count') else len(runs_count.data)
        
        # Check review_analysis_progress
        progress_total = 0
        if runs_total > 0:
            progress_count = sb_client.table("review_analysis_progress").select("id", count="exact").eq("run_id", runs_total).execute()
            progress_total = progress_count.count if hasattr(progress_count, 'count') else len(progress_count.data)
        
        aspects_count = sb_client.table("review_analysis_aspects").select("aspect_pk", count="exact").eq("project_id", project_id).execute()
        aspects_total = aspects_count.count if hasattr(aspects_count, 'count') else len(aspects_count.data)
        
        categories_count = sb_client.table("review_analysis_aspect_categories").select("category_pk", count="exact").eq("project_id", project_id).execute()
        categories_total = categories_count.count if hasattr(categories_count, 'count') else len(categories_count.data)
        
        log_with_timestamp(f"📊 Found {projects_total} projects, {runs_total} runs, {progress_total} progress records, {aspects_total} aspects and {categories_total} categories")
        
        if projects_total == 0 and runs_total == 0 and aspects_total == 0 and categories_total == 0:
            log_with_timestamp("✅ Database is already clean - no cleanup needed")
            return False
        
        if fail_on_existing:
            raise AssertionError(f"Test environment is dirty: {projects_total} projects, {runs_total} runs, {aspects_total} aspects and {categories_total} categories exist. Database must be clean before running test.")
        
        # Step 2: Clean up review_analysis_progress first (foreign key dependency)
        if progress_total > 0 and runs_total > 0:
            log_with_timestamp("🗑️ Cleaning up review_analysis_progress...")
            try:
                # Get the actual run ID
                run_result = sb_client.table("review_analysis_runs").select("id").eq("project_id", project_id).execute()
                if run_result.data:
                    run_id = run_result.data[0]["id"]
                    result = sb_client.table("review_analysis_progress").delete().eq("run_id", run_id).execute()
                    deleted_count = len(result.data) if result.data else progress_total
                    log_with_timestamp(f"✅ Deleted {deleted_count} progress records")
            except Exception as e:
                log_with_timestamp(f"❌ Failed to delete progress records: {e}", "ERROR")
                raise
        
        # Step 3: Get aspect PKs for occurrence cleanup
        if aspects_total > 0:
            log_with_timestamp("🔍 Getting aspect PKs for occurrence cleanup...")
            all_aspects = []
            offset = 0
            batch_size = 1000
            
            while True:
                batch = sb_client.table("review_analysis_aspects").select("aspect_pk").eq("project_id", project_id).range(offset, offset + batch_size - 1).execute().data
                if not batch:
                    break
                all_aspects.extend(batch)
                offset += batch_size
                if len(all_aspects) % 1000 == 0:
                    log_with_timestamp(f"  📦 Loaded {len(all_aspects)} aspect PKs so far...")
            
            aspect_pks = [a["aspect_pk"] for a in all_aspects]
            log_with_timestamp(f"✅ Found {len(aspect_pks)} aspect PKs")
            
            # Step 4: Clean up aspect occurrences first (foreign key dependency)
            if aspect_pks:
                log_with_timestamp("🗑️ Cleaning up aspect occurrences...")
                # Clean in batches to avoid query size limits
                batch_size = 100
                total_deleted = 0
                
                for i in range(0, len(aspect_pks), batch_size):
                    batch_pks = aspect_pks[i:i + batch_size]
                    try:
                        result = sb_client.table("review_analysis_aspect_occurrences").delete().in_("aspect_pk", batch_pks).execute()
                        batch_deleted = len(result.data) if result.data else 0
                        total_deleted += batch_deleted
                        if batch_deleted > 0:
                            log_with_timestamp(f"  ✅ Batch {i//batch_size + 1}: Deleted {batch_deleted} occurrences")
                    except Exception as e:
                        log_with_timestamp(f"  ⚠️ Batch {i//batch_size + 1} failed: {e}", "WARNING")
                
                log_with_timestamp(f"✅ Deleted {total_deleted} aspect occurrences total")
        
        # Step 5: Delete aspects
        if aspects_total > 0:
            log_with_timestamp(f"🗑️ Deleting {aspects_total} aspects...")
            try:
                result = sb_client.table("review_analysis_aspects").delete().eq("project_id", project_id).execute()
                deleted_count = len(result.data) if result.data else aspects_total
                log_with_timestamp(f"✅ Deleted {deleted_count} aspects")
            except Exception as e:
                log_with_timestamp(f"❌ Failed to delete aspects: {e}", "ERROR")
                raise
        
        # Step 6: Delete categories  
        if categories_total > 0:
            log_with_timestamp(f"🗑️ Deleting {categories_total} categories...")
            try:
                result = sb_client.table("review_analysis_aspect_categories").delete().eq("project_id", project_id).execute()
                deleted_count = len(result.data) if result.data else categories_total
                log_with_timestamp(f"✅ Deleted {deleted_count} categories")
            except Exception as e:
                log_with_timestamp(f"❌ Failed to delete categories: {e}", "ERROR")
                raise
        
        # Step 7: Delete review_analysis_runs
        if runs_total > 0:
            log_with_timestamp(f"🗑️ Deleting {runs_total} review_analysis_runs...")
            try:
                result = sb_client.table("review_analysis_runs").delete().eq("project_id", project_id).execute()
                deleted_count = len(result.data) if result.data else runs_total
                log_with_timestamp(f"✅ Deleted {deleted_count} review_analysis_runs")
            except Exception as e:
                log_with_timestamp(f"❌ Failed to delete review_analysis_runs: {e}", "ERROR")
                raise
        
        # Step 8: Delete project record
        if projects_total > 0:
            log_with_timestamp(f"🗑️ Deleting {projects_total} project record...")
            try:
                result = sb_client.table("projects").delete().eq("id", project_id).execute()
                deleted_count = len(result.data) if result.data else projects_total
                log_with_timestamp(f"✅ Deleted {deleted_count} project record")
            except Exception as e:
                log_with_timestamp(f"❌ Failed to delete project record: {e}", "ERROR")
                raise
        
        # Step 9: Verify cleanup
        log_with_timestamp("🔍 Verifying cleanup...")
        
        remaining_projects = sb_client.table("projects").select("id", count="exact").eq("id", project_id).execute()
        remaining_runs = sb_client.table("review_analysis_runs").select("id", count="exact").eq("project_id", project_id).execute()
        remaining_aspects = sb_client.table("review_analysis_aspects").select("aspect_pk", count="exact").eq("project_id", project_id).execute()
        remaining_categories = sb_client.table("review_analysis_aspect_categories").select("category_pk", count="exact").eq("project_id", project_id).execute()
        
        projects_remaining = remaining_projects.count if hasattr(remaining_projects, 'count') else len(remaining_projects.data)
        runs_remaining = remaining_runs.count if hasattr(remaining_runs, 'count') else len(remaining_runs.data)
        aspects_remaining = remaining_aspects.count if hasattr(remaining_aspects, 'count') else len(remaining_aspects.data)
        categories_remaining = remaining_categories.count if hasattr(remaining_categories, 'count') else len(remaining_categories.data)
        
        if projects_remaining > 0 or runs_remaining > 0 or aspects_remaining > 0 or categories_remaining > 0:
            error_msg = f"Cleanup incomplete: {projects_remaining} projects, {runs_remaining} runs, {aspects_remaining} aspects and {categories_remaining} categories remain"
            log_with_timestamp(f"❌ {error_msg}", "ERROR")
            raise AssertionError(error_msg)
        
        log_with_timestamp("✅ Cleanup completed successfully!")
        return True
        
    except Exception as e:
        log_with_timestamp(f"❌ Cleanup failed: {e}", "ERROR")
        import traceback
        traceback.print_exc()
        raise


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

    # project and product list - using 3 products with max 30 reviews each from category_l5_id=507840 (Dimmer Switches)
    project_id = str(uuid.uuid4())  # Generate proper UUID for projects table
    product_category = "Dimmer Switches"
    product_ids = ["B00MXCRAX8", "B0055VD9HK", "B09WL82DB2"]
    
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

    # --- Clean up any existing test data at the beginning ---------------
    print("🧹 Starting initial cleanup check...", flush=True)
    cleanup_start_time = time.time()
    log_with_timestamp(f"🧹 Starting initial cleanup check for project_id: {project_id}")
    
    try:
        cleanup_needed = cleanup_test_data(sb_client, project_id, fail_on_existing=False)
        if cleanup_needed:
            log_with_timestamp("✅ Initial cleanup completed - database is now clean")
        else:
            log_with_timestamp("✅ Database was already clean")
        
        cleanup_time = time.time() - cleanup_start_time
        log_with_timestamp(f"✅ Initial cleanup check completed in {cleanup_time:.2f}s")
        
    except Exception as e:
        cleanup_time = time.time() - cleanup_start_time
        print(f"❌ Initial cleanup failed: {e} (took {cleanup_time:.2f}s)", flush=True)
        log_with_timestamp(f"❌ Initial cleanup failed: {e} (took {cleanup_time:.2f}s)", "ERROR")
        raise

    # --- Create project record like project_service.py does --------------
    print("📝 Creating project record...", flush=True)
    log_with_timestamp("📝 Creating project record in projects table...")
    
    try:
        # Calculate estimates like project_service.py does
        total_reviews = (
            sb_client.table("product_reviews")
            .select("review_id", count="exact")
            .in_("product_id", product_ids)
            .execute()
        )
        estimated_reviews_to_analyze = total_reviews.count if hasattr(total_reviews, 'count') else len(total_reviews.data)
        
        # Estimate LLM calls (simplified calculation)
        estimated_llm_calls = (estimated_reviews_to_analyze + 9) // 10  # Rough estimate: 10 reviews per LLM call
        
        project_data = {
            "id": project_id,
            "project_name": "Integration Test Project",
            "company_name": "Test Company",
            "user_name": "Test User",
            "description": "Integration test project for review analysis pipeline",
            "selected_categories": [product_category],
            "selected_sources": ["amazon"],
            "selected_brands": [],
            "selected_product_asins": product_ids,
            "top_sales_count": 100,
            "total_products": len(product_ids),
            "total_brands": 1,
            "total_reviews": estimated_reviews_to_analyze,
            "avg_monthly_sales": 1000.0,
            "status": "active",
            "overall_status": "creating",
            "segmentation_status": "completed",  # Assume segmentation is done
            "review_analysis_status": "pending",
            "estimated_reviews_to_analyze": estimated_reviews_to_analyze,
            "estimated_llm_calls": estimated_llm_calls,
            "review_analysis_started_at": datetime.now(timezone.utc).isoformat()
        }
        
        # Insert project record
        project_result = sb_client.table("projects").upsert(project_data, on_conflict="id").execute()
        if not project_result.data:
            raise Exception("Failed to create project record")
        
        log_with_timestamp(f"✅ Project record created with {estimated_reviews_to_analyze} estimated reviews and {estimated_llm_calls} estimated LLM calls")
        
    except Exception as e:
        log_with_timestamp(f"❌ Failed to create project record: {e}", "ERROR")
        raise

    # --- call API --------------------------------------------------------
    print("🏗️ Setting up API call...", flush=True)
    log_with_timestamp("🏗️ Setting up direct service call instead of API...")

    req = ReviewAnalysisRequest(
        project_id=project_id,
        product_ids=product_ids,
        product_category=product_category,
    )
    print("📝 Request object created", flush=True)
    log_with_timestamp(f"📝 Request created: {asdict(req)}")

    # ------------------------------------------------------------------
    # Call the service directly instead of going through FastAPI
    # ------------------------------------------------------------------
    api_call_start = time.time()
    print("🌐 About to call review analysis service directly...", flush=True)
    log_with_timestamp("🌐 Calling review analysis service directly to avoid FastAPI lifespan issues...")
    
    try:
        # Import and call the service directly
        print("🔧 Importing DatabaseReviewAnalysisService...", flush=True)
        log_with_timestamp("🔧 Importing DatabaseReviewAnalysisService...")
        from review_analysis.services.db_review_analysis import DatabaseReviewAnalysisService
        print("✅ DatabaseReviewAnalysisService imported successfully", flush=True)
        log_with_timestamp("✅ DatabaseReviewAnalysisService imported successfully")
        
        # Create service instance
        print("🏗️ Creating DatabaseReviewAnalysisService instance...", flush=True)
        log_with_timestamp("🏗️ Creating DatabaseReviewAnalysisService instance...")
        service = DatabaseReviewAnalysisService()
        print("✅ DatabaseReviewAnalysisService instance created successfully", flush=True)
        log_with_timestamp("✅ DatabaseReviewAnalysisService instance created successfully")
        
        # Test the database query that the service will do first
        print("🔍 Testing database query that service will perform...", flush=True)
        log_with_timestamp("🔍 Testing database query that service will perform...")
        test_reviews = (
            sb_client.table("product_reviews")
            .select("product_id, review_id, review_title, review_text, rating")
            .in_("product_id", product_ids)
            .execute()
            .data
            or []
        )
        print(f"✅ Database query test completed - found {len(test_reviews)} reviews", flush=True)
        log_with_timestamp(f"✅ Database query test completed - found {len(test_reviews)} reviews")
        
        # Start the analysis using the request object
        print("🚀 Starting service.analyse() call...", flush=True)
        log_with_timestamp("🚀 Starting service.analyse() call...")
        
        # Add a progress callback to track what the service is doing
        async def debug_progress_callback(progress_data):
            step = progress_data.get("step", "unknown")
            status = progress_data.get("status", "unknown")
            details = progress_data.get("details", {})
            print(f"📊 Service progress: {step} - {status} | {details}", flush=True)
            log_with_timestamp(f"📊 Service progress: {step} - {status} | {details}")
        
        # Add a timeout wrapper to the service call
        import asyncio
        try:
            analysis_id = await asyncio.wait_for(
                service.analyse(req, progress_callback=debug_progress_callback), 
                timeout=300.0
            )  # 5 minute timeout for LLM calls
            print("✅ service.analyse() completed successfully", flush=True)
            log_with_timestamp("✅ service.analyse() completed successfully")
        except asyncio.TimeoutError:
            print("⏰ service.analyse() timed out after 5 minutes", flush=True)
            log_with_timestamp("⏰ service.analyse() timed out after 5 minutes", "ERROR")
            raise TimeoutError("service.analyse() call timed out after 5 minutes")
        
        api_call_time = time.time() - api_call_start
        log_with_timestamp(f"📡 Service call completed in {api_call_time:.2f}s with analysis_id: {analysis_id}")
        
        assert analysis_id, "analysis_id missing in response"
        log_with_timestamp(f"✅ Pipeline started successfully with analysis_id: {analysis_id}")
        
    except Exception as e:
        api_call_time = time.time() - api_call_start
        log_with_timestamp(f"❌ Service call failed after {api_call_time:.2f}s: {e}", "ERROR")
        import traceback
        log_with_timestamp(f"❌ Stack trace: {traceback.format_exc()}", "ERROR")
        raise

    # ------------------------------------------------------------------
    # Poll DB for progress & print small samples, similar to segmentation
    # ------------------------------------------------------------------
    timeout_s = 900  # 15 min timeout for the 3-stage workflow (extraction, categorization, consolidation)
    poll_interval = 10
    no_progress_timeout = 480  # 8 minutes - fail if no progress
    deadline = time.time() + timeout_s
    polling_start_time = time.time()
    last_change_time = time.time()
    
    log_with_timestamp(f"⏰ Starting progress polling with {timeout_s}s timeout and {poll_interval}s intervals")
    log_with_timestamp(f"🚨 No-progress timeout: {no_progress_timeout}s (will fail if no changes detected)")

    # Track all stages
    extraction_done = False
    categorization_done = False
    consolidation_done = False

    last_report = ""
    poll_count = 0
    last_aspects_count = 0
    last_categories_count = 0
    last_assigned_count = 0
    last_run_stage = "starting"

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

        # Check review_analysis_runs table for current stage
        runs_query_start = time.time()
        runs = (
            sb_client.table("review_analysis_runs")
            .select("id, status, stage, extraction_batches_done, extraction_batches_total, categorization_batches_done, categorization_batches_total, consolidation_batches_done, consolidation_batches_total")
            .eq("project_id", project_id)
            .execute()
            .data
        )
        runs_query_time = time.time() - runs_query_start
        
        current_run = runs[0] if runs else None
        current_run_stage = current_run.get("stage", "starting") if current_run else "starting"
        
        if current_run_stage != last_run_stage:
            log_with_timestamp(f"📊 Run stage changed: {last_run_stage} → {current_run_stage} (query: {runs_query_time:.2f}s)")
            last_run_stage = current_run_stage
            changes_detected = True

        # Check review_analysis_progress table for detailed progress
        progress_query_start = time.time()
        progress = []
        if current_run:
            progress = (
                sb_client.table("review_analysis_progress")
                .select("step_name, status, progress_current, progress_total, details")
                .eq("run_id", current_run["id"])
                .execute()
                .data
            )
        progress_query_time = time.time() - progress_query_start
        
        # Create progress map
        progress_map = {p['step_name']: p for p in progress}
        
        # Check each stage progress
        for stage_name in ["extraction", "categorization", "consolidation"]:
            stage_progress = progress_map.get(stage_name, {})
            stage_status = stage_progress.get("status", "pending")
            stage_current = stage_progress.get("progress_current", 0)
            stage_total = stage_progress.get("progress_total", 0)
            
            if stage_status == "completed":
                if stage_name == "extraction" and not extraction_done:
                    log_with_timestamp(f"🎉 MILESTONE: {stage_name.capitalize()} stage completed!")
                    extraction_done = True
                    changes_detected = True
                elif stage_name == "categorization" and not categorization_done:
                    log_with_timestamp(f"🎉 MILESTONE: {stage_name.capitalize()} stage completed!")
                    categorization_done = True
                    changes_detected = True
                elif stage_name == "consolidation" and not consolidation_done:
                    log_with_timestamp(f"🎉 MILESTONE: {stage_name.capitalize()} stage completed!")
                    consolidation_done = True
                    changes_detected = True
            elif stage_status == "in_progress":
                progress_bar = create_progress_bar(stage_current, stage_total)
                log_with_timestamp(f"📈 {stage_name.capitalize()} progress: {progress_bar}")

        # Aspects inserted? -------------------------------------------
        aspects_query_start = time.time()
        aspects = (
            sb_client.table("review_analysis_aspects")
            .select("aspect_pk, detail_text, category_pk")
            .eq("project_id", project_id)
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
        
        if aspects and not extraction_done:
            sample = [a["detail_text"][:50] + "..." if len(a["detail_text"]) > 50 else a["detail_text"] for a in aspects[:5]]
            log_with_timestamp(f"🎯 MILESTONE: Extracted aspects detected! Total: {len(aspects)}, Sample of first 5: {sample}")
            extraction_done = True
            changes_detected = True

        # Categories categorised --------------------------------------
        categories_cat_query_start = time.time()
        categories_cat = (
            sb_client.table("review_analysis_aspect_categories")
            .select("name, stage")
            .eq("project_id", project_id)
            .eq("stage", "categorisation")
            .execute()
            .data
        )
        categories_cat_query_time = time.time() - categories_cat_query_start
        
        if categories_cat and not categorization_done:
            names = [c["name"] for c in categories_cat[:5]]
            log_with_timestamp(f"🏷️ MILESTONE: Categorised categories detected! Total: {len(categories_cat)}, Sample of first 5: {names} (query: {categories_cat_query_time:.2f}s)")
            categorization_done = True
            changes_detected = True

        # Final categories --------------------------------------------
        categories_final_query_start = time.time()
        categories_final = (
            sb_client.table("review_analysis_aspect_categories")
            .select("name")
            .eq("project_id", project_id)
            .eq("stage", "final")
            .execute()
            .data
        )
        categories_final_query_time = time.time() - categories_final_query_start
        
        current_final_categories_count = len(categories_final)
        if current_final_categories_count != last_categories_count:
            log_with_timestamp(f"📊 Final categories count changed: {last_categories_count} → {current_final_categories_count} (query: {categories_final_query_time:.2f}s)")
            last_categories_count = current_final_categories_count
            changes_detected = True
        
        if categories_final and not consolidation_done:
            names = [c["name"] for c in categories_final[:5]]
            log_with_timestamp(f"🎉 MILESTONE: Final consolidated categories detected! Total: {len(categories_final)}, Sample of first 5: {names}")
            consolidation_done = True
            changes_detected = True

        # Update no-progress timer if any changes were detected this poll
        if changes_detected:
            last_change_time = time.time()
            log_with_timestamp("✅ Progress detected - resetting no-progress timer")

        # All done? ----------------------------------------------------
        if extraction_done and consolidation_done:
            # Pipeline is complete when all 3 stages are done - aspects are assigned during categorization
            # and reassigned during consolidation, so no separate refinement needed
            elapsed_time = time.time() - polling_start_time
            log_with_timestamp(f"🎯 PIPELINE COMPLETE! All 3 stages completed (total polling time: {elapsed_time:.2f}s)")
            break

        # Check for any remaining unassigned aspects for monitoring (but don't block completion)
        if extraction_done and categorization_done:
            log_with_timestamp("🔍 Checking for unassigned aspects (for monitoring only)...")
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
            
            if unassigned:
                log_with_timestamp(f"⏳ Still have unassigned aspects (check: {unassigned_check_time:.2f}s), waiting for consolidation...")
            else:
                log_with_timestamp(f"✅ All aspects are assigned (check: {unassigned_check_time:.2f}s), waiting for consolidation...")

        # progress message throttle
        elapsed_polling = time.time() - polling_start_time
        poll_time = time.time() - poll_start
        progress_status = f"extraction: {'✅' if extraction_done else '❌'}, categorization: {'✅' if categorization_done else '❌'}, consolidation: {'✅' if consolidation_done else '❌'}"
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
    
    assert extraction_done, "No aspects persisted"
    assert categorization_done, "No categorization completed"
    assert consolidation_done, "No final categories persisted"
    
    # Get final counts for reporting
    final_aspects = sb_client.table("review_analysis_aspects").select("aspect_pk").eq("project_id", project_id).execute().data
    final_categories = sb_client.table("review_analysis_aspect_categories").select("category_pk").eq("project_id", project_id).eq("stage", "final").execute().data
    final_runs = sb_client.table("review_analysis_runs").select("id").eq("project_id", project_id).execute().data
    final_progress = []
    if final_runs:
        final_progress = sb_client.table("review_analysis_progress").select("id").eq("run_id", final_runs[0]["id"]).execute().data
    
    log_with_timestamp(f"✅ TEST PASSED! Final results: {len(final_aspects)} aspects, {len(final_categories)} final categories, {len(final_runs)} runs, {len(final_progress)} progress records")

    # --- Final cleanup using comprehensive cleanup function -------------
    log_with_timestamp("🧹 Starting final cleanup...")
    cleanup_final_start = time.time()
    
    try:
        cleanup_test_data(sb_client, project_id, fail_on_existing=False)
        cleanup_final_time = time.time() - cleanup_final_start
        log_with_timestamp(f"✅ Final cleanup completed successfully in {cleanup_final_time:.2f}s - all test data removed")
    except Exception as e:
        cleanup_final_time = time.time() - cleanup_final_start
        log_with_timestamp(f"❌ Final cleanup failed: {e} (took {cleanup_final_time:.2f}s)", "ERROR")
        raise
    
    final_total_time = time.time() - test_start_time
    log_with_timestamp(f"🎉 TEST COMPLETED SUCCESSFULLY! Total time: {final_total_time:.2f}s") 