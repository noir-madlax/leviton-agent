"""Abstract consolidation stage base for taxonomy pipelines."""

from __future__ import annotations
import abc
from dataclasses import dataclass
from typing import List

from .pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)

__all__: list[str] = [
    "ConsolidationStageContext",
    "ConsolidationStageResult",
    "ConsolidationStage",
]


@dataclass(slots=True, frozen=True)
class ConsolidatedTaxonomyDTO:  # noqa: D401
    taxonomy: TaxonomyDTO
    original_taxonomies: list[TaxonomyDTO]


@dataclass(slots=True, frozen=True)
class ConsolidationStageContext(StageContext):
    taxonomy_a: list[TaxonomyDTO]
    taxonomy_b: list[TaxonomyDTO]


@dataclass(slots=True, frozen=True)
class ConsolidationStageResult(StageResultBase):
    taxonomies_consolidated: List[ConsolidatedTaxonomyDTO]


class ConsolidationStage(BaseStage, abc.ABC):
    """Abstract base class for consolidation stages."""

    @abc.abstractmethod
    async def _build_prompt(self, ctx: ConsolidationStageContext) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def _validate(self, raw_response: str, ctx: ConsolidationStageContext):
        raise NotImplementedError

    @abc.abstractmethod
    def _retry_prompt(
        self,
        original_prompt: str,
        retry_ctx: any,
        ctx: ConsolidationStageContext,
    ) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def _produce_result(
        self,
        raw_response: str,
        ctx: ConsolidationStageContext,
        attempts: int,
    ) -> ConsolidationStageResult:
        raise NotImplementedError

    # default split/merge not provided; subclass can override 