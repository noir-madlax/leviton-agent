"""Refinement stage implementation for the generic LLM-powered taxonomy pipeline.

This module defines a *RefinementStage* that categorises all products into the most
appropriate subcategories from the provided taxonomy.

The stage is built on the generic :class:`BaseStage` utilities which already
provide *attempt / retry / auto-split / persistence* mechanics.  The only
responsibilities left here are:

• Prompt construction with taxonomies and products.
• Response validation & parsing.
• Retry-prompt construction given a structured *retry-context*.
• Collating split-results back together.

The expected LLM output **must** be a JSON object of the following shape::

    {
      "P_0": "S_0",
      "P_1": "S_1",
      "P_2": "OUT_OF_SCOPE",
      "P_3": "S_2"
    }

Each key represents a product ID, and each value represents the assigned subcategory ID.
All products must be included in the output.
"""

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Dict, List

from core.utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from core.llm_taxonomy_pipeline.pipeline_stage import (
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)
from core.llm_taxonomy_pipeline.refinement_base import (
    RefinementStage as BaseRefinementStage,
)

__all__ = [
    "ProductRefinementStageResult",
    "ProductRefinementStageContext",
    "ProductRefinementStage",
]

# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------

# Domain-specific context/result matching existing tests

@dataclass(slots=True, frozen=True)
class RefinementStageContext(StageContext):
    """Context for product-segment taxonomy refinement."""

    taxonomies: list[TaxonomyDTO]
    input_texts: list[str]


@dataclass(slots=True, frozen=True)
class RefinementStageResult(StageResultBase):
    """Result payload mapping product index → taxonomy name."""

    assignments: dict[int, str]

# Product-specific aliases for consistency
ProductRefinementStageContext = RefinementStageContext
ProductRefinementStageResult = RefinementStageResult

# ---------------------------------------------------------------------------
# Fixed prompt templates
# ---------------------------------------------------------------------------
# The stage uses fixed prompt templates from the prompts directory to ensure
# consistency across all refinement operations.
# ---------------------------------------------------------------------------

# Path to prompt template files
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_FINAL_ASSIGN_PROMPT_PATH = _PROMPTS_DIR / "taxonomy_refinement_prompt_v0.txt"
_RETRY_PROMPT_PATH = (
    Path(__file__).resolve().parents[2] / "core" / "prompts" / "shared_retry_prompt_v0.txt"
)

# Load prompt templates at module level
try:
    with open(_FINAL_ASSIGN_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _REFINE_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_FINAL_ASSIGN_PROMPT_PATH}")

try:
    with open(_RETRY_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _RETRY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required retry template not found: {_RETRY_PROMPT_PATH}")


# ---------------------------------------------------------------------------
# RefinementStage implementation
# ---------------------------------------------------------------------------


class ProductRefinementStage(BaseRefinementStage):
    """Concrete taxonomy-refinement stage built on :class:`BaseStage`."""

    # --------------------- BaseStage abstract hooks -------------------------

    async def _build_prompt(self, ctx: ProductRefinementStageContext) -> str:  # noqa: D401
        """Render the fixed prompt template with subcategories and products."""

        # Build subcategories section with S_* IDs
        subcategories_lines = []
        for i, taxonomy in enumerate(ctx.taxonomies):
            s_id = f"S_{i}"
            subcategories_lines.append(f"[{s_id}] {taxonomy.name}: {taxonomy.definition}")
        
        subcategories_section = "\n".join(subcategories_lines)
        
        # Build products section with P_* IDs
        products_lines = []
        for i, text in enumerate(ctx.input_texts):
            p_id = f"P_{i}"
            products_lines.append(f"[{p_id}] {text}")
        
        products_section = "\n".join(products_lines)
        
        # Render template with all placeholders using replace to avoid JSON conflicts
        full_prompt = _REFINE_PROMPT_TEMPLATE.replace("{{product_category}}", ctx.product_category)
        full_prompt = full_prompt.replace("{{subcategories_section}}", subcategories_section)
        full_prompt = full_prompt.replace("{{products_section}}", products_section)
        
        return full_prompt

    def _validate(
        self, raw_response: str, ctx: ProductRefinementStageContext
    ) -> ValidationResult:
        """Validate and (optionally) return retry-context."""

        # Build valid product and subcategory ID sets
        valid_product_ids = {f"P_{i}" for i in range(len(ctx.input_texts))}
        valid_subcategory_ids = {f"S_{i}" for i in range(len(ctx.taxonomies))} | {"OUT_OF_SCOPE"}

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

        # Validate each assignment
        for product_id, subcategory_id in parsed.items():
            # Validate product ID format and existence
            if not isinstance(product_id, str):
                error_categories["validation_errors"].append(
                    f"Product ID must be a string, got {type(product_id).__name__}"
                )
                continue
                
            if product_id not in valid_product_ids:
                error_categories["completeness_errors"].append(
                    f"Invalid product ID '{product_id}'"
                )
                continue
            
            # Validate subcategory ID format and existence
            if not isinstance(subcategory_id, str):
                error_categories["validation_errors"].append(
                    f"Subcategory ID for '{product_id}' must be a string, got {type(subcategory_id).__name__}"
                )
                continue
                
            if subcategory_id not in valid_subcategory_ids:
                error_categories["completeness_errors"].append(
                    f"Invalid subcategory ID '{subcategory_id}' for product '{product_id}'"
                )
                continue

        all_errors = sum(len(v) for v in error_categories.values())
        if all_errors == 0:
            return ValidationResult(ok=True, error_categories=error_categories)

        return ValidationResult(ok=False, error_categories=error_categories)

    def _retry_prompt(
        self, original_prompt: str, validation_result: ValidationResult, ctx: ProductRefinementStageContext
    ) -> str:  # noqa: D401
        # Build human-readable error details from retry_ctx.error_categories
        error_details = create_retry_error_details(validation_result.error_categories)

        # Use the fixed retry prompt template
        retry_block = _RETRY_PROMPT_TEMPLATE.replace("{{error_details}}", error_details)
        return f"{original_prompt}\n\n{retry_block}"

    async def _produce_result(
        self,
        raw_response: str,
        ctx: ProductRefinementStageContext,
        attempts: int,
    ) -> ProductRefinementStageResult:
        """Convert a valid raw response into a :class:`ProductRefinementStageResult`."""

        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        # Convert P_* and S_* IDs back to integer indices and taxonomy names
        assignments = {}
        
        for product_id, subcategory_id in payload.items():
            # Extract product index from P_*
            product_idx = int(product_id[2:])
            
            if subcategory_id == "OUT_OF_SCOPE":
                assignments[product_idx] = "OUT_OF_SCOPE"
            else:
                # Extract subcategory index from S_* and get taxonomy name
                subcategory_idx = int(subcategory_id[2:])
                taxonomy_name = ctx.taxonomies[subcategory_idx].name
                assignments[product_idx] = taxonomy_name

        return ProductRefinementStageResult(
            assignments=assignments,
        )

    async def _merge_split_results(
        self,
        res_left: ProductRefinementStageResult,
        res_right: ProductRefinementStageResult,
        ctx_left: ProductRefinementStageContext,
        ctx_right: ProductRefinementStageContext,
        depth: int,
    ) -> ProductRefinementStageResult:  # noqa: D401 – signature enforced by BaseStage
        """Merge two partial results coming from auto-split recursion."""

        # Merge assignments - adjust indices for right side to account for offset
        assignments = dict(res_left.assignments)
        left_size = len(ctx_left.input_texts)
        
        # Right side assignments need to be offset by the size of left sequence
        for idx, taxonomy_name in res_right.assignments.items():
            assignments[idx + left_size] = taxonomy_name

        return ProductRefinementStageResult(
            assignments=assignments
        )

    def _split_context(
        self, ctx: ProductRefinementStageContext, depth: int
    ) -> tuple[ProductRefinementStageContext, ProductRefinementStageContext]:
        """Split refinement context into two parts for recursive processing."""
        
        if len(ctx.input_texts) <= 1:
            raise NotImplementedError("Cannot split context with single text")
        
        mid = len(ctx.input_texts) // 2
        
        # Split input texts
        left_input_texts = ctx.input_texts[:mid]
        right_input_texts = ctx.input_texts[mid:]
        
        ctx_left = ProductRefinementStageContext(
            product_category=ctx.product_category,
            storage=ctx.storage,
            taxonomies=ctx.taxonomies,
            input_texts=left_input_texts
        )

        ctx_right = ProductRefinementStageContext(
            product_category=ctx.product_category,
            storage=ctx.storage,
            taxonomies=ctx.taxonomies,
            input_texts=right_input_texts
        )

        return ctx_left, ctx_right 