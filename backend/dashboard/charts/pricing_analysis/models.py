"""Price Distribution Analysis API models and data structures."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from ..base_models import BaseRequestModel

# ==================== 请求模型 ====================

class PriceDistributionRequest(BaseRequestModel):
    """价格分布分析请求模型 - 按产品类型的价格分布"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": {
                    "categories": ["Light Switches", "Dimmer Switches"],
                    "brands": [],
                    "segments": [],
                    "extend_fields": {"smart_capability": "Smart"}
                },
                "timeframe": {
                    "period": "year"
                }
            }
        }

class PriceVsRevenueRequest(BaseRequestModel):
    """价格收入散点图分析请求模型"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": {
                    "categories": ["Light Switches", "Dimmer Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": [],
                    "extend_fields": {"smart_capability": "Smart"}
                },
                "timeframe": {
                    "period": "year"
                }
            }
        }

class BrandPriceDistributionRequest(BaseRequestModel):
    """品牌价格分布分析请求模型"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": {
                    "categories": ["Light Switches", "Dimmer Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": [],
                    "extend_fields": {"smart_capability": "Smart"}
                },
                "timeframe": {
                    "period": "year"
                }
            }
        }

class PriceDistributionOverviewRequest(BaseRequestModel):
    """价格分布概览请求模型 - 不使用过滤器，显示项目整体概览"""
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
                "filters": None,  # Overview不使用过滤器
                "timeframe": {
                    "period": "year"
                }
            }
        }

# ==================== 响应模型 ====================

class PriceStatistics(BaseModel):
    """价格统计模型"""
    min: float = Field(..., description="最小价格")
    q1: float = Field(..., description="第一四分位数")
    median: float = Field(..., description="中位数")
    mean: float = Field(..., description="平均价格")
    q3: float = Field(..., description="第三四分位数")
    max: float = Field(..., description="最大价格")

class CategoryPriceData(BaseModel):
    """单个分类的价格分布数据"""
    category: str = Field(..., description="分类名称")
    skuPrices: List[float] = Field(..., description="SKU价格列表")
    unitPrices: List[float] = Field(..., description="单位价格列表")
    productCount: int = Field(..., description="产品数量")
    stats: Dict[str, PriceStatistics] = Field(..., description="价格统计信息，包含sku和unit两种类型")

    class Config:
        json_schema_extra = {
            "example": {
                "category": "Light Switches",
                "skuPrices": [15.99, 25.99, 35.99],
                "unitPrices": [15.99, 25.99, 35.99],
                "productCount": 150,
                "stats": {
                    "sku": {
                        "min": 15.99,
                        "q1": 20.99,
                        "median": 25.99,
                        "mean": 26.50,
                        "q3": 30.99,
                        "max": 45.99
                    },
                    "unit": {
                        "min": 15.99,
                        "q1": 20.99,
                        "median": 25.99,
                        "mean": 26.50,
                        "q3": 30.99,
                        "max": 45.99
                    }
                }
            }
        }

class BrandPriceData(BaseModel):
    """品牌价格数据"""
    name: str = Field(..., description="品牌名称")
    skuPrices: List[float] = Field(..., description="SKU价格列表")
    unitPrices: List[float] = Field(..., description="单位价格列表")

class CategoryBrandDistribution(BaseModel):
    """分类的品牌价格分布"""
    category: str = Field(..., description="分类名称")
    brands: List[BrandPriceData] = Field(..., description="品牌价格数据列表")

class ProductDetail(BaseModel):
    """产品详细信息（用于散点图）"""
    id: str = Field(..., description="产品ID")
    name: str = Field(..., description="产品名称")
    brand: str = Field(..., description="品牌名称")
    price: float = Field(..., description="SKU价格")
    unitPrice: float = Field(..., description="单位价格")
    revenue: float = Field(..., description="收入")
    volume: float = Field(..., description="销量")
    url: str = Field(..., description="产品URL")

class TopProductsData(BaseModel):
    """Top产品数据（用于散点图）"""
    segments: Dict[str, List[ProductDetail]] = Field(..., description="按segment分组的产品")
    dimmerSwitches: List[ProductDetail] = Field(default_factory=list, description="调光开关产品（兼容性字段）")
    lightSwitches: List[ProductDetail] = Field(default_factory=list, description="灯开关产品（兼容性字段）")

class PriceDistributionMetadata(BaseModel):
    """价格分布分析元数据"""
    filtered_asins_count: int = Field(..., description="过滤后的ASIN数量")
    calculation_timestamp: str = Field(..., description="计算时间戳")
    timeframe_used: str = Field(..., description="使用的时间维度")
    data_source: str = Field(default="product_wide_table", description="数据来源表")
    categories_processed: List[str] = Field(..., description="处理的分类列表")

class PriceDistributionOverviewData(BaseModel):
    """价格分布概览单行数据"""
    segment: str = Field(..., description="分类名称")
    products: int = Field(..., description="产品数量")
    min_price: float = Field(..., description="最小价格")
    median_price: float = Field(..., description="中位数价格")  
    max_price: float = Field(..., description="最大价格")
    average_price: float = Field(..., description="平均价格")
    
    class Config:
        json_schema_extra = {
            "example": {
                "segment": "Light Switches + Smart",
                "products": 37,
                "min_price": 11.99,
                "median_price": 23.91,
                "max_price": 74.95,
                "average_price": 31.33
            }
        }

class PriceDistributionResponse(BaseModel):
    """价格分布API响应模型 - 按产品类型的价格分布"""
    priceDistribution: List[CategoryPriceData] = Field(..., description="按分类的价格分布数据")
    segmentNames: List[str] = Field(..., description="分类名称列表（兼容性字段）")
    segmentColors: List[str] = Field(..., description="分类颜色列表（兼容性字段）")
    metadata: PriceDistributionMetadata = Field(..., description="分析元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "priceDistribution": [
                    {
                        "category": "Light Switches",
                        "skuPrices": [15.99, 25.99, 35.99],
                        "unitPrices": [15.99, 25.99, 35.99],
                        "productCount": 150,
                        "stats": {
                            "sku": {
                                "min": 15.99,
                                "q1": 20.99,
                                "median": 25.99,
                                "mean": 26.50,
                                "q3": 30.99,
                                "max": 45.99
                            },
                            "unit": {
                                "min": 15.99,
                                "q1": 20.99,
                                "median": 25.99,
                                "mean": 26.50,
                                "q3": 30.99,
                                "max": 45.99
                            }
                        }
                    }
                ],
                "segmentNames": ["Light Switches", "Dimmer Switches"],
                "segmentColors": ["#FF6B6B", "#4ECDC4"],
                "metadata": {
                    "filtered_asins_count": 1250,
                    "calculation_timestamp": "2024-01-15T10:30:00Z",
                    "timeframe_used": "year",
                    "data_source": "product_wide_table",
                    "categories_processed": ["Light Switches", "Dimmer Switches"]
                }
            }
        }

class PriceVsRevenueResponse(BaseModel):
    """价格收入散点图API响应模型"""
    topProducts: TopProductsData = Field(..., description="Top产品数据（用于散点图）")
    segmentNames: List[str] = Field(..., description="分类名称列表（兼容性字段）")
    segmentColors: List[str] = Field(..., description="分类颜色列表（兼容性字段）")
    metadata: PriceDistributionMetadata = Field(..., description="分析元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "topProducts": {
                    "segments": {
                        "Light Switches": [
                            {
                                "id": "B01ABCD123",
                                "name": "Leviton Switch",
                                "brand": "Leviton",
                                "price": 25.99,
                                "unitPrice": 25.99,
                                "revenue": 50000.0,
                                "volume": 1923,
                                "url": "https://amazon.com/dp/B01ABCD123"
                            }
                        ]
                    },
                    "dimmerSwitches": [],
                    "lightSwitches": []
                },
                "segmentNames": ["Light Switches", "Dimmer Switches"],
                "segmentColors": ["#FF6B6B", "#4ECDC4"],
                "metadata": {
                    "filtered_asins_count": 1250,
                    "calculation_timestamp": "2024-01-15T10:30:00Z",
                    "timeframe_used": "year",
                    "data_source": "product_wide_table",
                    "categories_processed": ["Light Switches", "Dimmer Switches"]
                }
            }
        }

class BrandPriceDistributionResponse(BaseModel):
    """品牌价格分布API响应模型"""
    brandPriceDistribution: List[CategoryBrandDistribution] = Field(..., description="按分类的品牌价格分布")
    segmentNames: List[str] = Field(..., description="分类名称列表（兼容性字段）")
    segmentColors: List[str] = Field(..., description="分类颜色列表（兼容性字段）")
    metadata: PriceDistributionMetadata = Field(..., description="分析元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "brandPriceDistribution": [
                    {
                        "category": "Light Switches",
                        "brands": [
                            {
                                "name": "Leviton",
                                "skuPrices": [15.99, 25.99],
                                "unitPrices": [15.99, 25.99]
                            }
                        ]
                    }
                ],
                "segmentNames": ["Light Switches", "Dimmer Switches"],
                "segmentColors": ["#FF6B6B", "#4ECDC4"],
                "metadata": {
                    "filtered_asins_count": 1250,
                    "calculation_timestamp": "2024-01-15T10:30:00Z",
                    "timeframe_used": "year",
                    "data_source": "product_wide_table",
                    "categories_processed": ["Light Switches", "Dimmer Switches"]
                }
            }
        }

class PriceDistributionOverviewResponse(BaseModel):
    """价格分布概览API响应模型"""
    overview_data: List[PriceDistributionOverviewData] = Field(..., description="概览表格数据")
    metadata: PriceDistributionMetadata = Field(..., description="分析元数据")
    
    class Config:
        json_schema_extra = {
            "example": {
                "overview_data": [
                    {
                        "segment": "Light Switches + Smart",
                        "products": 37,
                        "min_price": 11.99,
                        "median_price": 23.91,
                        "max_price": 74.95,
                        "average_price": 31.33
                    },
                    {
                        "segment": "Dimmer Switches + Smart",
                        "products": 24,
                        "min_price": 14.97,
                        "median_price": 31.49,
                        "max_price": 189.90,
                        "average_price": 42.91
                    }
                ],
                "metadata": {
                    "filtered_asins_count": 152,
                    "calculation_timestamp": "2024-01-15T10:30:00Z",
                    "timeframe_used": "year",
                    "data_source": "product_wide_table",
                    "categories_processed": ["Light Switches + Smart", "Dimmer Switches + Smart"]
                }
            }
        }