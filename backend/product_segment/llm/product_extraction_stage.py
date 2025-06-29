"""Extraction stage implementation for the generic LLM-powered taxonomy pipeline.

This module defines an *ExtractionStage* that converts a **sequence of raw
texts** (e.g. product reviews, tickets …) into two deliverables:

1. *Provisional* taxonomies – every entry captures ``name`` and ``definition``.
2. Initial assignments – mapping from *input index* → *taxonomy name*.

The stage is built on the generic :class:`BaseStage` utilities which already
provide *attempt / retry / auto-split / persistence* mechanics.  The only
responsibilities left here are:

• Prompt construction.
• Response validation & parsing.
• Retry-prompt construction given a structured *retry-context*.
• Collating split-results back together.

The expected LLM output **must** be a JSON object of the following shape::

    {
      "Meaningful Subcategory 1": {
        "definition": "..., e.g. <specific product subtypes>",
        "ids": [0, 5, 12]
      },
      "Meaningful Subcategory 2": {
        "definition": "..., e.g. ...",
        "ids": [1, 8, 15]
      },
      "OUT_OF_SCOPE": {
        "definition": "Products that clearly don't belong to {product_category}, e.g. ...",
        "ids": [3, 9]
      }
    }

Each top-level key represents a taxonomy category name. Each category must have
a "definition" field and an "ids" field containing an array of product indices.
Each index from ``0`` … ``len(texts)-1`` must appear **exactly once** across
all "ids" arrays with no duplicates or missing indices.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from core.utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from core.llm_taxonomy_pipeline.pipeline_stage import BaseStage, StageContext, StageResultBase, TaxonomyDTO
from core.llm_taxonomy_pipeline.extraction_base import (
    ExtractionStage as BaseExtractionStage,
    ExtractionStageContext,
    ExtractionStageResult,
)

# Product-specific aliases for consistency
ProductExtractionStageContext = ExtractionStageContext
ProductExtractionStageResult = ExtractionStageResult

__all__ = [
    "TaxonomyDTO",
    "ProductExtractionStageResult",
    "ProductExtractionStageContext", 
    "ProductExtractionStage",
]

# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------

# Use generic context/result from core base

# ---------------------------------------------------------------------------
# Prompt helpers & retry-utilities
# ---------------------------------------------------------------------------





# ---------------------------------------------------------------------------
# Fixed prompt templates
# ---------------------------------------------------------------------------
# The stage uses fixed prompt templates from the prompts directory to ensure
# consistency across all extraction operations.
# ---------------------------------------------------------------------------

# Path to prompt template files: product_segment/llm/prompts
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_EXTRACT_PROMPT_PATH = _PROMPTS_DIR / "taxonomy_extraction_prompt_v0.txt"

# Shared retry template now lives under backend/core/prompts
_RETRY_PROMPT_PATH = (
    Path(__file__).resolve().parents[2]  # points to .../backend
    / "core" / "prompts" / "shared_retry_prompt_v0.txt"
)

# Load prompt templates at module level
try:
    with open(_EXTRACT_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _EXTRACT_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_EXTRACT_PROMPT_PATH}")

if not _RETRY_PROMPT_PATH.exists():
    raise RuntimeError(f"Required retry template not found: {_RETRY_PROMPT_PATH}")

with open(_RETRY_PROMPT_PATH, "r", encoding="utf-8") as f:
    _RETRY_PROMPT_TEMPLATE = f.read()


# ---------------------------------------------------------------------------
# ExtractionStage implementation
# ---------------------------------------------------------------------------


class ProductExtractionStage(BaseExtractionStage):
    """Concrete taxonomy-extraction stage built on :class:`BaseStage`."""

    # --------------------- BaseStage abstract hooks -------------------------

    async def _build_prompt(self, ctx: ProductExtractionStageContext) -> str:  # noqa: D401
        """Render the fixed prompt template and append the input lines."""

        # Replace placeholder using double‐brace syntax to avoid escaping JSON braces
        rendered_template = _EXTRACT_PROMPT_TEMPLATE.replace("{{product_category}}", ctx.product_category)

        input_lines = "\n".join(f"[{i}] {txt}" for i, txt in enumerate(ctx.input_texts))
        return f"{rendered_template}\n\n{input_lines}"

    def _validate(
        self, raw_response: str, ctx: ProductExtractionStageContext
    ) -> ValidationResult:
        """Validate and (optionally) return retry-context."""

        expected_ids = {str(i) for i in range(len(ctx.input_texts))}

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

        # Validate each taxonomy category
        taxonomy_names = set()
        all_assigned_ids = set()
        
        for category_name, category_data in parsed.items():
            taxonomy_names.add(category_name)
            
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
                # Validate ids are integers and collect them
                category_ids = category_data["ids"]
                for idx, id_val in enumerate(category_ids):
                    if not isinstance(id_val, int):
                        error_categories["validation_errors"].append(
                            f"Category '{category_name}' ids[{idx}] must be an integer"
                        )
                    else:
                        str_id = str(id_val)
                        if str_id not in expected_ids:
                            error_categories["completeness_errors"].append(
                                f"Category '{category_name}' contains invalid id {id_val}"
                            )
                        elif str_id in all_assigned_ids:
                            error_categories["completeness_errors"].append(
                                f"ID {id_val} appears in multiple categories"
                            )
                        else:
                            all_assigned_ids.add(str_id)

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
        self, original_prompt: str, validation_result: ValidationResult, ctx: ProductExtractionStageContext
    ) -> str:  # noqa: D401
        # Build human-readable error details from retry_ctx.error_categories
        error_details = create_retry_error_details(validation_result.error_categories)

        # Use the fixed retry prompt template
        retry_block = _RETRY_PROMPT_TEMPLATE.replace("{{error_details}}", error_details)
        retry_block = retry_block.replace("{{content_sections}}", "")
        return f"{original_prompt}\n\n{retry_block}"

    async def _produce_result(
        self,
        raw_response: str,
        ctx: ProductExtractionStageContext,
        attempts: int,
    ) -> ProductExtractionStageResult:
        """Convert a valid raw response into an :class:`ProductExtractionStageResult`."""

        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        # Extract taxonomies from the category structure
        taxonomies = [
            TaxonomyDTO(name=category_name, definition=category_data["definition"])
            for category_name, category_data in payload.items()
            if isinstance(category_data, dict) and "definition" in category_data
        ]
        
        # Convert ids arrays to assignments mapping
        assignments = {}
        for category_name, category_data in payload.items():
            if isinstance(category_data, dict) and "ids" in category_data:
                for product_id in category_data["ids"]:
                    assignments[int(product_id)] = category_name

        return ProductExtractionStageResult(
            taxonomies_extracted=taxonomies,
            assignments_initial=assignments,
        )

    async def _merge_split_results(
        self,
        res_left: ProductExtractionStageResult,
        res_right: ProductExtractionStageResult,
        ctx_left: ProductExtractionStageContext,
        ctx_right: ProductExtractionStageContext,
        depth: int,
    ) -> ProductExtractionStageResult:  # noqa: D401 – signature enforced by BaseStage
        """Merge two partial results coming from auto-split recursion."""

        # Merge taxonomies – keep order but de-duplicate by *name*.
        taxonomy_by_name: Dict[str, TaxonomyDTO] = {}
        for t in res_left.taxonomies_extracted + res_right.taxonomies_extracted:
            taxonomy_by_name.setdefault(t.name, t)

        # Merge assignments - adjust indices for right side to account for offset
        assignments = dict(res_left.assignments_initial)
        left_size = len(ctx_left.input_texts)
        
        # Right side assignments need to be offset by the size of left sequence
        for idx, category_name in res_right.assignments_initial.items():
            assignments[idx + left_size] = category_name

        return ProductExtractionStageResult(
            taxonomies_extracted=list(taxonomy_by_name.values()),
            assignments_initial=assignments
        )

    def _split_context(
        self, ctx: ProductExtractionStageContext, depth: int
    ) -> tuple[ProductExtractionStageContext, ProductExtractionStageContext]:
        """Split extraction context into two parts for recursive processing."""
        
        if len(ctx.input_texts) <= 1:
            raise NotImplementedError("Cannot split context with single text")
        
        mid = len(ctx.input_texts) // 2
        
        ctx_left = ProductExtractionStageContext(
            product_category=ctx.product_category,
            storage=ctx.storage,
            input_texts=ctx.input_texts[:mid]
        )

        ctx_right = ProductExtractionStageContext(
            product_category=ctx.product_category,
            storage=ctx.storage,
            input_texts=ctx.input_texts[mid:]
        )

        return ctx_left, ctx_right
