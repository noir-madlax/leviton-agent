"""Configuration for product segmentation module.

This module centralizes all configuration parameters for the product segmentation
pipeline, particularly the different size limits for each phase of processing.

All parameters can be overridden via environment variables, with the values below
serving as defaults for local development.
"""

from typing import Final

# Number of products to process in a single LLM call during initial segmentation
PRODUCTS_PER_TAXONOMY_PROMPT: Final[int] = 40

# Maximum number of taxonomies to consolidate in a single LLM call
TAXONOMIES_PER_CONSOLIDATION: Final[int] = 20

# Number of product assignments to refine in a single LLM call
PRODUCTS_PER_REFINEMENT: Final[int] = 40

# Maximum retries for LLM calls
MAX_RETRIES: Final[int] = 3

__all__ = [
    "PRODUCTS_PER_TAXONOMY_PROMPT",
    "TAXONOMIES_PER_CONSOLIDATION", 
    "PRODUCTS_PER_REFINEMENT",
    "MAX_RETRIES"
] 