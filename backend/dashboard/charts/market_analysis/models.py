"""Market Analysis API models."""

from typing import List, Dict, Any, Optional, Literal
from pydantic import BaseModel, Field
from ..base_models import BaseRequestModel


class TAMMarketShareRequest(BaseRequestModel):
    """Request model for TAM and Market Share analysis."""
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": {
                    "categories": ["Dimmer Switches", "Light Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": ["Premium", "Standard"],
                    "extend_fields": {
                        "smart_capability": "Smart"
                    }
                },
                "timeframe": {
                    "period": "year"
                }
            }
        }


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


# Top Segments by Revenue Models
class TopSegmentsByRevenueRequest(BaseRequestModel):
    """Request model for Top 10 Segments by Revenue analysis."""
    
    limit: int = Field(default=10, description="返回的 segment 数量限制", ge=1, le=50)
    metric_type: Literal["revenue", "volume", "products"] = Field(
        default="revenue", 
        description="排序指标类型: revenue(收入), volume(销量), products(产品数量)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": {
                    "categories": ["Dimmer Switches", "Light Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": ["Premium", "Standard"],
                    "extend_fields": {
                        "smart_capability": "Smart"
                    }
                },
                "timeframe": {
                    "period": "year"
                },
                "limit": 10,
                "metric_type": "revenue"
            }
        }


class SegmentRevenueData(BaseModel):
    """Segment revenue data model."""
    
    segment: str = Field(..., description="Segment 名称")
    revenue: float = Field(..., description="Segment 总收入")
    volume: int = Field(..., description="Segment 总销量")
    products: int = Field(..., description="Segment 产品数量")
    market_share_percentage: float = Field(..., description="市场份额百分比")
    rank: int = Field(..., description="排名")
    avg_price: float = Field(..., description="平均价格")
    top_brand: str = Field(..., description="主要品牌")


class TopSegmentsByRevenueData(BaseModel):
    """Top Segments 主数据模型."""
    
    segments: List[SegmentRevenueData] = Field(..., description="排序后的 segment 列表")
    total_market_revenue: float = Field(..., description="总市场收入")
    total_market_volume: int = Field(..., description="总市场销量")
    total_products: int = Field(..., description="总产品数量")
    currency: str = Field(default="USD", description="货币单位")


class TopSegmentsByRevenueMetadata(BaseModel):
    """Top Segments 元数据模型."""
    
    filtered_asins_count: int = Field(..., description="过滤后的 ASIN 数量")
    total_segments: int = Field(..., description="总 segment 数量")
    returned_segments: int = Field(..., description="返回的 segment 数量")
    metric_type: str = Field(..., description="排序指标类型")
    calculation_timestamp: str = Field(..., description="计算时间戳")


class TopSegmentsByRevenueResponse(BaseModel):
    """Top 10 Segments by Revenue 响应模型."""
    
    data: TopSegmentsByRevenueData = Field(..., description="Segment 数据")
    metadata: TopSegmentsByRevenueMetadata = Field(..., description="元数据")
