"""Competitor Analysis Chart Models for Dashboard module."""

from typing import Dict, List, Any, Literal, Optional
from pydantic import BaseModel, Field

from ..base_models import BaseRequestModel, BaseResponseModel


# ==================== Request Models ====================

class CompetitorSummaryRequest(BaseRequestModel):
    """Competitor analysis summary request model."""
    selected_asins: List[str] = Field(..., description="List of ASINs to analyze")


class CompetitorMatrixViewOptions(BaseModel):
    """Options for competitor matrix view."""
    # Sorting
    sort_by: Literal["mentions", "reviews", "sentiment"] = Field(default="mentions", description="Field to sort by")
    sort_direction: Literal["asc", "desc"] = Field(default="desc", description="Sort direction")
    
    # Limiting
    max_categories: int = Field(default=10, ge=1, le=50, description="Maximum number of categories to return")
    
    # Filtering
    min_mentions: Optional[int] = Field(default=None, description="Minimum total mentions to include")
    min_reviews: Optional[int] = Field(default=None, description="Minimum unique reviews to include")
    include_categories: Optional[List[str]] = Field(default=None, description="Specific categories to include")
    exclude_categories: Optional[List[str]] = Field(default=None, description="Categories to exclude")
    
    # Advanced
    sentiment_filter: Optional[Literal["positive_only", "negative_only", "mixed_only"]] = Field(default=None, description="Filter by sentiment type")


class CompetitorMatrixViewRequest(BaseRequestModel):
    """Request model for competitor analysis matrix view API."""
    selected_asins: List[str] = Field(..., description="List of ASINs to analyze")
    aspect_type: Literal["phy_perf", "use"] = Field(..., description="Aspect type filter")
    options: CompetitorMatrixViewOptions = Field(..., description="View options")


# ==================== Response Models ====================

class CompetitorSummaryProduct(BaseModel):
    """Individual competitor product summary model."""
    asin: str = Field(description="Product ASIN")
    product_title: str = Field(description="Product title")
    rating: float = Field(description="Product rating")
    brand: str = Field(description="Product brand")
    product_url: str = Field(description="Product URL")
    list_price: Optional[float] = Field(description="List price in USD")
    unique_reviews_count: int = Field(description="Number of unique reviews from review_aspect_data_view")
    additional_metrics: Dict[str, Any] = Field(description="Additional metrics including sentiment distribution and category counts")


class CompetitorSummaryData(BaseModel):
    """Competitor summary data model."""
    products: List[CompetitorSummaryProduct] = Field(description="List of competitor products with summary data")
    total_products: int = Field(description="Total number of products returned")
    selected_asins: List[str] = Field(description="List of ASINs that were requested")


class CompetitorSummaryResponse(BaseResponseModel[CompetitorSummaryData]):
    """Response model for competitor analysis summary API."""


class AspectCategoryInfo(BaseModel):
    """Information about an aspect category."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    definition: str = Field(description="Category definition")


class ProductAspectData(BaseModel):
    """Aspect data for a specific product."""
    asin: str = Field(description="Product ASIN")
    aspect_data: List[Dict[str, Any]] = Field(description="List of aspect data for this product")


class CompetitorMatrixViewData(BaseModel):
    """Competitor matrix view data model."""
    aspect_categories: List[AspectCategoryInfo] = Field(description="List of aspect categories sorted by total mentions")
    product_aspect_data: List[ProductAspectData] = Field(description="Aspect data for each product")
    selected_asins: List[str] = Field(description="List of ASINs that were requested")
    aspect_type: str = Field(description="Aspect type that was filtered")
    total_categories: int = Field(description="Total number of categories returned")


class CompetitorMatrixViewResponse(BaseResponseModel[CompetitorMatrixViewData]):
    """Response model for competitor analysis matrix view API.""" 