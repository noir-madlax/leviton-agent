from __future__ import annotations

import logging
from typing import List

from supabase import Client  # type: ignore

logger = logging.getLogger(__name__)

_TABLE = "review_analysis_aspect_occurrences"


class AspectOccurrenceRepository:
    """CRUD helpers for aspect_occurrence fact table."""

    def __init__(self, client: Client):
        self._client = client

    async def batch_insert(self, rows: List[dict]) -> bool:  # noqa: D401 – async
        """Insert occurrence rows (dicts must match DB column names)."""
        if not rows:
            return True
        try:
            res = self._client.table(_TABLE).insert(rows).execute()
            return bool(res.data)
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to insert aspect occurrences: %s", exc)
            return False 