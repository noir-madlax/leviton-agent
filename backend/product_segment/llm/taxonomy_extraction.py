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
      "taxonomies": [
        {"name": "<taxonomy_name>", "definition": "<what qualifies>"},
        ...
      ],
      "assignments": {
        "0": "<taxonomy_name_of_text_0>",
        "1": "<taxonomy_name_of_text_1>",
        ...
      }
    }

No other top-level keys are allowed.  Each index from ``0`` … ``len(texts)-1``
must appear **exactly once** in *assignments* and every referenced taxonomy
name must exist in the *taxonomies* list.
"""

from dataclasses import dataclass
import json
import textwrap
from typing import Any, Dict, List, Sequence

from core.utils.llm_utils import extract_json, create_retry_error_details, ValidationResult
from product_segment.llm.taxonomy_pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
)

__all__ = [
    "TaxonomyDTO",
    "ExtractionStageResult",
    "ExtractionStage",
]

# ---------------------------------------------------------------------------
# Data-transfer objects
# ---------------------------------------------------------------------------


@dataclass(slots=True, frozen=True)
class TaxonomyDTO:  # noqa: D401 – simple DTO
    """Lightweight taxonomy representation returned by the extraction stage."""

    name: str
    definition: str


@dataclass(slots=True)
class ExtractionStageResult(StageResultBase):  # pylint: disable=too-many-instance-attributes
    """Concrete :class:`StageResultBase` payload for the extraction stage."""

    taxonomies_extracted: List[TaxonomyDTO]
    assignments_initial: Dict[int, str]
    batches_done: int


# ---------------------------------------------------------------------------
# Prompt helpers & retry-utilities
# ---------------------------------------------------------------------------


# Simple retry template (the full blown template from product-segmentation
# is reused in a reduced form to avoid external dependencies).
_RETRY_TEMPLATE = textwrap.dedent(
    """

    -------- RETRY INSTRUCTIONS --------
    The previous answer had the following issues:
    {error_details}

    Please return the corrected JSON following the schema verbatim. Do *not*
    include code-blocks, markdown or commentary.
    -----------------------------------
    """
)


# ---------------------------------------------------------------------------
# Runtime-supplied prompt template
# ---------------------------------------------------------------------------
# The concrete prompt text must be supplied by the orchestrator via
# ``ctx.context_vars["prompt_template"]``.  Keeping the stage *prompt-agnostic*
# avoids hard-coding domain specifics and lets callers reuse the stage with
# different prompt flavours (see *extract_taxonomy_prompt_v0.txt*).
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# ExtractionStage implementation
# ---------------------------------------------------------------------------


class ExtractionStage(BaseStage):
    """Concrete taxonomy-extraction stage built on :class:`BaseStage`."""

    # --------------------- BaseStage abstract hooks -------------------------

    async def _build_prompt(self, seq: Sequence[str], ctx: StageContext) -> str:  # noqa: D401
        """Render the caller-supplied prompt template and append the input lines."""

        prompt_template: str | None = ctx.context_vars.get("prompt_template")
        if prompt_template is None:
            raise ValueError(
                "ExtractionStage requires 'prompt_template' in ctx.context_vars"
            )

        # Allow placeholder replacement using context_vars themselves. This lets
        # callers provide ``{"product_category": "Electronics"}``, …
        try:
            rendered_template = prompt_template.format(**ctx.context_vars)
        except KeyError as exc:
            raise ValueError(f"Missing template variable {exc} for prompt_template") from exc

        input_lines = "\n".join(f"[{i}] {txt}" for i, txt in enumerate(seq))
        return f"{rendered_template}\n\n{input_lines}"

    def _validate(
        self, raw_response: str, seq: Sequence[str], ctx: StageContext
    ) -> ValidationResult:
        """Validate and (optionally) return retry-context."""

        expected_ids = {str(i) for i in range(len(seq))}

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

        if "taxonomies" not in parsed or "assignments" not in parsed:
            missing = {k for k in ("taxonomies", "assignments") if k not in parsed}
            error_categories["format_errors"].append(
                f"Missing top-level keys: {', '.join(sorted(missing))}"
            )
            return ValidationResult(ok=False, error_categories=error_categories)

        taxonomies = parsed["taxonomies"]
        assignments = parsed["assignments"]

        # Validate taxonomies list
        if not isinstance(taxonomies, list):
            error_categories["format_errors"].append("'taxonomies' must be a list")
        else:
            for idx, entry in enumerate(taxonomies):
                if not isinstance(entry, dict):
                    error_categories["validation_errors"].append(
                        f"taxonomies[{idx}] is not an object"
                    )
                    continue
                if "name" not in entry or "definition" not in entry:
                    error_categories["validation_errors"].append(
                        f"taxonomies[{idx}] missing 'name' or 'definition'"
                    )

        # Validate assignments mapping
        if not isinstance(assignments, dict):
            error_categories["format_errors"].append("'assignments' must be an object")
        else:
            seen_ids = set()
            for k, v in assignments.items():
                if k not in expected_ids:
                    error_categories["completeness_errors"].append(
                        f"Unexpected id '{k}' in assignments"
                    )
                if k in seen_ids:
                    error_categories["completeness_errors"].append(
                        f"Duplicate id '{k}' in assignments"
                    )
                seen_ids.add(k)
                if not isinstance(v, str):
                    error_categories["validation_errors"].append(
                        f"Assignment for id '{k}' is not a string"
                    )
            missing = expected_ids - seen_ids
            if missing:
                error_categories["completeness_errors"].append(
                    f"Missing assignments for ids: {sorted(missing)}"
                )

            # Ensure referenced taxonomy exists
            taxonomy_names = {t.get("name") for t in taxonomies if isinstance(t, dict)}
            for k, v in assignments.items():
                if isinstance(v, str) and v not in taxonomy_names:
                    error_categories["validation_errors"].append(
                        f"Assignment for id '{k}' references unknown taxonomy '{v}'"
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
        retry_block = _RETRY_TEMPLATE.format(error_details=error_details)
        return f"{original_prompt}{retry_block}"

    async def _produce_result(
        self,
        seq: Sequence[str],
        raw_response: str,
        ctx: StageContext,
        attempts: int,
    ) -> ExtractionStageResult:
        """Convert a valid raw response into an :class:`ExtractionStageResult`."""

        json_text = extract_json(raw_response)
        payload = json.loads(json_text)

        taxonomies = [
            TaxonomyDTO(name=item["name"], definition=item["definition"])
            for item in payload["taxonomies"]
        ]
        assignments = {int(k): v for k, v in payload["assignments"].items()}

        return ExtractionStageResult(
            calls_made=attempts,
            taxonomies_extracted=taxonomies,
            assignments_initial=assignments,
            batches_done=1,
        )

    async def _merge_split_results(
        self,
        seq_left: Sequence[Any],
        seq_right: Sequence[Any],
        res_left: ExtractionStageResult,
        res_right: ExtractionStageResult,
        ctx: StageContext,
        depth: int,
    ) -> ExtractionStageResult:  # noqa: D401 – signature enforced by BaseStage
        """Merge two partial results coming from auto-split recursion."""

        # Merge taxonomies – keep order but de-duplicate by *name*.
        taxonomy_by_name: Dict[str, TaxonomyDTO] = {}
        for t in res_left.taxonomies_extracted + res_right.taxonomies_extracted:
            taxonomy_by_name.setdefault(t.name, t)

        # Merge assignments (right side wins on conflict which shouldn't happen)
        assignments = {**res_left.assignments_initial, **res_right.assignments_initial}

        return ExtractionStageResult(
            calls_made=res_left.calls_made + res_right.calls_made,
            taxonomies_extracted=list(taxonomy_by_name.values()),
            assignments_initial=assignments,
            batches_done=res_left.batches_done + res_right.batches_done,
        )
