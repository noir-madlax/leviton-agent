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


class StartSegmentationRequest(BaseModel):
    """Request to start a new segmentation run."""
    product_ids: List[Union[int, str]]  # 支持ASIN字符串或product_id整数
    product_category: str
    project_id: Optional[str] = None


class ProductSegmentRun(BaseModel):
    """Data for a segmentation run, matching product_segment_runs table."""
    id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    stage: SegmentationStage = SegmentationStage.INIT
    project_id: Optional[str] = None
    
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
    project_id: Optional[str] = None
    segment_name: Optional[str] = None

