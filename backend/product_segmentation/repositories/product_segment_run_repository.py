"""Product-segment run repository (v6.4).

Thin data-access layer around the ``product_segment_runs`` table.
Assumes the table already exists – *no* backwards-compat creation logic.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional

from supabase import Client  # type: ignore

from product_segmentation.models import (
    ProductSegmentRun,
    SegmentationStage,
)

logger = logging.getLogger(__name__)


_JSON_COLS = {"llm_config", "processing_params", "result_summary"}
_TABLE = "product_segment_runs"


class ProductSegmentRunRepository:
    """Repository for CRUD operations on *product_segment_runs*."""

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _model_to_payload(model: ProductSegmentRun) -> Dict[str, Any]:
        """Convert *ProductSegmentRun* → dict suitable for Supabase insert/update."""
        data = model.model_dump()
        for col in _JSON_COLS:
            if col in data and data[col] is not None:
                data[col] = json.dumps(data[col])
        # Convert enum to value
        data["stage"] = model.stage.value
        return data

    @staticmethod
    def _row_to_model(row: Dict[str, Any]) -> ProductSegmentRun:
        """Convert DB row → *ProductSegmentRun* (JSON columns decoded)."""
        for col in _JSON_COLS:
            if col in row and isinstance(row[col], str):
                try:
                    row[col] = json.loads(row[col])
                except json.JSONDecodeError:
                    logger.warning("Failed to decode JSON column %s", col)
        # stage comes back as str → Enum
        if isinstance(row.get("stage"), str):
            row["stage"] = SegmentationStage(row["stage"])
        return ProductSegmentRun(**row)

    # ------------------------------------------------------------------
    # CRUD operations
    # ------------------------------------------------------------------
    async def create(self, run: ProductSegmentRun) -> ProductSegmentRun:
        """Insert *run* and return the persisted record."""
        payload = self._model_to_payload(run)
        logger.debug("Inserting product_segment_run: %s", payload)
        result = self._client.table(_TABLE).insert(payload).execute()
        row = result.data[0]  # Supabase returns inserted row
        return self._row_to_model(row)

    async def get_by_id(self, run_id: str) -> Optional[ProductSegmentRun]:
        result = self._client.table(_TABLE).select("*").eq("id", run_id).execute()
        if result.data:
            return self._row_to_model(result.data[0])
        return None

    async def update_stage(self, run_id: str, stage: SegmentationStage) -> bool:
        result = (
            self._client.table(_TABLE)
            .update({"stage": stage.value})
            .eq("id", run_id)
            .execute()
        )
        return bool(result.data)

    async def update_progress(
        self,
        run_id: str,
        *,
        seg_batches_done: Optional[int] = None,
        con_batches_done: Optional[int] = None,
        ref_batches_done: Optional[int] = None,
        processed_products: Optional[int] = None,
    ) -> bool:
        update_data: Dict[str, Any] = {}
        if seg_batches_done is not None:
            update_data["seg_batches_done"] = seg_batches_done
        if con_batches_done is not None:
            update_data["con_batches_done"] = con_batches_done
        if ref_batches_done is not None:
            update_data["ref_batches_done"] = ref_batches_done
        if processed_products is not None:
            update_data["processed_products"] = processed_products
        if not update_data:
            return True  # nothing to update
        result = self._client.table(_TABLE).update(update_data).eq("id", run_id).execute()
        return bool(result.data)

    async def complete_run(self, run_id: str, result_summary: Dict[str, Any]) -> bool:
        payload = {
            "stage": SegmentationStage.COMPLETED.value,
            "result_summary": json.dumps(result_summary),
        }
        result = self._client.table(_TABLE).update(payload).eq("id", run_id).execute()
        return bool(result.data)

    async def delete(self, run_id: str) -> bool:
        result = self._client.table(_TABLE).delete().eq("id", run_id).execute()
        return bool(result.data)

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------
    async def get_recent_runs(self, limit: int = 10) -> List[ProductSegmentRun]:
        result = (
            self._client.table(_TABLE)
            .select("*")
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return [self._row_to_model(r) for r in result.data] if result.data else []

    async def get_runs_by_stage(self, stage: SegmentationStage) -> List[ProductSegmentRun]:
        result = (
            self._client.table(_TABLE)
            .select("*")
            .eq("stage", stage.value)
            .order("created_at", desc=True)
            .execute()
        )
        return [self._row_to_model(r) for r in result.data] if result.data else [] 