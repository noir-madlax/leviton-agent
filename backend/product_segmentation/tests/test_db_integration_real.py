from contextlib import suppress
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import List, Dict
import os
import json

import pytest

# ---------------------------------------------------------------------------
# Absolute imports – project packaging rules enforce non-relative imports.
# ---------------------------------------------------------------------------

from backend.core.database.connection import get_supabase_service_client
from backend.product_segmentation.models import (
    SegmentationStatus,
    StartSegmentationRequest,
)
from backend.product_segmentation.repositories.llm_interaction_repository import LLMInteractionRepository
from backend.product_segmentation.repositories.product_segment_repository import ProductSegmentRepository
from backend.product_segmentation.repositories.product_taxonomy_repository import ProductTaxonomyRepository
from backend.product_segmentation.repositories.segmentation_run_repository import SegmentationRunRepository
from backend.product_segmentation.services.db_product_segmentation import DatabaseProductSegmentationService
from backend.product_segmentation.storage.llm_storage import LLMStorageService

# Use the production LLM client that internally relies on the shared
# `safe_llm_call` helper (and therefore honours global rate limits).
from backend.product_segmentation.llm.product_segmentation_client import (
    ProductSegmentationLLMClient,
)


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
async def test_segmentation_service_against_real_db() -> None:  # noqa: D401 – integration test
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

    # Fetch three product IDs – skip test if table empty (CI safety net).
    product_query = (
        supabase_client.table("amazon_products").select("id").limit(3).execute()
    )
    if not product_query.data:
        # Fallback to hard-coded demo IDs that exist in the seed dataset.
        product_ids = [4, 5, 6]
    else:
        product_ids = [row["id"] for row in product_query.data]

    assert len(product_ids) >= 3, "Need at least 3 products for the test"

    # ------------------------------------------------------------------
    # 2️⃣  Instantiate service with *real* repositories and real LLM.
    # ------------------------------------------------------------------
    run_repo = SegmentationRunRepository(supabase_client)
    segment_repo = ProductSegmentRepository(supabase_client)
    taxonomy_repo = ProductTaxonomyRepository(supabase_client)
    interaction_repo = LLMInteractionRepository(supabase_client)

    with TemporaryDirectory(prefix="ps_int_test_logs_") as temp_dir:
        storage = LLMStorageService.create_local(temp_dir)

        # Initialize LLM client with real prompts
        prompts = _load_prompts()
        if not prompts.get("extract_taxonomy"):
            pytest.skip("Prompt templates not found – skipping integration test")

        llm_client = ProductSegmentationLLMClient(
            llm_client=None,  # Delegated to safe_llm_call inside the client
            prompts=prompts,
            max_retries=2,
            cache=None,
            interaction_repo=interaction_repo,
            storage_service=storage,
        )

        service = DatabaseProductSegmentationService(
            run_repo,
            segment_repo,
            storage,
            llm_client,
            taxonomy_repo=taxonomy_repo,
            interaction_repo=interaction_repo,
        )

        # --------------------------------------------------------------
        # 3⃣️  CREATE RUN without executing – we need the generated run_id
        # to insert a taxonomy row so that ``taxonomy_id`` exists before
        # segments are written (FK constraint).
        # --------------------------------------------------------------
        request = StartSegmentationRequest(product_ids=product_ids, category="Testing")
        run_id = await service.create_run(request)

        # --------------------------------------------------------------
        # 4⃣️  EXECUTE the run now that FK prerequisites are in place.
        # --------------------------------------------------------------
        await service.execute_run(run_id)

        # --------------------------------------------------------------
        # 5⃣️  VERIFY that the run completed successfully.
        # --------------------------------------------------------------
        run = await run_repo.get_by_id(run_id)
        assert run is not None
        assert run.status == "completed"

        # --------------------------------------------------------------
        # 6⃣️  CLEAN UP by deleting the run and its related data.
        # --------------------------------------------------------------
        await run_repo.delete(run_id) 