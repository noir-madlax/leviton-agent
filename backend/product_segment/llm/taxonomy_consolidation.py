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

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from core.utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from product_segment.llm.taxonomy_pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
)

__all__ = [
    "ConsolidatedTaxonomyDTO",
    "ConsolidationStageResult",
    "ConsolidationStage",
]

# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class ConsolidatedTaxonomyDTO:  # noqa: D401 – simple DTO
    """Lightweight consolidated taxonomy representation returned by the consolidation stage."""

    name: str
    definition: str
    original_ids: list[str]


@dataclass(slots=True, frozen=True)
class ConsolidationStageResult(StageResultBase):
    """Result returned by the consolidation stage."""
    
    taxonomies_consolidated: list[ConsolidatedTaxonomyDTO]
    consolidation_mapping: dict[str, str]  # original_id -> consolidated_category_name

# ---------------------------------------------------------------------------
# Fixed prompt templates
# ---------------------------------------------------------------------------
# The stage uses fixed prompt templates from the prompts directory to ensure
# consistency across all consolidation operations.
# ---------------------------------------------------------------------------

# Path to prompt template files
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_CONSOLIDATE_PROMPT_PATH = _PROMPTS_DIR / "taxonomy_consolidation_prompt_v0.txt"
_RETRY_PROMPT_PATH = _PROMPTS_DIR / "shared_retry_prompt_v0.txt"

# Load prompt templates at module level
try:
    with open(_CONSOLIDATE_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _CONSOLIDATE_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_CONSOLIDATE_PROMPT_PATH}")

try:
    with open(_RETRY_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _RETRY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required retry template not found: {_RETRY_PROMPT_PATH}")


# ---------------------------------------------------------------------------
# ConsolidationStage implementation
# ---------------------------------------------------------------------------


class ConsolidationStage(BaseStage):
    """Concrete taxonomy-consolidation stage built on :class:`BaseStage`."""

    # --------------------- BaseStage abstract hooks -------------------------

    async def _build_prompt(self, seq: Sequence[str], ctx: StageContext) -> str:  # noqa: D401
        """Render the fixed prompt template with the two taxonomies."""

        # For consolidation, seq should contain exactly 2 elements: taxonomy_a and taxonomy_b
        if len(seq) != 2:
            raise ValueError(f"ConsolidationStage expects exactly 2 taxonomies, got {len(seq)}")

        taxonomy_a, taxonomy_b = seq
        
        # Use the fixed consolidation prompt template
        template_vars = {
            "taxonomy_a": taxonomy_a,
            "taxonomy_b": taxonomy_b
        }
        
        try:
            rendered_template = _CONSOLIDATE_PROMPT_TEMPLATE.format(**template_vars)
        except KeyError as exc:
            raise ValueError(f"Missing template variable {exc} for prompt_template") from exc

        return rendered_template

    def _validate(
        self, raw_response: str, seq: Sequence[str], ctx: StageContext
    ) -> ValidationResult:
        """Validate and (optionally) return retry-context."""

        # Extract expected IDs from the input taxonomies
        expected_ids = set()
        try:
            # Parse both taxonomies to extract all category IDs
            taxonomy_a, taxonomy_b = seq
            
            # Parse taxonomy A
            taxonomy_a_data = json.loads(taxonomy_a)
            for category_id in taxonomy_a_data.keys():
                expected_ids.add(category_id)
            
            # Parse taxonomy B  
            taxonomy_b_data = json.loads(taxonomy_b)
            for category_id in taxonomy_b_data.keys():
                expected_ids.add(category_id)
                
        except Exception as exc:
            return ValidationResult(
                ok=False, 
                error_categories={"format_errors": [f"Failed to parse input taxonomies: {exc}"]}
            )

        error_categories: Dict[str, List[str]] = {
            "format_errors": [],
            "validation_errors": [],
            "completeness_errors": [],
        }

        try:
            json_text = extract_json(raw_response)
            parsed = json.loads(json_text)
        except Exception as exc:  # pylint: disable=broad-except
            error_categories["format_errors"].append(str(exc))
            return ValidationResult(ok=False, error_categories=error_categories)

        # Basic structure checks
        if not isinstance(parsed, dict):
            error_categories["format_errors"].append("Top-level JSON must be an object")
            return ValidationResult(ok=False, error_categories=error_categories)

        if not parsed:
            error_categories["format_errors"].append("JSON object cannot be empty")
            return ValidationResult(ok=False, error_categories=error_categories)

        # Validate each consolidated category
        category_names = set()
        all_assigned_ids = set()
        
        for category_name, category_data in parsed.items():
            category_names.add(category_name)
            
            if not isinstance(category_data, dict):
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' must be an object"
                )
                continue
                
            # Check required fields
            if "definition" not in category_data:
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' missing 'definition' field"
                )
            elif not isinstance(category_data["definition"], str):
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' definition must be a string"
                )
                
            if "ids" not in category_data:
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' missing 'ids' field"
                )
            elif not isinstance(category_data["ids"], list):
                error_categories["validation_errors"].append(
                    f"Category '{category_name}' ids must be a list"
                )
            else:
                # Validate ids are strings and collect them
                category_ids = category_data["ids"]
                for idx, id_val in enumerate(category_ids):
                    if not isinstance(id_val, str):
                        error_categories["validation_errors"].append(
                            f"Category '{category_name}' ids[{idx}] must be a string"
                        )
                    else:
                        if id_val not in expected_ids:
                            error_categories["completeness_errors"].append(
                                f"Category '{category_name}' contains invalid id {id_val}"
                            )
                        elif id_val in all_assigned_ids:
                            error_categories["completeness_errors"].append(
                                f"ID {id_val} appears in multiple categories"
                            )
                        else:
                            all_assigned_ids.add(id_val)

        # Check for missing assignments
        missing_ids = expected_ids - all_assigned_ids
        if missing_ids:
            error_categories["completeness_errors"].append(
                f"Missing assignments for ids: {sorted(missing_ids)}"
            )

        all_errors = sum(len(v) for v in error_categories.values())
        if all_errors == 0:
            return ValidationResult(ok=True, error_categories=error_categories)

        return ValidationResult(ok=False, error_categories=error_categories)

    def _retry_prompt(
        self, original_prompt: str, validation_result: ValidationResult, ctx: StageContext
    ) -> str:  # noqa: D401
        # Build human-readable error details from retry_ctx.error_categories
        error_details = create_retry_error_details(validation_result.error_categories)
        
        # Use the fixed retry prompt template
        retry_block = _RETRY_PROMPT_TEMPLATE.format(
            error_details=error_details,
            content_sections=""  # Not used in current template but required for format string
        )
        return f"{original_prompt}\n\n{retry_block}"

    async def _produce_result(
        self,
        seq: Sequence[str],
        raw_response: str,
        ctx: StageContext,
        attempts: int,
    ) -> ConsolidationStageResult:
        """Convert a valid raw response into a :class:`ConsolidationStageResult`."""

        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        # Extract consolidated taxonomies from the category structure
        taxonomies = [
            ConsolidatedTaxonomyDTO(
                name=category_name, 
                definition=category_data["definition"],
                original_ids=category_data["ids"]
            )
            for category_name, category_data in payload.items()
            if isinstance(category_data, dict) and "definition" in category_data and "ids" in category_data
        ]
        
        # Convert ids arrays to consolidation mapping
        consolidation_mapping = {}
        for category_name, category_data in payload.items():
            if isinstance(category_data, dict) and "ids" in category_data:
                for original_id in category_data["ids"]:
                    consolidation_mapping[original_id] = category_name

        return ConsolidationStageResult(
            taxonomies_consolidated=taxonomies,
            consolidation_mapping=consolidation_mapping,
        )

    async def _merge_split_results(
        self,
        seq_left: Sequence[Any],
        seq_right: Sequence[Any],
        res_left: ConsolidationStageResult,
        res_right: ConsolidationStageResult,
        ctx: StageContext,
        depth: int,
    ) -> ConsolidationStageResult:  # noqa: D401 – signature enforced by BaseStage
        """Merge two partial results coming from auto-split recursion."""

        # For consolidation, we typically don't expect splits since we're working with
        # two taxonomies as input, but we need to implement this for completeness
        
        # Merge taxonomies – keep order but de-duplicate by *name*.
        taxonomy_by_name: Dict[str, ConsolidatedTaxonomyDTO] = {}
        for t in res_left.taxonomies_consolidated + res_right.taxonomies_consolidated:
            if t.name in taxonomy_by_name:
                # If duplicate names, merge the original_ids
                existing = taxonomy_by_name[t.name]
                merged_ids = list(set(existing.original_ids + t.original_ids))
                taxonomy_by_name[t.name] = ConsolidatedTaxonomyDTO(
                    name=t.name,
                    definition=t.definition,  # Use the latest definition
                    original_ids=merged_ids
                )
            else:
                taxonomy_by_name[t.name] = t

        # Merge consolidation mappings
        consolidation_mapping = dict(res_left.consolidation_mapping)
        consolidation_mapping.update(res_right.consolidation_mapping)

        return ConsolidationStageResult(
            taxonomies_consolidated=list(taxonomy_by_name.values()),
            consolidation_mapping=consolidation_mapping
        ) 