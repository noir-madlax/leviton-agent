"""Repository for product taxonomy data access.

This repository mirrors the structure and coding style of the sibling
`SegmentationRunRepository` and `ProductSegmentRepository` classes that already
exist in the codebase.  Only the CRUD operations required by the current
service layer (Phase 3) are implemented.  Additional helper methods can be
added later once we need more advanced queries.

All Supabase calls follow the same *fire-and-forget* strategy as the other
repositories — they log on failure and return a boolean/empty list so the
caller can decide how to respond.  The repository does **not** raise because we
want the orchestration layer to retain full control over error handling.
"""

from typing import List
import logging
from supabase import Client

from product_segmentation.models import (
    ProductTaxonomy,
    ProductTaxonomyCreate,
)

logger = logging.getLogger(__name__)


class ProductTaxonomyRepository:  # pylint: disable=too-few-public-methods
    """Data-access helper for the *product_taxonomies* table."""

    def __init__(self, supabase_client: Client):  # noqa: D401 – simple init
        self._client = supabase_client
        self._table = "product_taxonomies"

    # ---------------------------------------------------------------------
    # Public API
    # ---------------------------------------------------------------------

    async def batch_create_taxonomies(self, taxonomies: List[ProductTaxonomyCreate]) -> List[ProductTaxonomy]:
        """Insert multiple taxonomy rows and return the created records.

        The caller is responsible for ensuring (run_id, category_name) pairs
        are unique to avoid database constraint violations.

        Returns
        -------
        List[ProductTaxonomy]
            The list of inserted taxonomy rows (may be empty on failure).
        """
        if not taxonomies:
            return []  # nothing to do

        payload = [tax.model_dump(exclude_unset=True) for tax in taxonomies]
        try:
            result = (
                self._client.table(self._table)
                .insert(payload, returning="representation")
                .execute()
            )
            if result.data:
                logger.info("Inserted %d taxonomy rows", len(result.data))
                return [ProductTaxonomy.parse_obj(row) for row in result.data]
            logger.error("Failed to insert taxonomies – empty response. Payload=%s, Response=%s", payload, result)
            return []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error inserting taxonomies: %s", exc)
            return []

    async def get_taxonomies_by_run(self, run_id: str) -> List[ProductTaxonomy]:
        """Fetch all taxonomies for a given run (ordered by *id*)."""
        try:
            result = (
                self._client.table(self._table)
                .select("*")
                .eq("run_id", run_id)
                .order("id")
                .execute()
            )
            if result.data:
                return [ProductTaxonomy.parse_obj(row) for row in result.data]
            return []
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Error fetching taxonomies for run %s: %s", run_id, exc)
            return [] 