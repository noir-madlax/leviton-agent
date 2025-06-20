"""Tests that the LLM client retrieves cached responses via the database/\
storage hybrid layer (Phase 3.1 feature)."""

from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncio
import pytest

from product_segmentation.llm.product_segmentation_client import (
    ProductSegmentationLLMClient,
)
from product_segmentation.models import InteractionType, LLMInteractionIndex
from product_segmentation.utils.cache import create_llm_cache
from product_segmentation.tests.stubs import StubLLM
from utils import config as cfg


class _StubInteractionRepo:
    """Stub interaction repository that returns deterministic responses."""

    def __init__(self, index_row: Optional[LLMInteractionIndex] = None):
        self._index_row = index_row

    async def get_by_cache_key(self, cache_key: str) -> Optional[LLMInteractionIndex]:
        """Return deterministic index row."""
        return self._index_row


class _StubStorage:
    """Stub storage service that returns deterministic responses."""

    def __init__(self, interaction_record: Dict[str, Any]):
        self._interaction_record = interaction_record

    async def load_interaction(self, file_path: str) -> Dict[str, Any]:
        """Return deterministic interaction record."""
        return self._interaction_record


@pytest.mark.asyncio
async def test_db_index_cache_roundtrip(tmp_path):
    """LLM client should return existing response without calling the model."""

    # ------------------------------------------------------------------
    # Prepare deterministic cache key based on prompt
    # ------------------------------------------------------------------
    llm_cache = create_llm_cache(tmp_path)
    prompt = "Extract taxonomy for Electronics"
    cache_ctx = {"model": cfg.LLM_MODEL_NAME, "temperature": cfg.LLM_TEMPERATURE}
    cache_key = llm_cache.generate_key(prompt, cache_ctx)

    # The *response* we expect back from the client (service format)
    expected_response = {
        "segments": [{"product_id": 1, "taxonomy_id": 1}],
        "taxonomies": [
            {
                "category_name": "Category A",
                "definition": "demo",
                "product_count": 1,
            }
        ],
        "cache_key": cache_key,
    }

    # Interaction file record that would be stored on disk
    interaction_record = {
        "run_id": "RUN_TEST",
        "interaction_type": InteractionType.SEGMENTATION.value,
        "batch_id": 0,
        "attempt": 1,
        "timestamp": datetime.utcnow().isoformat(),
        "request": {},
        "response": expected_response,
        "metadata": {"cache_key": cache_key},
    }

    # Row in *llm_interaction_index* table
    index_row = LLMInteractionIndex(
        id=1,
        run_id="RUN_TEST",
        interaction_type=InteractionType.SEGMENTATION,
        batch_id=0,
        attempt=1,
        file_path="RUN_TEST/interactions/seg_batch.json",
        cache_key=cache_key,
        created_at=datetime.utcnow(),
    )

    # Stub collaborators
    interaction_repo = _StubInteractionRepo(index_row)
    storage = _StubStorage(interaction_record)

    # LLM client with *no* file-cache entry but DB+storage integration
    client = ProductSegmentationLLMClient(
        llm_client=StubLLM(),  # Use stub LLM to avoid real API calls
        prompts={"extract_taxonomy": prompt},
        max_retries=1,
        cache=llm_cache,  # just used for key generation
        interaction_repo=interaction_repo,
        storage_service=storage,
    )

    products = [1]

    # The call should return the *cached* response instantly
    result = await client.segment_products(products, category="Electronics")
    assert result == expected_response 