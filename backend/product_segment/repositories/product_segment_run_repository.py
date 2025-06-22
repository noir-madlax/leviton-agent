"""Product-segment run repository (v6.4).

Thin data-access layer around the ``product_segment_runs`` table.
Assumes the table already exists – *no* backwards-compat creation logic.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, Optional

from supabase import Client  # type: ignore

from product_segment.models import (
    ProductSegmentRun,
    SegmentationStage,
)

logger = logging.getLogger(__name__)

_JSON_COLS = {"llm_config", "processing_params", "result_summary"}
_TABLE = "product_segment_runs"

class SegmentationRunRepository:
    """Repository for CRUD operations on product_segment_runs."""

    def __init__(self, supabase_client: Client):
        self._client = supabase_client

    @staticmethod
    def _model_to_payload(model: ProductSegmentRun) -> Dict[str, Any]:
        """Convert ProductSegmentRun → dict suitable for Supabase insert/update."""
        data = model.model_dump()
        for col in _JSON_COLS:
            if col in data and data[col] is not None:
                data[col] = json.dumps(data[col])
        # Convert enum to value
        data["stage"] = model.stage.value
        return data

    @staticmethod
    def _row_to_model(row: Dict[str, Any]) -> ProductSegmentRun:
        """Convert DB row → ProductSegmentRun (JSON columns decoded)."""
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

    async def create(self, run: ProductSegmentRun) -> ProductSegmentRun:
        """Insert run and return the persisted record."""
        payload = self._model_to_payload(run)
        logger.debug("Inserting product_segment_run: %s", payload)
        result = self._client.table(_TABLE).insert(payload).execute()
        row = result.data[0]  # Supabase returns inserted row
        return self._row_to_model(row)

    async def get_by_id(self, run_id: str) -> Optional[ProductSegmentRun]:
        """Get run by ID."""
        result = self._client.table(_TABLE).select("*").eq("id", run_id).execute()
        if result.data:
            return self._row_to_model(result.data[0])
        return None

    async def update_stage(self, run_id: str, stage: SegmentationStage) -> bool:
        """Update run stage."""
        result = (
            self._client.table(_TABLE)
            .update({"stage": stage.value})
            .eq("id", run_id)
            .execute()
        )
        return bool(result.data)

    async def update_total_calls(self, run_id: str, total_calls: int) -> bool:
        """Update total expected LLM calls for the run."""
        result = (
            self._client.table(_TABLE)
            .update({"calls_total": total_calls})
            .eq("id", run_id)
            .execute()
        )
        return bool(result.data)

    async def update_calls_done(self, run_id: str, calls_done: int) -> bool:
        """Update number of completed LLM calls."""
        result = (
            self._client.table(_TABLE)
            .update({"calls_done": calls_done})
            .eq("id", run_id)
            .execute()
        )
        return bool(result.data) 