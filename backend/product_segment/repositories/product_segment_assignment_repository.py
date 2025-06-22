"""Product-segment assignment repository (v6.4).

Data-access helpers for the product_segment_assignments table.
The table contains exactly one row per (run, product) pair and stores both
the initial (extraction) and refined taxonomy IDs.
"""

from __future__ import annotations

import logging
from typing import List

from supabase import Client  # type: ignore

from product_segment.models import ProductSegmentAssignment

logger = logging.getLogger(__name__)

_TABLE = "product_segment_assignments"

class ProductSegmentRepository:
    """CRUD helpers for product_segment_assignments."""

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    async def batch_create_assignments(self, assignments: List[ProductSegmentAssignment]) -> bool:
        """Create initial assignments with unassigned taxonomy."""
        try:
            if not assignments:
                return True
            payload = [a.model_dump(exclude_unset=True) for a in assignments]
            result = self._client.table(_TABLE).insert(payload).execute()
            return bool(result.data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to create assignments: %s", exc)
            return False

    async def get_run_products(self, run_id: str) -> List[int]:
        """Get all product IDs for a run."""
        try:
            result = self._client.table(_TABLE).select("product_id").eq("run_id", run_id).execute()
            return [row["product_id"] for row in result.data] if result.data else []
        except Exception as exc:
            logger.exception("Failed to get run products: %s", exc)
            return []

    async def update_initial_taxonomy(self, run_id: str, product_id: int, taxonomy_id: int) -> bool:
        """Update initial taxonomy assignment."""
        try:
            result = (
                self._client.table(_TABLE)
                .update({"taxonomy_id_initial": taxonomy_id})
                .eq("run_id", run_id)
                .eq("product_id", product_id)
                .execute()
            )
            return bool(result.data)
        except Exception as exc:
            logger.exception("Failed to update initial taxonomy: %s", exc)
            return False

    async def update_refined_taxonomy(self, run_id: str, product_id: int, taxonomy_id: int) -> bool:
        """Update refined taxonomy assignment."""
        try:
            result = (
                self._client.table(_TABLE)
                .update({"taxonomy_id_refined": taxonomy_id})
                .eq("run_id", run_id)
                .eq("product_id", product_id)
                .execute()
            )
            return bool(result.data)
        except Exception as exc:
            logger.exception("Failed to update refined taxonomy: %s", exc)
            return False 