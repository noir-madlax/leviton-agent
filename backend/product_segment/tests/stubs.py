"""Shared test stubs for product segmentation tests.

This module provides reusable stub implementations for testing the product
segmentation service without external dependencies.
"""

import json
from typing import Any, Dict, List, Optional, Sequence
import re


class StubLLM:
    """Stub LLM client that returns deterministic responses.
    
    This stub can be used in different contexts:
    1. As a direct LLM client (implements __call__)
    2. As a service-level client (implements segment_products, consolidate_taxonomy, refine_assignments)
    """

    def __init__(self, fail_consolidation: bool = False, fail_refinement: bool = False):
        self.fail_consolidation = fail_consolidation
        self.fail_refinement = fail_refinement
        self._batch_count = 0  # Track batch number for different taxonomies

    async def __call__(self, prompt: str, model: str = None, temperature: float = None) -> str:
        """Return deterministic response based on prompt (for direct LLM client usage)."""
        if "Extract taxonomy" in prompt:
            # Extract product indices from the prompt
            product_matches = re.findall(r'\[(\d+)\]', prompt)
            if product_matches:
                # Use the indices (0, 1, 2, ...) as expected by the segmentation logic
                indices = list(range(len(product_matches)))
                return json.dumps({
                    "Category A": {
                        "definition": "First category",
                        "ids": indices
                    }
                })
            else:
                # Fallback for when we can't parse product indices
                return json.dumps({
                    "Category A": {
                        "definition": "First category",
                        "ids": [0, 1, 2]
                    }
                })
        elif "Consolidate taxonomies" in prompt:
            if self.fail_consolidation:
                raise RuntimeError("Simulated consolidation failure")
            return json.dumps({
                "Category A": {
                    "definition": "First category",
                    "ids": ["A_0"]
                }
            })
        elif "Refine assignments" in prompt:
            if self.fail_refinement:
                raise RuntimeError("Simulated refinement failure")
            return json.dumps({
                "segments": [
                    {"product_id": 1, "taxonomy_id": 1, "category_name": "Category A"},
                    {"product_id": 2, "taxonomy_id": 1, "category_name": "Category A"}
                ]
            })
        return "{}"

    async def segment_products(self, products: Sequence[int], *, category: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """Return deterministic segmentation (for service-level usage)."""
        self._batch_count += 1
        category_name = f"Category {chr(64 + self._batch_count)}"  # A, B, C, etc.
        
        return {
            "segments": [
                {"product_id": pid, "taxonomy_id": self._batch_count, "category_name": category_name}
                for pid in products
            ],
            "taxonomies": [
                {
                    "category_name": category_name,
                    "definition": f"{category_name} definition",
                    "product_count": len(products)
                }
            ],
            "cache_key": f"stub_segment_{self._batch_count}"
        }

    async def consolidate_taxonomy(self, taxonomies: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """Return deterministic consolidation (for service-level usage).

        The service layer expects the key **"taxonomies"** in the response –
        returning anything else will raise a ``KeyError``.
        """
        if self.fail_consolidation:
            raise RuntimeError("Simulated consolidation failure")
        return {
            "taxonomies": taxonomies,
            "segments": [],
            "cache_key": "stub_consolidate_1",
        }

    async def refine_assignments(self, segments: List[Dict[str, Any]], taxonomies: Optional[List[Dict[str, Any]]] = None, **kwargs) -> Dict[str, Any]:
        """Return deterministic refinement (for service-level usage)."""
        if self.fail_refinement:
            raise RuntimeError("Simulated refinement failure")
        return {
            "segments": segments,
            "cache_key": "stub_refine_1"
        } 