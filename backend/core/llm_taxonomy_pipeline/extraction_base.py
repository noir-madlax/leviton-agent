"""Abstract extraction stage base for LLM-driven taxonomy pipelines.

Concrete domains (product_segment, review_analysis …) should subclass
:class:`ExtractionStage` and implement all abstract hooks.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Dict, Any, List

from .pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)

__all__: list[str] = [
    "ExtractionStageContext",
    "ExtractionStageResult",
    "ExtractionStage",
]


@dataclass(slots=True, frozen=True)
class ExtractionStageContext(StageContext):
    """Context object carrying the raw inputs for extraction."""

    input_texts: List[str]


@dataclass(slots=True, frozen=True)
class ExtractionStageResult(StageResultBase):
    """Generic result payload for extraction stages."""

    taxonomies_extracted: List[TaxonomyDTO]
    assignments_initial: Dict[int, str]


class ExtractionStage(BaseStage, abc.ABC):
    """Abstract base-class for extraction stages.

    Subclasses must implement **all** BaseStage hooks so that the generic
    orchestrator can run without knowing domain details.
    """

    # ------------------------ mandatory hooks --------------------------------

    @abc.abstractmethod
    async def _build_prompt(self, ctx: ExtractionStageContext) -> str:  # noqa: D401
        raise NotImplementedError

    @abc.abstractmethod
    def _validate(self, raw_response: str, ctx: ExtractionStageContext):  # noqa: D401
        raise NotImplementedError

    @abc.abstractmethod
    def _retry_prompt(
        self,
        original_prompt: str,
        retry_ctx: Any,
        ctx: ExtractionStageContext,
    ) -> str:  # noqa: D401
        raise NotImplementedError

    @abc.abstractmethod
    async def _produce_result(
        self,
        raw_response: str,
        ctx: ExtractionStageContext,
        attempts: int,
    ) -> ExtractionStageResult:  # noqa: D401
        raise NotImplementedError

    # --------------------- optional split/merge hooks -------------------------

    async def _merge_split_results(
        self,
        res_left: ExtractionStageResult,
        res_right: ExtractionStageResult,
        ctx_left: ExtractionStageContext,
        ctx_right: ExtractionStageContext,
        depth: int,
    ) -> ExtractionStageResult:  # noqa: D401 – default concatenation
        # Generic concatenation; domains may override
        return ExtractionStageResult(
            taxonomies_extracted=res_left.taxonomies_extracted + res_right.taxonomies_extracted,
            assignments_initial={
                **res_left.assignments_initial,
                **res_right.assignments_initial,
            },
        )

    def _split_context(
        self, ctx: ExtractionStageContext, depth: int
    ) -> tuple[ExtractionStageContext, ExtractionStageContext]:  # noqa: D401
        # Simple midpoint split of input_texts
        mid = len(ctx.input_texts) // 2
        left = ExtractionStageContext(
            product_category=ctx.product_category,
            input_texts=ctx.input_texts[:mid],
        )
        right = ExtractionStageContext(
            product_category=ctx.product_category,
            input_texts=ctx.input_texts[mid:],
        )
        return left, right 