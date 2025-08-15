"""Data models for Projects module."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


class ProjectFilters(BaseModel):
    """Project creation filters."""
    categories: List[str]
    sources: List[str]
    brands: List[str]
    top_sales_count: Optional[int] = None
    category_id: Optional[str] = None
    # 🆕 Optional: allow creating project by explicit ASIN list
    product_asins: Optional[List[str]] = None
    # 🆕 Optional: raw input text for backend parsing (kept for future use)
    raw_asin_input: Optional[str] = None


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    project_name: str
    company_name: Optional[str] = "Leviton"
    user_name: Optional[str] = "Current User"
    user_uid: Optional[str] = None  # 添加用户UID字段
    description: Optional[str] = None
    filters: ProjectFilters


class Project(BaseModel):
    """Project data model matching database schema."""
    id: str
    project_name: str
    company_name: Optional[str] = None
    user_name: Optional[str] = None
    description: Optional[str] = None
    selected_categories: List[str]
    selected_sources: List[str]
    selected_brands: List[str]
    selected_product_asins: List[str]
    top_sales_count: Optional[int] = None
    total_products: int
    total_brands: int
    total_reviews: int
    avg_monthly_sales: float
    created_at: datetime
    updated_at: datetime
    status: str
    # Add simplified overall status for frontend display
    overall_status: Optional[str] = "creating"  # 'creating', 'ready', 'failed'
    segmentation_run_id: Optional[str] = None
    segmentation_started_at: Optional[datetime] = None
    segmentation_completed_at: Optional[datetime] = None
    segmentation_duration_seconds: Optional[int] = None
    segmentation_status: Optional[str] = "pending"
    # Review Analysis fields
    review_analysis_id: Optional[str] = None
    review_analysis_started_at: Optional[datetime] = None
    review_analysis_completed_at: Optional[datetime] = None
    review_analysis_duration_seconds: Optional[int] = None
    review_analysis_status: Optional[str] = "pending"
    # Review analysis estimates
    estimated_reviews_to_analyze: Optional[int] = 0
    estimated_llm_calls: Optional[int] = 0


class ProjectCreateResponse(BaseModel):
    """Response model for project creation."""
    id: str
    project_name: str
    selected_product_asins: List[str]
    total_products: int
    total_brands: int
    total_reviews: int
    avg_monthly_sales: float
    status: str 
    overall_status: Optional[str] = "creating"
    segmentation_status: Optional[str] = "pending" 