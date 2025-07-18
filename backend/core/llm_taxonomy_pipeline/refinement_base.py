"""Abstract refinement/assignment stage base for taxonomy pipelines."""

from __future__ import annotations
import abc
from dataclasses import dataclass
from typing import Dict

from .pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    TaxonomyDTO,
)

__all__: list[str] = [
    "RefinementStageContext",
    "RefinementStageResult",
    "RefinementStage",
]


@dataclass(slots=True, frozen=True)
class RefinementStageContext(StageContext):
    """Input aspects/items and consolidated categories."""
    aspects: Dict[str, str]  # id -> description
    consolidated_categories: Dict[str, TaxonomyDTO]  # name -> dto


@dataclass(slots=True, frozen=True)
class RefinementStageResult(StageResultBase):
    assignments_final: Dict[str, str]  # id -> final category name


class RefinementStage(BaseStage, abc.ABC):
    """Abstract stage mapping items to consolidated categories."""

    @abc.abstractmethod
    async def _build_prompt(self, ctx: RefinementStageContext) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    def _validate(self, raw_response: str, ctx: RefinementStageContext):
        raise NotImplementedError

    @abc.abstractmethod
    def _retry_prompt(self, original_prompt: str, retry_ctx: any, ctx: RefinementStageContext, previous_response: str) -> str:
        raise NotImplementedError

    @abc.abstractmethod
    async def _produce_result(self, raw_response: str, ctx: RefinementStageContext, attempts: int) -> RefinementStageResult:
        raise NotImplementedError 