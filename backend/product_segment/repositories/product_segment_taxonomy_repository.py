"""Product-segment taxonomy repository (v6.4).

Thin CRUD wrapper around the ``product_segment_taxonomies`` table.
Assumes the table exists and the caller provides valid data.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from supabase import Client  # type: ignore

from product_segment.models import ProductSegmentTaxonomy

logger = logging.getLogger(__name__)

_TABLE = "product_segment_taxonomies"

class ProductTaxonomyRepository:
    """Data-access helpers for the product_segment_taxonomies table."""

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    async def create_taxonomy(self, taxonomy: ProductSegmentTaxonomy) -> int:
        """Create a single taxonomy and return its ID."""
        try:
            payload = taxonomy.model_dump(exclude_unset=True)
            result = (
                self._client.table(_TABLE)
                .insert(payload)
                .execute()
            )
            if result.data:
                return result.data[0]["id"]
            logger.error("Failed to insert taxonomy – empty response: %s", payload)
            return 0
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error inserting taxonomy: %s", exc)
            return 0

    async def batch_create_taxonomies(self, taxonomies: List[ProductSegmentTaxonomy]) -> List[int]:
        """Insert taxonomies and return their IDs."""
        if not taxonomies:
            return []
        payload = [t.model_dump(exclude_unset=True) for t in taxonomies]
        try:
            result = (
                self._client.table(_TABLE)
                .insert(payload)
                .execute()
            )
            if result.data:
                logger.info("Inserted %d taxonomy rows", len(result.data))
                return [row["id"] for row in result.data]
            logger.error("Failed to insert taxonomies – empty response: %s", payload)
            return []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error inserting taxonomies: %s", exc)
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