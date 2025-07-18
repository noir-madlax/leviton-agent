from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Set, Dict, Any
import json

from core.llm_taxonomy_pipeline.categorization_base import (
    CategorizationStage,
    CategorizationStageContext as _BaseCtx,
    CategorizationStageResult,
)
from core.utils.llm_utils import ValidationResult, extract_json, create_retry_error_details
from core.llm_taxonomy_pipeline.pipeline_stage import TaxonomyDTO

# ---------------------------------------------------------------------------
# Fixed prompt templates
# ---------------------------------------------------------------------------
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_CATEGORISE_PROMPT_PATH = _PROMPTS_DIR / "review_aspects_categorization_prompt_v0.txt"

# Shared retry template lives under backend/core/prompts
_RETRY_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "core" / "prompts" / "shared_retry_prompt_v0.txt"
)

# Load prompt templates at module import – fail-fast on missing files
try:
    with open(_CATEGORISE_PROMPT_PATH, "r", encoding="utf-8") as f:
        _CATEGORISE_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_CATEGORISE_PROMPT_PATH}")

if not _RETRY_PROMPT_PATH.exists():
    raise RuntimeError(f"Required retry template not found: {_RETRY_PROMPT_PATH}")

with open(_RETRY_PROMPT_PATH, "r", encoding="utf-8") as f:
    _RETRY_PROMPT_TEMPLATE = f.read()

# ---------------------------------------------------------------------------
# Context dataclass
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ReviewCategorizationContext(_BaseCtx):
    """Extended context for review-aspect categorisation."""

    aspect_type: str  # e.g. "physical", "performance", "use case"
    aspect_context: str  # Human-readable description of the aspect domain
    input_description: str  # Short description of input line format
    product_categories: Set[str]  # Used for contextual hints

    aspects: List[Tuple[str, str]]  # Override type so mypy sees the same field


# ---------------------------------------------------------------------------
# Enhanced result dataclass to include aspect assignments
# ---------------------------------------------------------------------------

@dataclass(slots=True, frozen=True)
class ReviewCategorizationResult(CategorizationStageResult):
    """Enhanced result that includes aspect-to-category assignments."""
    
    assignments_initial: Dict[str, str]  # aspect_id -> category_name


# ---------------------------------------------------------------------------
# Stage implementation
# ---------------------------------------------------------------------------

class ReviewCategorizationStage(CategorizationStage):
    """Concrete aspect categorisation stage for *review_analysis* domain."""

    # We simply wire the fixed templates into the generic base-class

    def __init__(self) -> None:
        super().__init__(
            categorise_prompt_template=_CATEGORISE_PROMPT_TEMPLATE,
            retry_prompt_template=_RETRY_PROMPT_TEMPLATE,
        )

    # ----------------------- Base hooks ----------------------------------

    async def _build_prompt(self, ctx: ReviewCategorizationContext) -> str:  # noqa: D401
        # Compose dynamic product context
        product_context_block = ""
        if ctx.product_categories:
            cats_sorted = ", ".join(sorted(ctx.product_categories))
            product_context_block = (
                f"\n\n**PRODUCT CATEGORIES IN DATASET:** {cats_sorted}\n"
                f"Consider how {ctx.aspect_type} aspects relate to customer needs across "
                f"these {len(ctx.product_categories)} product categories."
            )

        # Render template placeholders
        rendered_template = (
            _CATEGORISE_PROMPT_TEMPLATE
            .replace("{{aspect_type}}", ctx.aspect_type)
            .replace("{{aspect_context}}", ctx.aspect_context)
            .replace("{{input_description}}", ctx.input_description)
            .replace("{{product_context}}", product_context_block)
        )

        # Append the list of aspects below the template
        aspect_lines = "\n".join(f"[{aid}] {desc}" for aid, desc in ctx.aspects)
        return f"{rendered_template}\n\n{aspect_lines}"

    def _validate(self, raw_response: str, ctx: ReviewCategorizationContext) -> ValidationResult:
        """Validate response with aspect ID assignment similar to product extraction."""
        
        expected_ids = {aid for aid, _ in ctx.aspects}
        
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

        # Validate each category
        all_assigned_ids = set()
        
        for category_name, category_data in parsed.items():
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
                # Validate ids and collect them
                category_ids = category_data["ids"]
                for idx, id_val in enumerate(category_ids):
                    if not isinstance(id_val, (int, str)):
                        error_categories["validation_errors"].append(
                            f"Category '{category_name}' ids[{idx}] must be an integer or string"
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
        self, original_prompt: str, validation_result: ValidationResult, ctx: ReviewCategorizationContext, previous_response: str
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
        ctx: ReviewCategorizationContext,
        attempts: int,
    ) -> ReviewCategorizationResult:
        """Convert a valid raw response into a ReviewCategorizationResult with assignments."""

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
                for aspect_id in category_data["ids"]:
                    assignments[str(aspect_id)] = category_name

        return ReviewCategorizationResult(
            taxonomies_categorised=taxonomies,
            assignments_initial=assignments,
        )

    async def _merge_split_results(
        self,
        res_left: ReviewCategorizationResult,
        res_right: ReviewCategorizationResult,
        ctx_left: ReviewCategorizationContext,
        ctx_right: ReviewCategorizationContext,
        depth: int,
    ) -> ReviewCategorizationResult:  # noqa: D401 – signature enforced by BaseStage
        """Merge two partial results coming from auto-split recursion."""

        # Merge taxonomies – keep order but de-duplicate by *name*.
        taxonomy_by_name: Dict[str, TaxonomyDTO] = {}
        for t in res_left.taxonomies_categorised + res_right.taxonomies_categorised:
            taxonomy_by_name.setdefault(t.name, t)

        # Merge assignments - no offset needed since aspect IDs are strings
        assignments = dict(res_left.assignments_initial)
        assignments.update(res_right.assignments_initial)

        return ReviewCategorizationResult(
            taxonomies_categorised=list(taxonomy_by_name.values()),
            assignments_initial=assignments,
        )

    def _split_context(
        self, ctx: ReviewCategorizationContext, depth: int
    ) -> tuple[ReviewCategorizationContext, ReviewCategorizationContext]:
        """Split categorization context into two parts for recursive processing."""
        
        if len(ctx.aspects) <= 1:
            raise NotImplementedError("Cannot split context with single aspect")
        
        mid = len(ctx.aspects) // 2
        
        ctx_left = ReviewCategorizationContext(
            product_category=ctx.product_category,
            aspect_type=ctx.aspect_type,
            aspect_context=ctx.aspect_context,
            input_description=ctx.input_description,
            product_categories=ctx.product_categories,
            aspects=ctx.aspects[:mid]
        )

        ctx_right = ReviewCategorizationContext(
            product_category=ctx.product_category,
            aspect_type=ctx.aspect_type,
            aspect_context=ctx.aspect_context,
            input_description=ctx.input_description,
            product_categories=ctx.product_categories,
            aspects=ctx.aspects[mid:]
        )

        return ctx_left, ctx_right 