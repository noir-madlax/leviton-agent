"""Refinement stage implementation for review aspect categorization.

This module defines a *ReviewRefinementStage* that takes existing aspect assignments
across all categories and reassigns aspects to categories that match
STRICTLY BETTER than their current assignment.

The stage is built on the generic :class:`BaseStage` utilities which already
provide *attempt / retry / auto-split / persistence* mechanics.  The only
responsibilities left here are:

• Prompt construction with categories and current assignments.
• Response validation & parsing.
• Retry-prompt construction given a structured *retry-context*.
• Collating split-results back together.

The expected LLM output **must** be a JSON object of the following shape::

    {
      "1": "C_2",
      "5": "C_0",
      "12": "OUT_OF_SCOPE"
    }

OR if no aspects need reassignment::

    {}

Each key represents an aspect index (integer as string) that needs reassignment, 
and each value represents the new category ID. Only aspects that need reassignment 
should be included. If no aspects need reassignment, an empty JSON object should be returned.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from core.utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from core.llm_taxonomy_pipeline.pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)

__all__ = [
    "ReviewRefinementStageContext",
    "ReviewRefinementStageResult", 
    "ReviewRefinementStage",
]

# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ReviewRefinementStageContext(StageContext):
    """Context for review aspect refinement."""

    aspect_type: str  # e.g. "physical", "performance", "use case"
    aspect_context: str  # Human-readable description of the aspect domain
    categories: List[TaxonomyDTO]  # Available categories for assignment
    aspects: List[str]  # List of aspect descriptions (indexed by position)
    original_categories: Optional[List[Optional[str]]] = None  # Original categories for each aspect (None for use cases or when not available)
@dataclass(slots=True, frozen=True)
class ReviewRefinementStageResult(StageResultBase):
    """Result payload mapping aspect_index → new category name."""

    reassignments: Dict[int, str]  # aspect_index -> new_category_name


# ---------------------------------------------------------------------------
# Fixed prompt templates
# ---------------------------------------------------------------------------

# Path to prompt template files
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_REFINEMENT_PROMPT_PATH = _PROMPTS_DIR / "review_aspects_refinement_prompt_v0.txt"
_RETRY_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "core" / "prompts" / "shared_retry_prompt_v0.txt"
)

# Load prompt templates at module level
try:
    with open(_REFINEMENT_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _REFINEMENT_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_REFINEMENT_PROMPT_PATH}")

try:
    with open(_RETRY_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _RETRY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required retry template not found: {_RETRY_PROMPT_PATH}")


# ---------------------------------------------------------------------------
# ReviewRefinementStage implementation
# ---------------------------------------------------------------------------

class ReviewRefinementStage(BaseStage):
    """Concrete review aspect refinement stage built on :class:`BaseStage`."""

    # --------------------- BaseStage abstract hooks -------------------------

    async def _build_prompt(self, ctx: ReviewRefinementStageContext) -> str:  # noqa: D401
        """Render the fixed prompt template with categories and aspect assignments."""

        # Build categories section with C_* IDs
        categories_lines = []
        
        for i, category in enumerate(ctx.categories):
            c_id = f"C_{i}"
            categories_lines.append(f"[{c_id}] {category.name}: {category.definition}")
        
        categories_section = "\n".join(categories_lines)
        
        # Build aspects section with integer IDs
        formatted_aspects = []
        for i, description in enumerate(ctx.aspects):
            # For use aspect type, never combine category with description
            if ctx.aspect_type.lower() == "use":
                # Use cases don't have categories, use description as-is
                formatted_aspects.append(f"[{i}] {description}")
            elif ctx.original_categories and i < len(ctx.original_categories) and ctx.original_categories[i]:
                original_category = ctx.original_categories[i]
                # Format as "{category} - {description}"
                formatted_aspects.append(f"[{i}] {original_category} - {description}")
            else:
                # No category available, use description as-is
                formatted_aspects.append(f"[{i}] {description}")
        
        formatted_aspects = "\n".join(formatted_aspects)
        
        # Render template with all placeholders using replace to avoid JSON conflicts
        full_prompt = _REFINEMENT_PROMPT_TEMPLATE.replace("{{aspect_type}}", ctx.aspect_type)
        full_prompt = full_prompt.replace("{{product_category}}", ctx.product_category)
        full_prompt = full_prompt.replace("{{aspect_context}}", ctx.aspect_context)
        full_prompt = full_prompt.replace("{{categories_section}}", categories_section)
        full_prompt = full_prompt.replace("{{formatted_aspects}}", formatted_aspects)
        
        return full_prompt

    def _validate(
        self, raw_response: str, ctx: ReviewRefinementStageContext
    ) -> ValidationResult:
        """Validate and (optionally) return retry-context."""

        # Build valid aspect and category ID sets
        valid_aspect_ids = {str(i) for i in range(len(ctx.aspects))}
        valid_category_ids = {f"C_{i}" for i in range(len(ctx.categories))} | {"OUT_OF_SCOPE"}

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

        # Empty object is valid (no reassignments needed)
        if not parsed:
            return ValidationResult(ok=True, error_categories=error_categories)

        # Validate each reassignment
        for aspect_idx_str, category_id in parsed.items():
            # Validate aspect index format and existence
            if not isinstance(aspect_idx_str, str):
                error_categories["validation_errors"].append(
                    f"Aspect index must be a string, got {type(aspect_idx_str).__name__}"
                )
                continue
                
            if aspect_idx_str not in valid_aspect_ids:
                error_categories["completeness_errors"].append(
                    f"Invalid aspect index '{aspect_idx_str}'"
                )
                continue
            
            # Validate category ID format and existence
            if not isinstance(category_id, str):
                error_categories["validation_errors"].append(
                    f"Category ID for aspect '{aspect_idx_str}' must be a string, got {type(category_id).__name__}"
                )
                continue
                
            if category_id not in valid_category_ids:
                error_categories["completeness_errors"].append(
                    f"Invalid category ID '{category_id}' for aspect '{aspect_idx_str}'"
                )
                continue



        all_errors = sum(len(v) for v in error_categories.values())
        if all_errors == 0:
            return ValidationResult(ok=True, error_categories=error_categories)

        return ValidationResult(ok=False, error_categories=error_categories)

    def _retry_prompt(
        self, original_prompt: str, validation_result: ValidationResult, ctx: ReviewRefinementStageContext, previous_response: str
    ) -> str:  # noqa: D401
        # Build human-readable error details from validation_result.error_categories
        error_details = create_retry_error_details(validation_result.error_categories)

        # Include the previous response in the retry instructions
        previous_response_section = f"""
=== PREVIOUS RESPONSE (INCORRECT) ===
{previous_response}
=== END PREVIOUS RESPONSE ===

"""
        
        # Use the fixed retry prompt template with previous response
        retry_block = _RETRY_PROMPT_TEMPLATE.replace("{{error_details}}", error_details)
        return f"{original_prompt}\n\n{previous_response_section}{retry_block}"

    async def _produce_result(
        self,
        raw_response: str,
        ctx: ReviewRefinementStageContext,
        attempts: int,
    ) -> ReviewRefinementStageResult:
        """Convert a valid raw response into a :class:`ReviewRefinementStageResult`."""

        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        # Convert C_* IDs back to category names and aspect IDs to integers
        reassignments = {}
        
        for aspect_id_str, category_id in payload.items():
            aspect_idx = int(aspect_id_str)  # Convert string aspect ID to integer
            
            if category_id == "OUT_OF_SCOPE":
                reassignments[aspect_idx] = "OUT_OF_SCOPE"
            else:
                # Extract category index from C_* and get category name
                category_idx = int(category_id[2:])
                new_category_name = ctx.categories[category_idx].name
                reassignments[aspect_idx] = new_category_name

        return ReviewRefinementStageResult(
            reassignments=reassignments,
        )

    async def _merge_split_results(
        self,
        res_left: ReviewRefinementStageResult,
        res_right: ReviewRefinementStageResult,
        ctx_left: ReviewRefinementStageContext,
        ctx_right: ReviewRefinementStageContext,
        depth: int,
    ) -> ReviewRefinementStageResult:  # noqa: D401 – signature enforced by BaseStage
        """Merge two partial results coming from auto-split recursion."""

        # Merge reassignments - adjust indices for right side to account for offset
        reassignments = dict(res_left.reassignments)
        left_size = len(ctx_left.aspects)
        
        # Right side reassignments need to be offset by the size of left sequence
        for idx, category_name in res_right.reassignments.items():
            reassignments[idx + left_size] = category_name

        return ReviewRefinementStageResult(
            reassignments=reassignments
        )

    def _split_context(
        self, ctx: ReviewRefinementStageContext, depth: int
    ) -> tuple[ReviewRefinementStageContext, ReviewRefinementStageContext]:
        """Split refinement context into two parts for recursive processing."""
        
        if len(ctx.aspects) <= 1:
            raise NotImplementedError("Cannot split context with single aspect")
        
        mid = len(ctx.aspects) // 2
        
        # Split aspects and original categories
        left_aspects = ctx.aspects[:mid]
        right_aspects = ctx.aspects[mid:]
        
        left_original_categories = None
        right_original_categories = None
        if ctx.original_categories:
            left_original_categories = ctx.original_categories[:mid]
            right_original_categories = ctx.original_categories[mid:]
        
        ctx_left = ReviewRefinementStageContext(
            product_category=ctx.product_category,
            aspect_type=ctx.aspect_type,
            aspect_context=ctx.aspect_context,
            categories=ctx.categories,
            aspects=left_aspects,
            original_categories=left_original_categories,
        )

        ctx_right = ReviewRefinementStageContext(
            product_category=ctx.product_category,
            aspect_type=ctx.aspect_type,
            aspect_context=ctx.aspect_context,
            categories=ctx.categories,
            aspects=right_aspects,
            original_categories=right_original_categories,
        )

        return ctx_left, ctx_right 