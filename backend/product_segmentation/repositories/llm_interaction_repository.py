"""Repository for *llm_interaction_index* table access.

This repository provides a minimal CRUD interface used by the product
segmentation engine to persist an index of raw LLM interaction files.  The
implementation mirrors the existing repository classes in this package so that
higher-level services can be wired with dependency-injection in exactly the
same way.

Only the insert operation is required by the current service layer, but a
simple ``get_by_run`` helper is included for future use and to make unit-testing
straight-forward.
"""

from typing import List
import logging
from supabase import Client

from backend.product_segmentation.models import (
    LLMInteractionIndex,
    LLMInteractionIndexCreate,
)

logger = logging.getLogger(__name__)


class LLMInteractionRepository:  # pylint: disable=too-few-public-methods
    """Data-access helper for the *llm_interaction_index* table."""

    def __init__(self, supabase_client: Client):  # noqa: D401 – simple init
        self._client = supabase_client
        self._table = "llm_interaction_index"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def batch_create_interactions(
        self, interactions: List[LLMInteractionIndexCreate]
    ) -> bool:
        """Insert multiple interaction index rows.

        The service typically calls this once per batch so grouping everything
        into *one* request keeps the network overhead low.
        """
        if not interactions:
            return True  # trivially successful

        payload = [interaction.dict(exclude_unset=True) for interaction in interactions]
        try:
            result = self._client.table(self._table).insert(payload).execute()
            if result.data and len(result.data) > 0:
                logger.info("Inserted %d LLM interaction index rows", len(result.data))
                return True
            logger.error("Failed to insert LLM interactions – empty response")
            return False
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error inserting LLM interactions: %s", exc)
            return False

    async def get_by_run(self, run_id: str) -> List[LLMInteractionIndex]:
        """Return all interactions (ordered by *id*) for the given run."""
        try:
            result = (
                self._client.table(self._table)
                .select("*")
                .eq("run_id", run_id)
                .order("id")
                .execute()
            )
            if result.data:
                return [LLMInteractionIndex.parse_obj(row) for row in result.data]
            return []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching interaction index for run %s: %s", run_id, exc)
            return []

    async def get_by_cache_key(self, cache_key: str) -> LLMInteractionIndex | None:
        """Return the **first** interaction that matches *cache_key*.

        The client code only needs to know whether *any* previous interaction
        exists so that it can load the raw JSON file from storage.  We
        therefore return at most **one** row (the oldest by *id*) or *None*.
        """
        try:
            result = (
                self._client.table(self._table)
                .select("*")
                .eq("cache_key", cache_key)
                .order("id")
                .limit(1)
                .execute()
            )
            if result.data:
                return LLMInteractionIndex.parse_obj(result.data[0])
            return None
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching interaction by cache_key %s: %s", cache_key, exc)
            return None 