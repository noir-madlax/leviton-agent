"""Product-segment LLM interaction repository (v6.4).

CRUD helpers for the ``product_segment_llm_interactions`` table which stores a
lightweight index pointing to the raw JSON files in storage.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from supabase import Client  # type: ignore

from product_segmentation.models import ProductSegmentLLMInteraction

logger = logging.getLogger(__name__)

_TABLE = "product_segment_llm_interactions"


class ProductSegmentLLMInteractionRepository:  # pylint: disable=too-few-public-methods
    """Data-access helpers for *product_segment_llm_interactions*."""

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    # ------------------------------------------------------------------
    # Inserts
    # ------------------------------------------------------------------
    async def batch_create(self, interactions: List[ProductSegmentLLMInteraction]) -> bool:
        """Insert multiple interaction-index rows in a single request."""
        if not interactions:
            return True
        payload = [i.model_dump(exclude_unset=True) for i in interactions]
        try:
            result = self._client.table(_TABLE).insert(payload).execute()
            if result.data:
                logger.info("Inserted %d LLM interaction index rows", len(result.data))
                return True
            logger.error("Failed to insert LLM interactions – empty response")
            return False
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error inserting LLM interactions: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    async def get_by_run(self, run_id: str) -> List[ProductSegmentLLMInteraction]:
        try:
            result = (
                self._client.table(_TABLE)
                .select("*")
                .eq("run_id", run_id)
                .order("id")
                .execute()
            )
            return [ProductSegmentLLMInteraction(**row) for row in result.data] if result.data else []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching interactions for run %s: %s", run_id, exc)
            return []

    async def get_by_cache_key(self, cache_key: str) -> Optional[ProductSegmentLLMInteraction]:
        try:
            result = (
                self._client.table(_TABLE)
                .select("*")
                .eq("cache_key", cache_key)
                .order("id")
                .limit(1)
                .execute()
            )
            if result.data:
                return ProductSegmentLLMInteraction(**result.data[0])
            return None
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching interaction by cache_key %s: %s", cache_key, exc)
            return None 