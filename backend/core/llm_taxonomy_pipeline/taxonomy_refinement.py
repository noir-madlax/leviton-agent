"""Refinement stage implementation for the generic LLM-powered taxonomy pipeline.

This module defines a *RefinementStage* that takes existing product assignments
across all subcategories and reassigns products to subcategories that match
STRICTLY BETTER than their current assignment.

The stage is built on the generic :class:`BaseStage` utilities which already
provide *attempt / retry / auto-split / persistence* mechanics.  The only
responsibilities left here are:

• Prompt construction with taxonomies and current assignments.
• Response validation & parsing.
• Retry-prompt construction given a structured *retry-context*.
• Collating split-results back together.

The expected LLM output **must** be a JSON object of the following shape::

    {
      "P_1": "S_2",
      "P_5": "S_0"
    }

OR if no products need reassignment::

    {}

Each key represents a product ID that needs reassignment, and each value represents
the new subcategory ID. Only products that need reassignment should be included.
If no products need reassignment, an empty JSON object should be returned.
"""

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any, Dict, List, Sequence

from core.utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from product_segment.llm.taxonomy_pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)

__all__ = [
    "RefinementStageResult",
    "RefinementStageContext",
    "RefinementStage",
]

# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class RefinementStageContext(StageContext):
    """Context for taxonomy refinement stage containing taxonomies and current assignments."""
    
    taxonomies: list[TaxonomyDTO]
    current_assignments: dict[int, str]  # product_id -> taxonomy_name
    input_texts: list[str]  # product descriptions indexed by product_id


@dataclass(slots=True, frozen=True)
class RefinementStageResult(StageResultBase):
    """Result returned by the refinement stage."""
    
    reassignments: dict[int, str]  # product_id -> new_taxonomy_name

# ---------------------------------------------------------------------------
# Fixed prompt templates
# ---------------------------------------------------------------------------
# The stage uses fixed prompt templates from the prompts directory to ensure
# consistency across all refinement operations.
# ---------------------------------------------------------------------------

# Path to prompt template files
_PROMPTS_DIR = Path(__file__).parent.parent / "prompts"
_REFINE_PROMPT_PATH = _PROMPTS_DIR / "taxonomy_refinement_prompt_v0.txt"
_RETRY_PROMPT_PATH = _PROMPTS_DIR / "shared_retry_prompt_v0.txt"

# Load prompt templates at module level
try:
    with open(_REFINE_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _REFINE_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required prompt template not found: {_REFINE_PROMPT_PATH}")

try:
    with open(_RETRY_PROMPT_PATH, 'r', encoding='utf-8') as f:
        _RETRY_PROMPT_TEMPLATE = f.read()
except FileNotFoundError:
    raise RuntimeError(f"Required retry template not found: {_RETRY_PROMPT_PATH}")


# ---------------------------------------------------------------------------
# RefinementStage implementation
# ---------------------------------------------------------------------------


class RefinementStage(BaseStage):
    """Concrete taxonomy-refinement stage built on :class:`BaseStage`."""

    # --------------------- BaseStage abstract hooks -------------------------

    async def _build_prompt(self, ctx: RefinementStageContext) -> str:  # noqa: D401
        """Render the fixed prompt template with subcategories and product assignments."""

        # Build subcategories section with S_* IDs
        subcategories_lines = []
        taxonomy_id_map = {}  # taxonomy_name -> S_id
        
        for i, taxonomy in enumerate(ctx.taxonomies):
            s_id = f"S_{i}"
            taxonomy_id_map[taxonomy.name] = s_id
            subcategories_lines.append(f"{s_id}: {taxonomy.name}")
            subcategories_lines.append(f"Definition: {taxonomy.definition}")
            subcategories_lines.append("")  # Empty line for readability
        
        subcategories_section = "\n".join(subcategories_lines)
        
        # Build products section with P_* IDs and current assignments
        products_lines = []
        
        for i, text in enumerate(ctx.input_texts):
            p_id = f"P_{i}"
            current_taxonomy_name = ctx.current_assignments.get(i, "UNASSIGNED")
            current_s_id = taxonomy_id_map.get(current_taxonomy_name, "UNKNOWN")
            
            products_lines.append(f"{p_id}: {text} → {current_s_id} ({current_taxonomy_name})")
        
        products_section = "\n".join(products_lines)
        
        # Combine template with sections
        full_prompt = f"{_REFINE_PROMPT_TEMPLATE}\n\n**SUBCATEGORIES:**\n{subcategories_section}\n**PRODUCTS:**\n{products_section}"
        
        return full_prompt

    def _validate(
        self, raw_response: str, ctx: RefinementStageContext
    ) -> ValidationResult:
        """Validate and (optionally) return retry-context."""

        # Build valid product and subcategory ID sets
        valid_product_ids = {f"P_{i}" for i in range(len(ctx.input_texts))}
        valid_subcategory_ids = {f"S_{i}" for i in range(len(ctx.taxonomies))}
        
        # Build taxonomy name to S_id mapping for validation
        taxonomy_id_map = {taxonomy.name: f"S_{i}" for i, taxonomy in enumerate(ctx.taxonomies)}

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
            
            # Check if product is being reassigned to its current category (should not happen)
            product_idx = int(product_id[2:])  # Extract index from P_*
            current_taxonomy_name = ctx.current_assignments.get(product_idx)
            current_s_id = taxonomy_id_map.get(current_taxonomy_name)
            
            if subcategory_id == current_s_id:
                error_categories["validation_errors"].append(
                    f"Product '{product_id}' is assigned to its current subcategory '{subcategory_id}'"
                )

        all_errors = sum(len(v) for v in error_categories.values())
        if all_errors == 0:
            return ValidationResult(ok=True, error_categories=error_categories)

        return ValidationResult(ok=False, error_categories=error_categories)

    def _retry_prompt(
        self, original_prompt: str, validation_result: ValidationResult, ctx: RefinementStageContext
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
        raw_response: str,
        ctx: RefinementStageContext,
        attempts: int,
    ) -> RefinementStageResult:
        """Convert a valid raw response into a :class:`RefinementStageResult`."""

        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        # Convert P_* and S_* IDs back to integer indices and taxonomy names
        reassignments = {}
        
        for product_id, subcategory_id in payload.items():
            # Extract product index from P_*
            product_idx = int(product_id[2:])
            
            # Extract subcategory index from S_* and get taxonomy name
            subcategory_idx = int(subcategory_id[2:])
            new_taxonomy_name = ctx.taxonomies[subcategory_idx].name
            
            reassignments[product_idx] = new_taxonomy_name

        return RefinementStageResult(
            reassignments=reassignments,
        )

    async def _merge_split_results(
        self,
        res_left: RefinementStageResult,
        res_right: RefinementStageResult,
        ctx_left: RefinementStageContext,
        ctx_right: RefinementStageContext,
        depth: int,
    ) -> RefinementStageResult:  # noqa: D401 – signature enforced by BaseStage
        """Merge two partial results coming from auto-split recursion."""

        # Merge reassignments - adjust indices for right side to account for offset
        reassignments = dict(res_left.reassignments)
        left_size = len(ctx_left.input_texts)
        
        # Right side reassignments need to be offset by the size of left sequence
        for idx, taxonomy_name in res_right.reassignments.items():
            reassignments[idx + left_size] = taxonomy_name

        return RefinementStageResult(
            reassignments=reassignments
        )

    def _split_context(
        self, ctx: RefinementStageContext, depth: int
    ) -> tuple[RefinementStageContext, RefinementStageContext]:
        """Split refinement context into two parts for recursive processing."""
        
        if len(ctx.input_texts) <= 1:
            raise NotImplementedError("Cannot split context with single text")
        
        mid = len(ctx.input_texts) // 2
        
        # Split input texts and adjust assignments for each side
        left_assignments = {}
        right_assignments = {}
        
        for i in range(len(ctx.input_texts)):
            if i < mid:
                left_assignments[i] = ctx.current_assignments.get(i)
            else:
                # Adjust index for right side (starts from 0)
                right_assignments[i - mid] = ctx.current_assignments.get(i)
        
        ctx_left = RefinementStageContext(
            product_category=ctx.product_category,
            storage=ctx.storage,
            taxonomies=ctx.taxonomies,
            current_assignments=left_assignments,
            input_texts=ctx.input_texts[:mid]
        )
        
        ctx_right = RefinementStageContext(
            product_category=ctx.product_category,
            storage=ctx.storage,
            taxonomies=ctx.taxonomies,
            current_assignments=right_assignments,
            input_texts=ctx.input_texts[mid:]
        )
        
        return ctx_left, ctx_right 