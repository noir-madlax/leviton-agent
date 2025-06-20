"""Models for the Product Segmentation service.

This module defines the data models used by the Product Segmentation service,
including run tracking, taxonomies, assignments, and LLM interactions.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union
from pydantic import BaseModel, Field


class SegmentationStage(str, Enum):
    """Status/stage of a segmentation run."""
    INIT = "init"
    EXTRACTION = "extraction"
    CONSOLIDATION = "consolidation"
    REFINEMENT = "refinement"
    COMPLETED = "completed"
    FAILED = "failed"


class InteractionType(str, Enum):
    """Type of LLM interaction."""
    EXTRACTION = "extraction"
    CONSOLIDATION = "consolidation"
    REFINEMENT = "refinement"


class StartSegmentationRequest(BaseModel):
    """Request to start a new segmentation run."""
    product_ids: List[int]
    product_category: str


class ProductSegmentRun(BaseModel):
    """Data for a segmentation run, matching product_segment_runs table."""
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    stage: SegmentationStage = SegmentationStage.INIT
    
    # Progress tracking fields
    seg_batches_done: int = 0
    seg_batches_total: Optional[int] = None
    con_batches_done: int = 0
    con_batches_total: Optional[int] = None
    ref_batches_done: int = 0
    ref_batches_total: Optional[int] = None
    
    total_products: int
    processed_products: int = 0
    
    llm_config: Dict = Field(default_factory=dict)
    processing_params: Dict = Field(default_factory=dict)
    result_summary: Optional[Dict] = None


class ProductSegmentTaxonomy(BaseModel):
    """Data for a product taxonomy, matching product_segment_taxonomies table."""
    run_id: str
    segment_name: str
    definition: str = ""
    stage: str = "extraction"


class ProductSegmentAssignment(BaseModel):
    """Data for a product segment assignment, matching product_segment_assignments table."""
    run_id: str
    product_id: int
    taxonomy_id_initial: int
    taxonomy_id_refined: int


class ProductSegmentLLMInteraction(BaseModel):
    """Data for an LLM interaction record, matching product_segment_llm_interactions table."""
    run_id: str
    interaction_type: InteractionType
    batch_id: int
    attempt: int = 1
    file_path: str
    cache_key: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ProgressEvent(BaseModel):
    """Event emitted to track segmentation progress."""
    run_id: str
    percent: float
    stage: SegmentationStage
