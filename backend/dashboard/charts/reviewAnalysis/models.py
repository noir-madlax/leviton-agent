"""Models for Review Analysis Chart."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

from ..base_models import BaseRequestModel, BaseResponseModel
from ..reviewCore.models import ReviewAspectBase, CategoryInfoBase, PaginationBase


# ==================== Request Models ====================

class TopCategoriesRequest(BaseRequestModel):
    """Request model for top categories analysis."""
    additional_conditions: Dict[str, Any] = Field(..., description="Additional filtering conditions")


class ReviewsByCategoryRequest(BaseRequestModel):
    """Request model for retrieving reviews by category."""
    category_id: int = Field(..., description="Aspect category ID")
    limit: int = Field(default=100, description="Number of reviews to return")
    offset: int = Field(default=0, description="Offset for pagination")
    sort_by: Literal["review_id", "date", "rating", "sentiment"] = Field(
        default="review_id", description="Sort field"
    )
    sort_order: Literal["asc", "desc"] = Field(
        default="desc", description="Sort direction"
    )


# ==================== Response Models ====================

class CategorySummary(BaseModel):
    """Category summary with statistics."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    definition: str = Field(description="Category definition")
    aspect_type: str = Field(description="Aspect type")
    total_mentions: int = Field(description="Total mentions across all sentiments")
    positive_mentions: int = Field(description="Number of positive mentions")
    negative_mentions: int = Field(description="Number of negative mentions")
    neutral_mentions: int = Field(description="Number of neutral mentions")
    unique_reviews: int = Field(description="Number of unique reviews")
    positive_ratio: float = Field(description="Ratio of positive mentions to total mentions")


class TopCategoriesData(BaseModel):
    """Top categories data model."""
    categories: List[CategorySummary] = Field(description="List of top categories with statistics")
    total_categories: int = Field(description="Total number of categories returned")
    summary_stats: Dict[str, Any] = Field(description="Summary statistics across all categories")


class TopCategoriesResponse(BaseResponseModel[TopCategoriesData]):
    """Response model for top categories analysis API."""


class ReviewWithProductInfo(BaseModel):
    """Review detail model with product information."""
    review_id: str = Field(description="Unique review identifier")
    review_title: Optional[str] = Field(description="Review title")
    review_text: str = Field(description="Review content text")
    rating: Optional[int] = Field(description="Review rating (1-5)")
    verified: Optional[bool] = Field(description="Whether review is verified")
    review_date: Optional[str] = Field(description="Review date")
    aspects: List[ReviewAspectBase] = Field(description="All aspects mentioned in this review with sentiments")
    # Product information (required for review analysis since reviews come from different products)
    product_id: str = Field(description="Product ASIN")
    product_title: Optional[str] = Field(description="Product title")
    product_brand: Optional[str] = Field(description="Product brand")
    product_url: Optional[str] = Field(description="Product URL")


class ReviewsByCategoryData(BaseModel):
    """Reviews by category data model."""
    reviews: List[ReviewWithProductInfo] = Field(description="List of review details with product information")
    total_reviews: int = Field(description="Total number of reviews found")
    project_id: str = Field(description="Project ID used for filtering")
    category_id: int = Field(description="Category ID used for filtering")
    category_info: Optional[CategoryInfoBase] = Field(description="Category information")
    pagination: PaginationBase = Field(description="Pagination information")


class ReviewsByCategoryResponse(BaseResponseModel[ReviewsByCategoryData]):
    """Response model for reviews by category API.""" 