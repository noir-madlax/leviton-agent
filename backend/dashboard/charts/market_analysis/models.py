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


class CategoryTopSegments(BaseModel):
    """Top segments grouped under a specific category."""
    
    category: str = Field(..., description="类别名称")
    total_revenue: float = Field(..., description="该类别总收入")
    total_volume: int = Field(..., description="该类别总销量")
    total_products: int = Field(..., description="该类别产品总数")
    segments: List[SegmentRevenueData] = Field(..., description="该类别下的 Top-N segments")


class TopSegmentsByRevenueData(BaseModel):
    """Top Segments 主数据模型."""
    
    top_segments_by_category: List[CategoryTopSegments] = Field(..., description="按类别分组后的 Top-N segment 列表")
    total_market_revenue: float = Field(..., description="总市场收入")
    total_market_volume: int = Field(..., description="总市场销量")
    total_products: int = Field(..., description="总产品数量")
    currency: str = Field(default="USD", description="货币单位")


class TopSegmentsByRevenueMetadata(BaseModel):
    """Top Segments 元数据模型."""
    
    filtered_asins_count: int = Field(..., description="过滤后的 ASIN 数量")
    total_categories: int = Field(..., description="总类别数量")
    total_segments: int = Field(..., description="所有类别下去重后的 segment 总数")
    returned_segments: int = Field(..., description="返回的 segment 条目数量（所有类别合计）")
    metric_type: str = Field(..., description="排序指标类型")
    timeframe_used: str = Field(..., description="使用的时间范围")
    limit_per_category: int = Field(..., description="每个类别返回的 segment 上限")
    calculation_timestamp: str = Field(..., description="计算时间戳")


class TopSegmentsByRevenueResponse(BaseModel):
    """Top 10 Segments by Revenue 响应模型."""
    
    data: TopSegmentsByRevenueData = Field(..., description="Segment 数据")
    metadata: TopSegmentsByRevenueMetadata = Field(..., description="元数据")


# Package Type Distribution Models
class PackageTypeDistributionRequest(BaseRequestModel):
    """Request model for Package Type Distribution analysis."""
    
    metric_type: Literal["revenue", "products"] = Field(
        default="revenue", 
        description="分析指标类型: revenue(收入) 或 products(产品数量)"
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
                "metric_type": "revenue"
            }
        }


class PackageTypeData(BaseModel):
    """Single package type data model."""
    
    package_type: str = Field(..., description="包装类型名称")
    revenue: float = Field(..., description="总收入")
    volume: int = Field(..., description="总销量") 
    product_count: int = Field(..., description="产品数量")
    percentage: float = Field(..., description="占比百分比")
    rank: int = Field(..., description="排名")


class CategoryPackageDistribution(BaseModel):
    """Package distribution data for a specific category."""
    
    category: str = Field(..., description="产品类别名称")
    total_revenue: float = Field(..., description="该类别总收入")
    total_volume: int = Field(..., description="该类别总销量")
    total_products: int = Field(..., description="该类别产品总数")
    package_types: List[PackageTypeData] = Field(..., description="该类别的包装类型分布")


class PackageTypeDistributionData(BaseModel):
    """Package Type Distribution main data model."""
    
    overall_distribution: List[PackageTypeData] = Field(..., description="总体包装类型分布")
    distribution_by_category: List[CategoryPackageDistribution] = Field(..., description="按类别分组的包装类型分布")
    total_market_revenue: float = Field(..., description="总市场收入")
    total_market_volume: int = Field(..., description="总市场销量")
    total_products: int = Field(..., description="总产品数量")
    metric_type: str = Field(..., description="当前使用的指标类型")
    currency: str = Field(default="USD", description="货币单位")


class PackageTypeDistributionMetadata(BaseModel):
    """Package Type Distribution metadata model."""
    
    filtered_asins_count: int = Field(..., description="过滤后的ASIN数量")
    total_categories: int = Field(..., description="总类别数量")
    total_package_types: int = Field(..., description="发现的包装类型数量")
    metric_type: str = Field(..., description="分析指标类型")
    timeframe_used: str = Field(..., description="使用的时间范围")
    calculation_timestamp: str = Field(..., description="计算时间戳")


class PackageTypeDistributionResponse(BaseModel):
    """Package Type Distribution response model."""
    
    data: PackageTypeDistributionData = Field(..., description="包装类型分布数据")
    metadata: PackageTypeDistributionMetadata = Field(..., description="元数据")
