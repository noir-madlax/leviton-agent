"""Review-specific consolidation stage implementation.

This module provides consolidation for review aspects (physical, performance, use case)
by inheriting from the generic core consolidation implementation and adding only 
review-specific template variables and deduplication logic.
"""

from pathlib import Path
from typing import Dict
import json

from core.llm_taxonomy_pipeline.consolidation_base import (
    ConsolidationStage as BaseConsolidationStage,
    ConsolidationStageContext,
    ConsolidationStageResult,
    ConsolidatedTaxonomyDTO,
)

__all__ = [
    "ConsolidatedTaxonomyDTO",
    "ConsolidationStageResult", 
    "ConsolidationStageContext",
    "ConsolidationStage",
]

# Prompt template paths
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_CONSOLIDATE_PROMPT_FILE = "review_aspects_consolidation_prompt_v0.txt"


class ConsolidationStage(BaseConsolidationStage):
    """Review aspect consolidation stage with deduplication support."""

    def __init__(self, aspect_type: str = "", product_categories: set = None):
        """Initialize with review-specific context."""
        consolidate_template, retry_template = self.load_templates(
            _PROMPTS_DIR, _CONSOLIDATE_PROMPT_FILE
        )
        super().__init__(consolidate_template, retry_template)
        
        self.aspect_type = aspect_type
        self.product_categories = product_categories or set()

        # Provide default aspect definitions that match extraction prompt semantics
        self._aspect_type_definitions: Dict[str, str] = {
            "physical": (
                "Components or inherent physical properties of the product, such as "
                "dimensions, appearance, or material composition."
            ),
            "performance": (
                "Performance characteristics or behaviours of the product under various "
                "conditions, e.g. durability, reliability, speed, flexibility."
            ),
            "use": (
                "Specific applications, objects, methods, tools, or environments that "
                "illustrate how customers use the product."
            ),
        }

    def _get_additional_template_vars(self, ctx: ConsolidationStageContext) -> Dict[str, str]:
        """Add review-specific template variables."""
        # Resolve aspect definition, fall back to empty string if not available
        aspect_definition = self._aspect_type_definitions.get(self.aspect_type.lower(), "")

        product_context = ""
        if self.product_categories:
            categories_list = ', '.join(sorted(self.product_categories))
            product_context = (
                f"\n\n**PRODUCT CATEGORIES IN DATASET:** {categories_list}\n"
                f"Consider how {self.aspect_type} aspects relate to customer needs "
                f"across these {len(self.product_categories)} product categories."
            )
        
        return {
            "aspect_type": self.aspect_type,
            "aspect_definition": aspect_definition,
            "product_context": product_context,
        }