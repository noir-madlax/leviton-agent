"""Shared LLM taxonomy pipeline infrastructure.

This package contains generic building-blocks (batching, retry, split-and-conquer)
that can be reused by *product_segment* and *review_analysis* domain pipelines.
"""

from .pipeline_stage import (
    BaseStage,
    StageContext,
    StageResultBase,
    StageProtocolError,
    StageCallBudgetExceeded,
    CallStorage,
    TaxonomyDTO,
)

__all__: list[str] = [
    "BaseStage",
    "StageContext",
    "StageResultBase",
    "StageProtocolError",
    "StageCallBudgetExceeded",
    "CallStorage",
    "TaxonomyDTO",
    "ExtractionStageContext",
    "ExtractionStageResult",
    "ExtractionStage",
    "ConsolidationStageContext",
    "ConsolidationStageResult",
    "ConsolidationStage",
    "RefinementStageContext",
    "RefinementStageResult",
    "RefinementStage",
] 