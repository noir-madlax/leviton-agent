from __future__ import annotations

import logging
from typing import List

from supabase import Client  # type: ignore

logger = logging.getLogger(__name__)

_TABLE = "review_analysis_aspect_categories"


class AspectCategoryRepository:
    """Repository for the aspect_category table."""

    def __init__(self, client: Client):
        self._client = client

    async def batch_insert(self, categories: List[dict]) -> List[int]:
        """Insert categories and return the PK list."""
        if not categories:
            return []
        try:
            res = self._client.table(_TABLE).insert(categories).execute()
            return [row["category_pk"] for row in res.data] if res.data else []
        except Exception as exc:  # pylint: disable=broad-except
            logger.exception("Failed to insert categories: %s", exc)
            return [] 