"""Models for Review Analysis Chart."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field

from ..base_models import BaseRequestModel, BaseResponseModel
from ..reviewCore.models import ReviewAspectBase, CategoryInfoBase, PaginationBase


# ==================== Request Models ====================

class TopCategoriesRequest(BaseRequestModel):
    """Request model for top categories analysis with embedded cause analysis."""
    options: Dict[str, Any] = Field(..., description="Options for filtering and selecting aspect categories. Can include 'return_top_cause_categories' for cause analysis with options: sentiment (optional), limit (default: 10)")


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
    chart_type: Optional[Literal["pain-points", "delights", "use-case"]] = Field(
        default=None, description="Chart type to determine aspect type filtering"
    )


# ==================== Response Models ====================

class CauseAspect(BaseModel):
    """Simplified cause aspect with sentiment."""
    aspect_description: str = Field(description="Formatted aspect description")
    sentiment: str = Field(description="Sentiment: '+' for positive, '-' for negative")


class CauseData(BaseModel):
    """Cause data embedded in each category."""
    cause_category_pk: int = Field(description="Cause category primary key")
    cause_category_name: str = Field(description="Cause category name")
    total_reviews: int = Field(description="Number of unique reviews mentioning this cause")
    positive_reviews: int = Field(description="Number of unique reviews with positive sentiment")
    negative_reviews: int = Field(description="Number of unique reviews with negative sentiment")
    aspects: List[CauseAspect] = Field(description="List of aspects mentioning this cause with sentiments")


class AggregatedCauseSummary(BaseModel):
    """Aggregated cause summary across all aspects."""
    cause_category_pk: int = Field(description="Cause category primary key")
    cause_category_name: str = Field(description="Cause category name")
    total_reviews: int = Field(description="Total unique reviews across all aspects")
    total_positive_reviews: int = Field(description="Total positive reviews across all aspects")
    total_negative_reviews: int = Field(description="Total negative reviews across all aspects")
    rank: int = Field(description="Rank based on total reviews")
    aspects: List[CauseAspect] = Field(description="All aspects mentioning this cause with sentiments")


class CategorySummary(BaseModel):
    """Category summary with statistics and embedded cause data."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    definition: str = Field(description="Category definition")
    aspect_type: str = Field(description="Aspect type")
    total_mentions: int = Field(description="Total mentions across all sentiments")
    positive_mentions: int = Field(description="Number of positive mentions")
    negative_mentions: int = Field(description="Number of negative mentions")

    total_reviews: int = Field(description="Number of unique reviews")
    positive_reviews: int = Field(description="Number of unique reviews with positive sentiment")
    negative_reviews: int = Field(description="Number of unique reviews with negative sentiment")
    positive_ratio: float = Field(description="Ratio of positive reviews to total sentiment reviews")
    cause_data: List[CauseData] = Field(default=[], description="Embedded cause data for this category")


class TopCategoriesData(BaseModel):
    """Top categories data model with embedded cause analysis."""
    categories: List[CategorySummary] = Field(description="List of top categories with statistics and embedded cause data")
    total_categories: int = Field(description="Total number of categories returned")
    summary_stats: Dict[str, Any] = Field(description="Summary statistics across all categories")
    aggregated_cause_summary: List[AggregatedCauseSummary] = Field(default=[], description="Aggregated cause summary across all aspects")


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