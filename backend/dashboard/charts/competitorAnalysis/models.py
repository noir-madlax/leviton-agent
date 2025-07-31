"""Models for Competitor Analysis Chart."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from datetime import datetime

from ..base_models import BaseRequestModel, BaseResponseModel


# ==================== Request Models ====================

class CompetitorSummaryRequest(BaseRequestModel):
    """Request model for competitor analysis summary."""
    # selected_asins is now inherited from BaseRequestModel


class CompetitorMatrixViewRequest(BaseRequestModel):
    """Request model for competitor analysis matrix view."""
    # selected_asins is now inherited from BaseRequestModel
    aspect_type: Literal["phy_perf", "use"] = Field(..., description="Aspect type filter")
    options: Dict[str, Any] = Field(..., description="Options for filtering and selecting aspect categories (sort_by, sort_direction, max_categories, min_mentions, etc.)")


class ReviewRetrievalRequest(BaseRequestModel):
    """Request model for retrieving reviews by category and product."""
    category_id: int = Field(..., description="Aspect category ID to filter by")
    product_id: str = Field(..., description="Product ID (ASIN) to filter by")
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
        default=None, description="Filter by rating (high: 4-5 stars, mid: 3 stars, low: 1-2 stars). If None, returns all ratings."
    )


# ==================== Response Models ====================

class CompetitorSummaryProduct(BaseModel):
    """Individual competitor product summary model."""
    asin: str = Field(description="Product ASIN")
    product_title: str = Field(description="Product title")
    rating: Optional[float] = Field(description="Product rating")
    brand: Optional[str] = Field(description="Product brand")
    product_url: Optional[str] = Field(description="Product URL")
    list_price: Optional[float] = Field(description="List price in USD")
    unique_reviews_count: int = Field(description="Number of unique reviews")
    additional_metrics: Optional[Dict[str, Any]] = Field(
        default=None, description="Additional metrics including sentiment distribution and category counts"
    )


class CompetitorSummaryData(BaseModel):
    """Competitor summary data model."""
    products: List[CompetitorSummaryProduct] = Field(description="List of competitor products")
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
    aspect_categories: List[AspectCategoryInfo] = Field(
        description="List of aspect categories sorted by total mentions"
    )
    product_aspect_data: List[ProductAspectData] = Field(
        description="Aspect data for each product"
    )
    selected_asins: List[str] = Field(description="List of ASINs that were requested")
    aspect_type: str = Field(description="Aspect type that was filtered")
    total_categories: int = Field(description="Total number of categories returned")


class CompetitorMatrixViewResponse(BaseResponseModel[CompetitorMatrixViewData]):
    """Response model for competitor analysis matrix view API."""


class ReviewAspect(BaseModel):
    """Individual aspect mentioned in a review."""
    aspect_description: str = Field(description="Aspect description from the review")
    sentiment: str = Field(description="Sentiment (+ for positive, - for negative, neutral)")
    aspect_type: str = Field(description="Aspect type (phy, perf, use)")


class ReviewDetail(BaseModel):
    """Individual review detail model with aggregated aspects."""
    review_id: str = Field(description="Unique review identifier")
    review_title: Optional[str] = Field(description="Review title")
    review_text: str = Field(description="Review content text")
    rating: Optional[int] = Field(description="Review rating (1-5)")
    verified: Optional[bool] = Field(description="Whether review is verified")
    review_date: Optional[str] = Field(description="Review date")
    aspects: List[ReviewAspect] = Field(description="All aspects mentioned in this review with sentiments")
    category_name: str = Field(description="Aspect category name")
    category_definition: Optional[str] = Field(description="Category definition")
    aspect_type: str = Field(description="Aspect type (phy, perf, use)")


class PaginationInfo(BaseModel):
    """Pagination information."""
    limit: int = Field(description="Number of items per page")
    offset: int = Field(description="Current offset")
    has_more: bool = Field(description="Whether there are more items available")


class CategoryInfo(BaseModel):
    """Category information."""
    category_pk: int = Field(description="Category primary key")
    name: str = Field(description="Category name")
    definition: str = Field(description="Category definition")
    aspect_type: str = Field(description="Aspect type")
    stage: str = Field(description="Category stage")


class ReviewRetrievalData(BaseModel):
    """Review retrieval data model."""
    reviews: List[ReviewDetail] = Field(description="List of review details with aggregated aspects")
    total_reviews: int = Field(description="Total number of reviews found")
    project_id: str = Field(description="Project ID used for filtering")
    category_id: int = Field(description="Category ID used for filtering")
    product_id: str = Field(description="Product ID used for filtering")
    category_info: Optional[CategoryInfo] = Field(description="Category information")
    pagination: PaginationInfo = Field(description="Pagination information")


class ReviewRetrievalResponse(BaseResponseModel[ReviewRetrievalData]):
    """Response model for review retrieval API.""" 