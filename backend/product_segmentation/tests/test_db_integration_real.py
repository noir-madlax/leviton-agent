from pathlib import Path
from typing import Dict
import os
import importlib
import pytest
import json
import pprint
import textwrap
from datetime import datetime
# Reload modules that may have cached the old constants
# ---------------------------------------------------------------------------
# Absolute imports – project packaging rules enforce non-relative imports.
# ---------------------------------------------------------------------------

from core.database.connection import get_supabase_service_client
from product_segmentation.models import (
    SegmentationStatus,
    StartSegmentationRequest,
)
from product_segmentation.repositories.llm_interaction_repository import LLMInteractionRepository
from product_segmentation.repositories.product_segment_repository import ProductSegmentRepository
from product_segmentation.repositories.product_taxonomy_repository import ProductTaxonomyRepository
from product_segmentation.repositories.segmentation_run_repository import SegmentationRunRepository
from product_segmentation.storage.llm_storage import LLMStorageService

# Use the production LLM client that internally relies on the shared
# `safe_llm_call` helper (and therefore honours global rate limits).
from product_segmentation.llm.product_segmentation_client import (
    ProductSegmentationLLMClient,
)
# Get project root directory (parent of backend directory)
PROJECT_ROOT = Path(__file__).parent.parent
# Persistent log root for integration tests
TEST_LOG_ROOT = PROJECT_ROOT / "data" / "test_llm_logs"
TEST_LOG_ROOT.mkdir(parents=True, exist_ok=True)

TEST_PRODUCT_NUM = 40
PRODUCTS_PER_TAXONOMY_PROMPT = 10
TAXONOMIES_PER_CONSOLIDATION = 5
PRODUCTS_PER_REFINEMENT = 20

def _load_prompts() -> Dict[str, str]:
    """Load prompt templates required by *ProductSegmentationLLMClient*."""

    names = [
        ("extract_taxonomy", "extract_taxonomy_prompt_v0.txt"),
        ("consolidate_taxonomy", "consolidate_taxonomy_prompt_v0.txt"),
        ("refine_assignments", "refine_assignments_prompt_v0.txt"),
    ]
    base = Path("product_segmentation/prompts")  # Relative to backend directory
    result: Dict[str, str] = {}
    for key, fname in names:
        fpath = base / fname
        if fpath.exists():
            result[key] = fpath.read_text(encoding="utf-8")
        else:
            result[key] = ""  # Fallback – client will still function
    return result


@pytest.mark.asyncio()
async def test_segmentation_service_against_real_db(monkeypatch) -> None:  # noqa: D401 – integration test
    """Run the segmentation service against the *real* Supabase database.

    Preconditions:
    1. Service environment variables (``SUPABASE_URL`` & ``SUPABASE_SERVICE_KEY``)
       must be set – the *service* key **must** grant insert/update privileges
       on all segmentation tables.
    2. The ``amazon_products`` table must contain at least three rows.

    The test:  ⤵
        • Fetch 3 product IDs from ``amazon_products``.
        • Create & execute a segmentation run using the real repository layer.
        • Assert that database rows are inserted & the run completes.
        • Clean up inserted rows so that the database remains tidy.
    """

    # ------------------------------------------------------------------
    # 1️⃣  Connect to Supabase using the *service* key (read/write access).
    # ------------------------------------------------------------------
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_service_key = os.getenv("SUPABASE_SERVICE_KEY")
    if not supabase_url or not supabase_service_key:
        pytest.skip("Supabase credentials not configured – skipping integration test")

    supabase_client = get_supabase_service_client()

    # ------------------------------------------------------------------
    # 🔧  Override segmentation batch-size constants so the test runs fast
    #     regardless of what the global defaults are.  We patch the module
    #     *before* any service/LLM client is instantiated so every import
    #     path sees the updated values.
    # ------------------------------------------------------------------
    from product_segmentation import config as seg_cfg  # local import

    monkeypatch.setattr(seg_cfg, "PRODUCTS_PER_TAXONOMY_PROMPT", PRODUCTS_PER_TAXONOMY_PROMPT, raising=False)
    monkeypatch.setattr(seg_cfg, "TAXONOMIES_PER_CONSOLIDATION", TAXONOMIES_PER_CONSOLIDATION, raising=False)
    monkeypatch.setattr(seg_cfg, "PRODUCTS_PER_REFINEMENT", PRODUCTS_PER_REFINEMENT, raising=False)

    
    import product_segmentation.llm.product_segmentation_client as _ps_client
    import product_segmentation.services.db_product_segmentation as _ps_service

    importlib.reload(_ps_client)
    importlib.reload(_ps_service)

    # Fetch three product IDs – skip test if table empty (CI safety net).
    product_query = (
        supabase_client.table("amazon_products").select("id").limit(TEST_PRODUCT_NUM).execute()
    )
    product_ids = [row["id"] for row in product_query.data]
    print(f"Found {len(product_ids)} products: {', '.join(str(id) for id in product_ids[:10])}, ...")


    # ------------------------------------------------------------------
    # 2️⃣  Instantiate service with *real* repositories and real LLM.
    # ------------------------------------------------------------------
    run_repo = SegmentationRunRepository(supabase_client)
    segment_repo = ProductSegmentRepository(supabase_client)
    taxonomy_repo = ProductTaxonomyRepository(supabase_client)
    interaction_repo = LLMInteractionRepository(supabase_client)

    log_dir = TEST_LOG_ROOT / f"run_{datetime.utcnow().strftime('%Y%m%dT%H%M%S')}"
    log_dir.mkdir(parents=True, exist_ok=True)

    storage = LLMStorageService.create_local(str(log_dir))

    # Initialize LLM client with real prompts
    prompts = _load_prompts()
    if not prompts.get("extract_taxonomy"):
        pytest.skip("Prompt templates not found – skipping integration test")

    segmentation_llm_client = ProductSegmentationLLMClient(
        llm_client=None,
        prompts=prompts,
        max_retries=2,
        cache=None,
        interaction_repo=interaction_repo,
        storage_service=storage,
    )

    # Re-import the (now reloaded) service class
    from product_segmentation.services.db_product_segmentation import DatabaseProductSegmentationService

    service = DatabaseProductSegmentationService(
        run_repo,
        segment_repo,
        storage,
        segmentation_llm_client,
        taxonomy_repo=taxonomy_repo,
        interaction_repo=interaction_repo,
    )

    # --------------------------------------------------------------
    # 3⃣️  CREATE RUN without executing – we need the generated run_id
    # to insert a taxonomy row so that ``taxonomy_id`` exists before
    # segments are written (FK constraint).
    # --------------------------------------------------------------
    request = StartSegmentationRequest(product_ids=product_ids, category="Light Switch")
    run_id = await service.create_run(request)

    # --------------------------------------------------------------
    # 4⃣️  EXECUTE the run now that FK prerequisites are in place.
    # --------------------------------------------------------------
    await service.execute_run(run_id)

    # --------------------------------------------------------------
    # 5⃣️  VERIFY that the run completed successfully **and** capture
    #     intermediate artefacts for debugging / future assertions.
    # --------------------------------------------------------------
    run = await run_repo.get_by_id(run_id)
    assert run is not None
    assert run.status == SegmentationStatus.COMPLETED

    # Pull intermediate data ------------------------------------------------
    segments = await segment_repo.get_segments_by_run(run_id)
    refined_segments = await segment_repo.get_refined_segments_by_run(run_id)
    taxonomies = await taxonomy_repo.get_taxonomies_by_run(run_id)
    interactions = await interaction_repo.get_by_run(run_id)

    # Debug logging – helps when running the test manually ---------------
    def _pretty(obj):  # local helper for compact JSON formatting
        try:
            return json.dumps(obj, indent=2, default=str)[:1000]
        except Exception:  # pragma: no cover – fallback
            return pprint.pformat(obj)[:1000]

    print("\n========== DB ARTIFACTS (truncated to 1 000 chars each) ==========")
    print("Run:", run.model_dump() if hasattr(run, "model_dump") else run)
    print("\n-- Taxonomies (", len(taxonomies), ") --")
    for idx, t in enumerate(taxonomies, 1):
        print(f"[# {idx}]", _pretty(t))

    print("\n-- Segments (", len(segments), ") --")
    for idx, s in enumerate(segments, 1):
        if idx > 20:  # avoid flooding
            print("… truncated …")
            break
        print(f"[# {idx}]", _pretty(s))

    print("\n-- Refined Segments (", len(refined_segments), ") --")
    for idx, s in enumerate(refined_segments, 1):
        if idx > 20:
            print("… truncated …")
            break
        print(f"[# {idx}]", _pretty(s))

    print("\n-- Interaction index rows (", len(interactions), ") --")
    for idx, row in enumerate(interactions, 1):
        print(f"[# {idx}]", _pretty(row))

    # The local storage backend writes interaction logs to *temp_dir*.
    stored_files = [p for p in Path(log_dir).rglob("*.json")]
    print(f"\n========== JSON FILES ( {len(stored_files)} ) under {log_dir} ==========")
    for fpath in stored_files:
        print(f"\n--- {fpath.name} ---")
        try:
            content = textwrap.indent(fpath.read_text(encoding='utf-8')[:2000], prefix="    ")
            print(content)
            if len(content) >= 2000:
                print("    … truncated …")
        except Exception as exc:
            print("    <error reading file>", exc)
    print("\n===============================================================\n")

    # Basic sanity assertions ------------------------------------------------
    assert len(taxonomies) > 0, "No taxonomies persisted"
    assert len(segments) > 0, "No product_segments persisted"
    assert len(interactions) > 0, "No interaction index rows persisted"
    assert len(stored_files) > 0, "No JSON interaction logs written to disk"

    # --------------------------------------------------------------
    # 6⃣️  CLEAN UP by deleting the run and its related data.
    # --------------------------------------------------------------
    await run_repo.delete(run_id) 