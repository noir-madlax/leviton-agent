from __future__ import annotations

import abc
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Tuple

from ..utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from .pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)

__all__: list[str] = [
    "CategorizationStageContext",
    "CategorizationStageResult",
    "CategorizationStage",
]


@dataclass(slots=True, frozen=True)
class CategorizationStageContext(StageContext):
    """Context object for aspect categorisation stages.

    Parameters
    ----------
    aspects
        Sequence of ``(id, text)`` pairs that should be categorised.
        *id* **must** be a *string* that is unique inside the batch.
    """

    aspects: List[Tuple[str, str]]  # (aspect_id, description)


@dataclass(slots=True, frozen=True)
class CategorizationStageResult(StageResultBase):
    """Payload returned by a successful categorisation stage execution."""

    taxonomies_categorised: List[TaxonomyDTO]


class CategorizationStage(BaseStage, abc.ABC):
    """Abstract base-class for aspect categorisation stages.

    Concrete subclasses only need to implement *prompt rendering* and may
    optionally supply additional placeholder variables via
    :pyfunc:`_get_additional_template_vars`.  Validation, retry-prompt generation
    and result parsing are handled here.
    """

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def __init__(self, categorise_prompt_template: str, retry_prompt_template: str):
        self._categorise_prompt_template = categorise_prompt_template
        self._retry_prompt_template = retry_prompt_template

    @classmethod
    def load_templates(
        cls,
        prompts_dir: Path,
        categorise_filename: str,
        retry_filename: str = "shared_retry_prompt_v0.txt",
    ) -> tuple[str, str]:
        """Utility helper to load prompt templates from *prompts_dir*."""
        categorise_path = prompts_dir / categorise_filename
        retry_path = prompts_dir.parents[1] / "core" / "prompts" / retry_filename

        try:
            with open(categorise_path, "r", encoding="utf-8") as f:
                categorise_template = f.read()
        except FileNotFoundError:  # pragma: no cover – catastrophic configuration error
            raise RuntimeError(f"Required prompt template not found: {categorise_path}")

        try:
            with open(retry_path, "r", encoding="utf-8") as f:
                retry_template = f.read()
        except FileNotFoundError:  # pragma: no cover
            raise RuntimeError(f"Required retry template not found: {retry_path}")

        return categorise_template, retry_template

    # ------------------------------------------------------------------
    # Validation helpers
    # ------------------------------------------------------------------

    def _validate(self, raw_response: str, ctx: CategorizationStageContext) -> ValidationResult:  # noqa: D401
        """Validate the LLM response for aspect categorisation.

        Expected schema (pure JSON):

        {
          "Meaningful Category": {
            "definition": "Precise customer-centric description, e.g. ..."
          },
          "Another Category": {
            "definition": "..."
          }
        }

        A valid response is a *flat* JSON object where **each** key is a
        category name and the corresponding value is an object with a single
        field "definition" (string).  No other fields are allowed.  Any historic "ids" arrays are no longer supported.
        """

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

        # Structural sanity checks ------------------------------------------------
        if not isinstance(parsed, dict):
            error_categories["format_errors"].append("Top-level JSON must be an object")
            return ValidationResult(ok=False, error_categories=error_categories)

        if not parsed:
            error_categories["format_errors"].append("JSON object cannot be empty")
            return ValidationResult(ok=False, error_categories=error_categories)

        # Field-level validation --------------------------------------------------
        for cat_name, cat_data in parsed.items():
            if not isinstance(cat_data, dict):
                error_categories["validation_errors"].append(
                    f"Category '{cat_name}' must be an object"
                )
                continue

            # Mandatory definition ------------------------------------------------
            if "definition" not in cat_data:
                error_categories["validation_errors"].append(
                    f"Category '{cat_name}' missing 'definition' field"
                )
            elif not isinstance(cat_data["definition"], str):
                error_categories["validation_errors"].append(
                    f"Category '{cat_name}' definition must be a string"
                )

            # No other fields are allowed than 'definition'
            extra_fields = set(cat_data.keys()) - {"definition"}
            if extra_fields:
                error_categories["validation_errors"].append(
                    f"Category '{cat_name}' contains unexpected fields: {sorted(extra_fields)}"
                )

            # Reject any reserved category names (e.g. OUT_OF_SCOPE)
            if cat_name.strip().upper() == "OUT_OF_SCOPE":
                error_categories["validation_errors"].append(
                    "Category name 'OUT_OF_SCOPE' is reserved and not allowed"
                )

        all_errors = sum(len(v) for v in error_categories.values())
        return ValidationResult(ok=all_errors == 0, error_categories=error_categories)

    # ------------------------------------------------------------------
    # Retry prompt helper
    # ------------------------------------------------------------------

    def _retry_prompt(self, original_prompt: str, validation_result: ValidationResult, ctx: CategorizationStageContext, previous_response: str) -> str:  # noqa: D401
        error_details = create_retry_error_details(validation_result.error_categories)
        retry_block = self._retry_prompt_template.replace("{{error_details}}", error_details)
        return f"{original_prompt}\n\n{retry_block}"

    # ------------------------------------------------------------------
    # Result conversion helper
    # ------------------------------------------------------------------

    async def _produce_result(
        self, raw_response: str, ctx: CategorizationStageContext, attempts: int
    ) -> CategorizationStageResult:
        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        taxonomies: List[TaxonomyDTO] = [
            TaxonomyDTO(name=cat_name, definition=cat_data["definition"])
            for cat_name, cat_data in payload.items()
            if isinstance(cat_data, dict) and "definition" in cat_data
        ]

        return CategorizationStageResult(
            taxonomies_categorised=taxonomies,
        )

    # ------------------------------------------------------------------
    # Split / merge helpers
    # ------------------------------------------------------------------

    async def _merge_split_results(
        self,
        res_left: CategorizationStageResult,
        res_right: CategorizationStageResult,
        ctx_left: CategorizationStageContext,
        ctx_right: CategorizationStageContext,
        depth: int,
    ) -> CategorizationStageResult:  # noqa: D401 – signature enforced by BaseStage
        taxonomy_by_name: Dict[str, TaxonomyDTO] = {}
        for t in res_left.taxonomies_categorised + res_right.taxonomies_categorised:
            taxonomy_by_name.setdefault(t.name, t)

        return CategorizationStageResult(
            taxonomies_categorised=list(taxonomy_by_name.values()),
        )

    def _split_context(
        self, ctx: CategorizationStageContext, depth: int
    ) -> tuple[CategorizationStageContext, CategorizationStageContext]:  # noqa: D401
        """Split the aspect list in half for recursive processing."""
        if len(ctx.aspects) <= 1:
            raise NotImplementedError("Cannot split context with a single aspect")

        mid = len(ctx.aspects) // 2
        left = CategorizationStageContext(
            product_category=ctx.product_category,
            aspects=ctx.aspects[:mid],
        )
        right = CategorizationStageContext(
            product_category=ctx.product_category,
            aspects=ctx.aspects[mid:],
        )
        return left, right

    # ------------------------------------------------------------------
    # Optional helper for subclasses
    # ------------------------------------------------------------------

    def _get_additional_template_vars(self, ctx: CategorizationStageContext) -> Dict[str, str]:
        """Subclasses may override to add domain-specific placeholder vars."""
        return {} 