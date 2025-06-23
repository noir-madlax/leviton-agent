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


class ProjectCreateRequest(BaseModel):
    """Request model for creating a new project."""
    project_name: str
    company_name: Optional[str] = "Leviton"
    user_name: Optional[str] = "Current User"
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