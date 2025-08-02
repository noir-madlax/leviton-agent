"""Models for Review Analysis Chart."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

from ..base_models import BaseRequestModel, BaseResponseModel
from ..reviewCore.models import ReviewAspectBase, CategoryInfoBase, PaginationBase


# ==================== Request Models ====================

class TopCategoriesRequest(BaseRequestModel):
    """Request model for top categories analysis."""
    options: Dict[str, Any] = Field(..., description="Options for filtering and selecting aspect categories (aspect_type, sort_by, sort_direction, max_categories, min_mentions, etc.)")


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
    sentiment_filter: Optional[Literal["positive", "negative"]] = Field(
        default=None, description="Filter by sentiment (positive, negative). If None, returns all sentiments."
    )
    rating_filter: Optional[Literal["high", "mid", "low"]] = Field(
        default=None, description="Filter by rating: high (4-5 stars), mid (3 stars), low (1-2 stars). If None, returns all ratings."
    )


class CauseMatrixViewRequest(BaseRequestModel):
    """Request model for cause analysis matrix view."""
    top_aspect_category_ids: List[int] = Field(..., description="List of top aspect category IDs (columns)")
    top_cause_category_ids: List[int] = Field(..., description="List of top cause category IDs (rows)")
    sentiment_filter: Optional[Literal["+", "-"]] = Field(
        default=None, description="Filter by sentiment (+ for positive, - for negative). If None, returns all sentiments."
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
    total_reviews: int = Field(description="Number of unique reviews")
    positive_reviews: int = Field(description="Number of unique reviews with positive sentiment")
    negative_reviews: int = Field(description="Number of unique reviews with negative sentiment")
    positive_ratio: float = Field(description="Ratio of positive reviews to total sentiment reviews")


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


class CauseMatrixCell(BaseModel):
    """Individual cell data in the cause matrix."""
    category_pk: int = Field(description="Aspect category primary key")
    category_name: str = Field(description="Aspect category name")
    total_reviews: int = Field(description="Total unique reviews mentioning both aspect and cause")
    positive_reviews: int = Field(description="Positive reviews mentioning both aspect and cause")
    negative_reviews: int = Field(description="Negative reviews mentioning both aspect and cause")


class CauseMatrixRow(BaseModel):
    """Row data in the cause matrix (one cause category)."""
    cause_category_id: int = Field(description="Cause category ID")
    cause_category_name: str = Field(description="Cause category name")
    aspect_data: List[CauseMatrixCell] = Field(description="Cell data for each aspect category")


class CauseMatrixViewData(BaseModel):
    """Cause matrix view data model."""
    aspect_categories: List[Dict[str, Any]] = Field(description="List of aspect categories (columns)")
    cause_aspect_data: List[CauseMatrixRow] = Field(description="Matrix data with cause categories as rows")
    total_aspect_categories: int = Field(description="Total number of aspect categories")
    total_cause_categories: int = Field(description="Total number of cause categories")


class CauseMatrixViewResponse(BaseResponseModel[CauseMatrixViewData]):
    """Response model for cause matrix view API.""" 