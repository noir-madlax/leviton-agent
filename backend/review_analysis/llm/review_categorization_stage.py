from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import List, Tuple, Set

from core.llm_taxonomy_pipeline.categorization_base import (
    CategorizationStage,
    CategorizationStageContext as _BaseCtx,
)

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

    # _validate, _retry_prompt, _produce_result, _merge_split_results are
    # provided by the generic base-class – no overrides needed.

    # Only splitting behaviour is reused from base. If desired we could
    # customise, but the default half-split is appropriate. 