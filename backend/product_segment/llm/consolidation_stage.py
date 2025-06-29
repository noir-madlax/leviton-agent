"""Consolidation stage implementation for the generic LLM-powered taxonomy pipeline.

This module defines a *ConsolidationStage* that takes two existing taxonomies
and consolidates them by identifying similar categories and grouping them together,
while preserving the specificity and distinctiveness of each category type.

The stage is built on the generic :class:`BaseStage` utilities which already
provide *attempt / retry / auto-split / persistence* mechanics.  The only
responsibilities left here are:

• Prompt construction with two taxonomies as input.
• Response validation & parsing.
• Retry-prompt construction given a structured *retry-context*.
• Collating split-results back together.

The expected LLM output **must** be a JSON object of the following shape::

    {
      "Consolidated Category Name 1": {
        "definition": "..., e.g. <specific product subtypes>",
        "ids": ["A_0", "B_1"]
      },
      "Consolidated Category Name 2": {
        "definition": "..., e.g. ...",
        "ids": ["A_1"]
      },
      "Consolidated Category Name 3": {
        "definition": "..., e.g. ...",
        "ids": ["B_0"]
      }
    }

Each top-level key represents a consolidated taxonomy category name. Each category must have
a "definition" field and an "ids" field containing an array of original category IDs.
Each original category ID (A_*, B_*) must appear **exactly once** across
all "ids" arrays with no duplicates or missing IDs.
"""

from pathlib import Path

from core.llm_taxonomy_pipeline.consolidation_base import (
    ConsolidationStage as BaseConsolidationStage,
    ConsolidatedTaxonomyDTO,
    ConsolidationStageContext,
    ConsolidationStageResult,
)

__all__ = [
    "ConsolidatedTaxonomyDTO",
    "ConsolidationStageResult",
    "ConsolidationStageContext", 
    "ConsolidationStage",
]

# Path to prompt template files
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_CONSOLIDATE_PROMPT_FILE = "taxonomy_consolidation_prompt_v0.txt"


class ConsolidationStage(BaseConsolidationStage):
    """Concrete taxonomy-consolidation stage built on :class:`BaseStage`."""

    def __init__(self):
        """Initialize with product segment templates."""
        consolidate_template, retry_template = self.load_templates(
            _PROMPTS_DIR, _CONSOLIDATE_PROMPT_FILE
        )
        super().__init__(consolidate_template, retry_template)