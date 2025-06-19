"""Utility helpers for working with product taxonomies.

These functions are minimal *Python*-only implementations that enable the
``DatabaseProductSegmentationService`` to perform a *best-effort* consolidation
step when no advanced LLM support is available.  The logic purposefully keeps
state handling simple and deterministic so that it can be unit-tested without
external services.
"""

from typing import Any, Dict, List

__all__ = [
    "merge_batch_taxonomies",
]


def merge_batch_taxonomies(taxonomies: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Merge multiple *batch-level* taxonomy dicts into a single structure.

    Each taxonomy in *taxonomies* is expected to follow the schema returned by
    the stub LLM client:

    ``{"category_name": str, "definition": str, "product_count": int}``

    The merge strategy is *name-based*: identical ``category_name`` entries are
    merged by keeping the first encountered *definition* and summing the
    *product_count* values.  The function returns a mapping that can later be
    persisted via :class:`backend.product_segmentation.repositories.product_taxonomy_repository.ProductTaxonomyRepository`.
    """
    merged: Dict[str, Dict[str, Any]] = {}

    for tax in taxonomies:
        name = tax.get("category_name")
        if not name:
            # Skip invalid records – service has already validated the presence
            # of a name field before passing the data down here.
            continue

        entry = merged.setdefault(
            name,
            {
                "category_name": name,
                "definition": tax.get("definition"),
                "product_count": 0,
            },
        )

        # Keep first non-empty definition encountered
        if not entry.get("definition") and tax.get("definition"):
            entry["definition"] = tax["definition"]

        entry["product_count"] = entry.get("product_count", 0) + tax.get(
            "product_count", 0
        )

    return merged 