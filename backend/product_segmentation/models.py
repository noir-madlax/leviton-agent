"""
Pydantic models for product segmentation entities
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator, field_validator, model_validator, ConfigDict
from enum import Enum


class SegmentationStatus(str, Enum):
    """Segmentation run status options"""
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class InteractionType(str, Enum):
    """LLM interaction types"""
    SEGMENTATION = "segmentation"
    CONSOLIDATE_TAXONOMY = "consolidate_taxonomy"
    REFINE_ASSIGNMENTS = "refine_assignments"


# Base models for database entities
class SegmentationRunBase(BaseModel):
    """Base model for segmentation runs"""
    category: Optional[str] = None
    llm_config: Optional[Dict[str, Any]] = None
    processing_params: Optional[Dict[str, Any]] = None
    total_products: Optional[int] = None
    processed_products: int = 0
    result_summary: Optional[Dict[str, Any]] = None


class SegmentationRunCreate(SegmentationRunBase):
    """Model for creating segmentation runs"""
    id: str = Field(..., description="Run identifier")
    total_products: int = Field(..., description="Total number of products to process")
    processed_products: int = Field(default=0, description="Number of products processed")
    status: SegmentationStatus = Field(default=SegmentationStatus.RUNNING, description="Run status")
    llm_config: Optional[Dict[str, Any]] = Field(default=None, description="LLM configuration")
    processing_params: Optional[Dict[str, Any]] = Field(default=None, description="Processing parameters")
    result_summary: Optional[Dict[str, Any]] = Field(default=None, description="Summary of results")

    @field_validator('id')
    def validate_id(cls, v):
        """Validate run ID"""
        if not v:
            raise ValueError("Run ID must be non-empty")
        if len(v) > 50:
            raise ValueError("Run ID must be at most 50 characters")
        return v

    @field_validator('category')
    def validate_category_run(cls, v):
        if v is None or not v.strip():
            raise ValueError("Category must be non-empty")
        return v


class SegmentationRun(SegmentationRunCreate):
    """Full segmentation run model"""
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RunProductCreate(BaseModel):
    """Model for adding products to a run"""
    run_id: str
    product_id: int


class RunProduct(RunProductCreate):
    """Full run product model"""
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class ProductTaxonomyBase(BaseModel):
    """Base model for product taxonomies"""
    category_name: str = Field(..., max_length=255)
    definition: Optional[str] = None
    product_count: int = 0


class ProductTaxonomyCreate(ProductTaxonomyBase):
    """Model for creating taxonomies"""
    run_id: str = Field(..., description="Run identifier")
    category_name: str = Field(..., description="Category name")
    definition: str = Field(..., description="Category definition")
    product_count: int = Field(..., description="Number of products in category")


class ProductTaxonomy(ProductTaxonomyCreate):
    """Full taxonomy model"""
    id: int = Field(..., description="Taxonomy identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class ProductSegmentBase(BaseModel):
    """Base model for product segments"""
    run_id: str
    product_id: int
    taxonomy_id: int


class ProductSegmentCreate(ProductSegmentBase):
    """Model for creating product segments"""
    category_name: Optional[str] = Field(default=None, description="Category name")


class ProductSegment(ProductSegmentCreate):
    """Full product segment model"""
    id: int = Field(..., description="Segment identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class RefinedProductSegmentCreate(ProductSegmentBase):
    """Model for creating refined product segments"""
    category_name: Optional[str] = Field(default=None, description="Category name")


class RefinedProductSegment(RefinedProductSegmentCreate):
    """Full refined product segment model"""
    id: int = Field(..., description="Segment identifier")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class LLMInteractionIndexBase(BaseModel):
    """Base model for LLM interaction index"""
    interaction_type: InteractionType
    batch_id: Optional[int] = None
    attempt: int = 1
    file_path: str
    prompt_file: Optional[str] = None
    cache_key: Optional[str] = Field(None, max_length=32)


class LLMInteractionIndexCreate(LLMInteractionIndexBase):
    """Model for creating LLM interaction index entries"""
    run_id: str = Field(..., description="Run identifier")


class LLMInteractionIndex(LLMInteractionIndexBase):
    """Full LLM interaction index model"""
    id: int = Field(..., description="Index identifier")
    run_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    
    model_config = ConfigDict(from_attributes=True)


# Request/Response models for API
class StartSegmentationRequest(BaseModel):
    """Request to start a new segmentation run."""

    product_ids: List[int]
    category: str  # required – aligns with prompt template requirement
    batch_size: Optional[int] = None

    @field_validator("product_ids")
    def validate_product_ids(cls, v: List[int]) -> List[int]:
        """Validate product IDs."""
        if not v:
            raise ValueError("At least one product ID required")
        return v

    @field_validator("category")
    def validate_category(cls, v: str) -> str:  # noqa: D401 – pydantic signature
        if not v or not v.strip():
            raise ValueError("Category must be non-empty")
        return v

    @field_validator("batch_size")
    def validate_batch_size(cls, v: Optional[int]) -> Optional[int]:
        """Validate batch size."""
        if v is not None and v <= 0:
            raise ValueError("Batch size must be positive")
        return v


class SegmentationStatusResponse(BaseModel):
    """Response model for segmentation status"""
    run_id: str
    status: SegmentationStatus
    total_products: int
    processed_products: int
    progress_percent: float
    estimated_completion: Optional[datetime] = None


class TaxonomyResult(BaseModel):
    """Taxonomy result model"""
    id: int
    category_name: str
    definition: Optional[str]
    product_count: int


class SegmentResult(BaseModel):
    """Segment result model"""
    product_id: int
    taxonomy_id: int


class SegmentationResultsResponse(BaseModel):
    """Response model for segmentation results endpoint."""
    run_id: str
    status: SegmentationStatus
    taxonomies: List[Dict[str, Any]]
    segments: List[Dict[str, Any]]
    refined_segments: List[Dict[str, Any]] 