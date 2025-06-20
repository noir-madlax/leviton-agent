"""Product-segment assignment repository (v6.4).

Data-access helpers for the *product_segment_assignments* table.  The table
contains exactly one row per (run, product) pair and stores both the *initial*
(extraction) and *refined* taxonomy IDs.

The repository methods intentionally mirror the interface expected by the
service layer so that no further refactoring is required.
"""

from __future__ import annotations

import logging
from typing import List

from supabase import Client  # type: ignore

from product_segmentation.models import (
    ProductSegmentAssignment,
)

logger = logging.getLogger(__name__)

_TABLE = "product_segment_assignments"


class ProductSegmentAssignmentRepository:
    """CRUD helpers for product_segment_assignments."""

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    # ------------------------------------------------------------------
    # Run-product helpers (replaces legacy *run_products* table)
    # ------------------------------------------------------------------
    async def create_run_products(self, run_id: str, product_ids: List[int]) -> bool:  # noqa: D401
        """Create placeholder assignment rows for *run_id* and the given *product_ids*."""
        try:
            rows = [{"run_id": run_id, "product_id": pid} for pid in product_ids]
            result = self._client.table(_TABLE).insert(rows, upsert=True).execute()
            return bool(result.data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to create run products: %s", exc)
            return False

    async def get_run_products(self, run_id: str) -> List[int]:
        try:
            result = self._client.table(_TABLE).select("product_id").eq("run_id", run_id).execute()
            return [row["product_id"] for row in result.data] if result.data else []
        except Exception as exc:
            logger.exception("Failed to get run products: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Initial extraction assignments
    # ------------------------------------------------------------------
    async def batch_create_segments(self, segments: List[dict]) -> bool:
        """Upsert *initial* taxonomy assignments produced during extraction."""
        try:
            if not segments:
                return True
            rows = [
                {
                    "run_id": s["run_id"],
                    "product_id": s["product_id"],
                    "taxonomy_id_initial": s["taxonomy_id"],
                }
                for s in segments
            ]
            result = self._client.table(_TABLE).upsert(rows, on_conflict=["run_id", "product_id"]).execute()
            return bool(result.data)
        except Exception as exc:
            logger.exception("Failed to upsert initial segments: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Refinement assignments
    # ------------------------------------------------------------------
    async def batch_create_refined_segments(self, segments: List[dict]) -> bool:
        """Populate *refined* taxonomy assignments."""
        try:
            if not segments:
                return True
            # Build update list (Supabase upsert will update existing rows)
            rows = [
                {
                    "run_id": s["run_id"],
                    "product_id": s["product_id"],
                    "taxonomy_id_refined": s["taxonomy_id"],
                }
                for s in segments
            ]
            result = self._client.table(_TABLE).upsert(rows, on_conflict=["run_id", "product_id"]).execute()
            return bool(result.data)
        except Exception as exc:
            logger.exception("Failed to upsert refined segments: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------
    async def get_assignments_by_run(self, run_id: str) -> List[ProductSegmentAssignment]:
        try:
            result = self._client.table(_TABLE).select("*").eq("run_id", run_id).execute()
            return [ProductSegmentAssignment(**row) for row in result.data] if result.data else []
        except Exception as exc:
            logger.exception("Failed to get assignments: %s", exc)
            return []

    async def delete_by_run(self, run_id: str) -> bool:
        try:
            result = self._client.table(_TABLE).delete().eq("run_id", run_id).execute()
            return bool(result.data)
        except Exception as exc:
            logger.exception("Failed to delete assignments: %s", exc)
            return False 