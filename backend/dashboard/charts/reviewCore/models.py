"""Shared models for review analysis functionality."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field


class ReviewAspectBase(BaseModel):
    """Base model for review aspects."""
    aspect_description: str = Field(description="Aspect description from the review")
    sentiment: str = Field(description="Sentiment (+ for positive, - for negative, neutral)")
    aspect_type: str = Field(description="Aspect type (phy, perf, use)")


class ProductInfoBase(BaseModel):
    """Base model for product information."""
    product_id: str = Field(description="Product ASIN")
    title: Optional[str] = Field(description="Product title")
    brand: Optional[str] = Field(description="Product brand")
    product_url: Optional[str] = Field(description="Product URL")


class ReviewDetailBase(BaseModel):
    """Base model for review details."""
    review_id: str = Field(description="Unique review identifier")
    review_title: Optional[str] = Field(description="Review title")
    review_text: str = Field(description="Review content text")
    rating: Optional[int] = Field(description="Review rating (1-5)")
    verified: Optional[bool] = Field(description="Whether review is verified")
    review_date: Optional[str] = Field(description="Review date")
    aspects: List[ReviewAspectBase] = Field(description="All aspects mentioned in this review with sentiments")


class CategoryInfoBase(BaseModel):
    """Base model for category information."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    definition: str = Field(description="Category definition")
    aspect_type: str = Field(description="Aspect type")


class PaginationBase(BaseModel):
    """Base pagination model."""
    limit: int = Field(description="Number of items per page")
    offset: int = Field(description="Current offset")
    has_more: bool = Field(description="Whether there are more items available") 