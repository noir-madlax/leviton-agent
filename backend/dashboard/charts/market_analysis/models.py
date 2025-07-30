"""Market Analysis API models."""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class TAMMarketShareRequest(BaseModel):
    """Request model for TAM and Market Share analysis."""

    project_id: str = Field(..., description="Project ID for filtering", example="d2c02b80-4c82-44cc-8093-56708a7883f7")
    filters: Optional[Dict[str, Any]] = Field(
        default_factory=dict,
        description="Filters to apply (categories, brands, segments, extend_fields)",
        example={
            "categories": ["Dimmer Switches", "Light Switches"],
            "brands": ["Leviton", "Lutron"],
            "segments": ["Premium", "Standard"],
            "extend_fields": {
                "smart_capability": "Smart"
            }
        }
    )


class BrandShareData(BaseModel):
    """Brand market share data within a category."""
    
    brand: str = Field(..., description="Brand name")
    revenue: float = Field(..., description="Brand revenue in this category")
    volume: int = Field(..., description="Brand volume in this category")
    product_count: int = Field(..., description="Number of products from this brand")
    market_share_percentage: float = Field(..., description="Market share percentage within category")
    rank: int = Field(..., description="Rank within this category by revenue")


class CategoryMarketShare(BaseModel):
    """Market share data for a specific category."""
    
    category: str = Field(..., description="Category name")
    total_revenue: float = Field(..., description="Total revenue for this category")
    total_volume: int = Field(..., description="Total volume for this category")
    total_products: int = Field(..., description="Total number of products in this category")
    brand_shares: List[BrandShareData] = Field(..., description="Brand market shares within this category")


class TAMData(BaseModel):
    """Total Addressable Market data."""
    
    total_market_revenue: float = Field(..., description="Total market revenue across all categories")
    total_market_volume: int = Field(..., description="Total market volume across all categories")
    total_products: int = Field(..., description="Total number of products across all categories")
    currency: str = Field(default="USD", description="Currency for revenue figures")


class TAMMarketShareMetadata(BaseModel):
    """Metadata for TAM and Market Share analysis."""
    
    filtered_asins_count: int = Field(..., description="Number of ASINs after filtering")
    total_categories: int = Field(..., description="Number of categories in the analysis")
    total_brands: int = Field(..., description="Number of brands in the analysis")
    calculation_timestamp: str = Field(..., description="Timestamp when calculation was performed")


class TAMMarketShareResponse(BaseModel):
    """Response model for TAM and Market Share analysis."""
    
    tam_data: TAMData = Field(..., description="Total Addressable Market data")
    market_share_by_category: List[CategoryMarketShare] = Field(
        ..., 
        description="Market share data grouped by category"
    )
    metadata: TAMMarketShareMetadata = Field(..., description="Analysis metadata")
