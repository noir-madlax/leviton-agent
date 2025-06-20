"""Product-segment taxonomy repository (v6.4).

Thin CRUD wrapper around the ``product_segment_taxonomies`` table.  No legacy
fallbacks – expects the table exists and the caller provides valid data.
"""

from __future__ import annotations

import logging
from typing import List

from supabase import Client  # type: ignore

from product_segmentation.models import ProductSegmentTaxonomy

logger = logging.getLogger(__name__)

_TABLE = "product_segment_taxonomies"


class ProductSegmentTaxonomyRepository:  # pylint: disable=too-few-public-methods
    """Data-access helpers for the *product_segment_taxonomies* table."""

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    # ------------------------------------------------------------------
    # Inserts
    # ------------------------------------------------------------------
    async def batch_create(self, taxonomies: List[ProductSegmentTaxonomy]) -> List[ProductSegmentTaxonomy]:
        """Insert *taxonomies* and return the persisted rows."""
        if not taxonomies:
            return []
        payload = [t.model_dump(exclude_unset=True) for t in taxonomies]
        try:
            result = (
                self._client.table(_TABLE)
                .insert(payload, returning="representation")
                .execute()
            )
            if result.data:
                logger.info("Inserted %d taxonomy rows", len(result.data))
                return [ProductSegmentTaxonomy(**row) for row in result.data]
            logger.error("Failed to insert product taxonomies – empty response: %s", payload)
            return []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error inserting product taxonomies: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    async def get_by_run(self, run_id: str) -> List[ProductSegmentTaxonomy]:
        try:
            result = (
                self._client.table(_TABLE)
                .select("*")
                .eq("run_id", run_id)
                .order("id")
                .execute()
            )
            return [ProductSegmentTaxonomy(**row) for row in result.data] if result.data else []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching taxonomies for run %s: %s", run_id, exc)
            return []

    # ------------------------------------------------------------------
    # Deletion helpers
    # ------------------------------------------------------------------
    async def delete_by_run(self, run_id: str) -> bool:
        try:
            result = self._client.table(_TABLE).delete().eq("run_id", run_id).execute()
            return bool(result.data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error deleting taxonomies for run %s: %s", run_id, exc)
            return False 