"""Data models for Dashboard API responses."""

from typing import List, Optional, Dict, Any, Literal, Union
from pydantic import BaseModel, Field
from core.models.filters import ProjectFilters


# ==================== 请求模型 ====================

class DashboardQueryOptions(BaseModel):
    """Dashboard 查询选项"""
    limit: Optional[int] = Field(default=None, description="限制返回结果数量")
    offset: Optional[int] = Field(default=0, description="分页偏移量")
    sort_by: Optional[str] = Field(default=None, description="排序字段")
    sort_order: Optional[Literal["asc", "desc"]] = Field(default="desc", description="排序方向")


class DashboardRequest(BaseModel):
    """Dashboard API 统一请求模型"""
    project_id: str = Field(..., description="项目ID，用于ASIN过滤")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="过滤条件JSON对象")
    options: Optional[DashboardQueryOptions] = Field(default=None, description="查询选项")

    def get_project_filters(self) -> ProjectFilters:
        """将请求中的 filters 转换为 ProjectFilters 对象"""
        if not self.filters:
            return ProjectFilters.empty()
        return ProjectFilters.from_dict(self.filters)

    def get_query_options(self) -> DashboardQueryOptions:
        """获取查询选项，如果为空则返回默认选项"""
        return self.options or DashboardQueryOptions()


class SpecificAnalysisRequest(DashboardRequest):
    """特定分析请求模型，可以扩展特殊参数"""
    pass


class PackagePreferenceRequest(DashboardRequest):
    """包装偏好分析请求模型"""
    metric_type: Optional[str] = Field(default=None, description="指标类型")


class CompetitorAnalysisRequest(DashboardRequest):
    """竞争对手分析请求模型"""
    selected_asins: Optional[List[str]] = Field(default=None, description="选中的ASIN列表")


class CompetitorSummaryRequest(BaseModel):
    """Competitor analysis summary request model."""
    project_id: str = Field(..., description="Project ID for filtering")
    selected_asins: List[str] = Field(..., description="List of ASINs to analyze")


# ==================== 响应模型 ====================

class BrandCategoryData(BaseModel):
    """Brand category revenue/volume data model.
    
    Matches the exact format expected by frontend components.
    Enhanced to support dynamic categories.
    """
    brand: str = Field(description="Brand name")
    categories: Optional[Dict[str, Dict[str, Union[float, int]]]] = Field(default={}, description="Category-wise revenue, volume, and product count data")
    dimmerRevenue: float = Field(default=0, description="Dimmer switches revenue (compatibility)")
    switchRevenue: float = Field(default=0, description="Light switches revenue (compatibility)")
    dimmerVolume: float = Field(default=0, description="Dimmer switches volume (compatibility)")
    switchVolume: float = Field(default=0, description="Light switches volume (compatibility)")


class BrandAnalysisResponse(BaseModel):
    """Response model for brand analysis API.
    
    Enhanced to support dynamic categories and returns all brands by revenue.
    """
    data: List[BrandCategoryData] = Field(description="All brand category data sorted by revenue")
    segmentNames: Optional[List[str]] = Field(default=[], description="List of category names in the project (kept as segmentNames for API compatibility)")
    segmentColors: Optional[List[str]] = Field(default=[], description="Colors for each category (kept as segmentColors for API compatibility)")
    project_id: str = Field(description="Project ID used for filtering")
    total_brands: int = Field(description="Number of brands returned (all brands)")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# Product Analysis Models
class ProductInfo(BaseModel):
    """Individual product info model."""
    id: str = Field(description="Product ID (ASIN)")
    name: str = Field(description="Product name")
    brand: str = Field(description="Brand name")
    price: float = Field(description="Product price")
    unitPrice: float = Field(description="Unit price")
    revenue: float = Field(description="Annual revenue")
    volume: float = Field(description="Annual sales volume")
    url: str = Field(description="Product URL")


class CategoryProducts(BaseModel):
    """Category products model."""
    category: str = Field(description="Category name")
    products: List[ProductInfo] = Field(description="Products in category")


class TopProductsData(BaseModel):
    """Top products data structure."""
    segments: Dict[str, List[ProductInfo]] = Field(description="Products by segment")
    dimmerSwitches: List[ProductInfo] = Field(description="Dimmer switches products (legacy)")
    lightSwitches: List[ProductInfo] = Field(description="Light switches products (legacy)")


class SegmentSummary(BaseModel):
    """Segment summary statistics."""
    totalRevenue: float = Field(description="Total revenue")
    totalVolume: float = Field(description="Total volume")
    productCount: int = Field(description="Product count")
    avgPrice: float = Field(description="Average price")
    topBrand: str = Field(description="Top brand")


class ProductAnalysisResponse(BaseModel):
    """Response model for product analysis API."""
    priceVsRevenue: List[CategoryProducts] = Field(description="Price vs revenue data")
    topProducts: TopProductsData = Field(description="Top products data with segments")
    segmentSummary: Dict[str, SegmentSummary] = Field(description="Summary statistics by segment")
    segmentNames: List[str] = Field(description="List of segment names")
    segmentColors: List[str] = Field(description="Colors for each segment")
    project_id: str = Field(description="Project ID used for filtering")
    total_products: int = Field(description="Total number of products analyzed")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# Pricing Analysis Models
class PriceStats(BaseModel):
    """Price statistics model."""
    min: float = Field(description="Minimum price")
    q1: float = Field(description="First quartile")
    median: float = Field(description="Median price")
    mean: float = Field(description="Mean price")
    q3: float = Field(description="Third quartile")
    max: float = Field(description="Maximum price")


class PriceStatsGroup(BaseModel):
    """Price statistics group model."""
    sku: PriceStats = Field(description="SKU price statistics")
    unit: PriceStats = Field(description="Unit price statistics")


class PriceDistribution(BaseModel):
    """Price distribution model."""
    category: str = Field(description="Category name")
    skuPrices: List[float] = Field(description="SKU prices")
    unitPrices: List[float] = Field(description="Unit prices")
    stats: PriceStatsGroup = Field(description="Price statistics")


class BrandPrices(BaseModel):
    """Brand prices model."""
    name: str = Field(description="Brand name")
    skuPrices: List[float] = Field(description="SKU prices")
    unitPrices: List[float] = Field(description="Unit prices")


class BrandPriceDistribution(BaseModel):
    """Brand price distribution model."""
    category: str = Field(description="Category name")
    brands: List[BrandPrices] = Field(description="Brand price data")


class PricingAnalysisResponse(BaseModel):
    """Response model for pricing analysis API."""
    priceDistribution: List[PriceDistribution] = Field(description="Price distribution data")
    brandPriceDistribution: List[BrandPriceDistribution] = Field(description="Brand price distribution data")
    segmentNames: List[str] = Field(description="List of segment names")
    segmentColors: List[str] = Field(description="Colors for each segment")
    project_id: str = Field(description="Project ID used for filtering")
    total_products: int = Field(description="Total number of products analyzed")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# Market Insights Models
class SegmentData(BaseModel):
    """Market segment data model."""
    segment: str = Field(description="Segment name")
    revenue: float = Field(description="Segment revenue")
    volume: float = Field(description="Segment volume")
    products: int = Field(description="Number of products")


class SegmentRevenue(BaseModel):
    """Segment revenue model with enhanced support for dynamic segments."""
    segments: List[SegmentData] = Field(description="All project segments")
    segmentNames: List[str] = Field(description="List of segment names")
    dimmerSwitches: List[SegmentData] = Field(description="Legacy: first half of segments")
    lightSwitches: List[SegmentData] = Field(description="Legacy: second half of segments")


class MarketInsightsResponse(BaseModel):
    """Response model for market insights API."""
    segmentRevenue: SegmentRevenue = Field(description="Segment revenue data")
    project_id: str = Field(description="Project ID used for filtering")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# Package Preference Models
class SameProductComparison(BaseModel):
    """Same product comparison model."""
    productName: str = Field(description="Product name")
    packSize: str = Field(description="Pack size label")
    packCount: int = Field(description="Pack count")
    salesVolume: float = Field(description="Sales volume")
    price: float = Field(description="Product price")
    unitPrice: float = Field(description="Unit price")


class PackageDistributionItem(BaseModel):
    """Package distribution item model."""
    name: Optional[str] = Field(description="Package type name")
    packSize: str = Field(description="Pack size label")
    value: float = Field(description="Revenue value")
    salesRevenue: float = Field(description="Sales revenue")
    count: int = Field(description="Product count")
    percentage: float = Field(description="Percentage")
    salesVolume: Optional[float] = Field(default=0, description="Sales volume (legacy compatibility)")


class PackagePreferenceResponse(BaseModel):
    """Response model for package preference API."""
    sameProductComparison: List[SameProductComparison] = Field(description="Same product comparison data")
    packageDistribution: List[PackageDistributionItem] = Field(description="Overall package distribution")
    segmentDistributions: Optional[Dict[str, List[PackageDistributionItem]]] = Field(default={}, description="Package distribution by segment")
    segmentNames: Optional[List[str]] = Field(default=[], description="List of segment names")
    segmentColors: Optional[List[str]] = Field(default=[], description="Colors for each segment")
    dimmerSwitches: List[PackageDistributionItem] = Field(description="Dimmer switches package distribution (legacy)")
    lightSwitches: List[PackageDistributionItem] = Field(description="Light switches package distribution (legacy)")
    project_id: str = Field(description="Project ID used for filtering")
    total_products: int = Field(description="Total number of products analyzed")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# ==================== Review Insights Models ====================

class PainPoint(BaseModel):
    """Pain point data model with enhanced fields."""
    aspect: str
    category: str
    severity: float
    frequency: int
    impactedProducts: int
    type: Literal["Physical", "Performance", "Usability"]
    # Enhanced fields for frontend optimization
    categoryDefinition: Optional[str] = Field(default="", description="Category definition for tooltips")
    totalMentions: Optional[int] = Field(default=0, description="Total mentions across all sentiments")
    negativeRate: Optional[float] = Field(default=0, description="Percentage of negative mentions")
    # New field for frontend mapping
    relatedDetailTexts: Optional[List[str]] = Field(default=None, description="Related detail texts for mapping")

class CustomerLike(BaseModel):
    """Customer like data model with enhanced fields."""
    feature: str
    category: str
    frequency: int
    satisfactionLevel: Literal["High", "Medium", "Low"]
    # Enhanced fields for frontend optimization
    categoryDefinition: Optional[str] = Field(default="", description="Category definition for tooltips")
    totalMentions: Optional[int] = Field(default=0, description="Total mentions across all sentiments")
    positiveRate: Optional[float] = Field(default=0, description="Percentage of positive mentions")
    # New field for frontend mapping
    relatedDetailTexts: Optional[List[str]] = Field(default=None, description="Related detail texts for mapping")

class AllUseCase(BaseModel):
    """All use case data model with enhanced fields."""
    useCase: str
    productAttribute: str
    satisfactionRate: float
    mentionCount: int
    positiveCount: int
    negativeCount: int
    # Enhanced fields for frontend optimization
    categoryDefinition: Optional[str] = Field(default="", description="Category definition for tooltips")
    productCount: Optional[int] = Field(default=0, description="Number of products mentioning this use case")
    # New field for frontend mapping
    relatedDetailTexts: Optional[List[str]] = Field(default=None, description="Related detail texts for mapping")

class UnderservedUseCase(BaseModel):
    """Underserved use case data model with enhanced fields."""
    useCase: str
    productAttribute: str
    gapLevel: float
    mentionCount: int
    # Enhanced fields for frontend optimization
    categoryDefinition: Optional[str] = Field(default="", description="Category definition for tooltips")
    productCount: Optional[int] = Field(default=0, description="Number of products mentioning this use case")
    # New field for frontend mapping
    relatedDetailTexts: Optional[List[str]] = Field(default=None, description="Related detail texts for mapping")

class ReviewInsightsResponse(BaseModel):
    """Review insights response model."""
    painPoints: List[PainPoint]
    customerLikes: List[CustomerLike]
    allUseCases: List[AllUseCase]
    underservedUseCases: List[UnderservedUseCase]
    totalUseMentions: int = Field(description="Total mentions across all use cases")
    project_id: str = Field(description="Project ID used for filtering")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# ==================== Competitor Analysis Models ====================

class CompetitorMatrixData(BaseModel):
    """Competitor matrix data model."""
    product: str
    category: str
    categoryType: Literal["Physical", "Performance"]
    mentions: int
    satisfactionRate: float
    positiveCount: int
    negativeCount: int
    totalReviews: int

class UseCaseMatrixData(BaseModel):
    """Use case matrix data model."""
    product: str
    useCase: str
    mentions: int
    satisfactionRate: float
    gapLevel: float

class UseCaseData(BaseModel):
    """Use case data container."""
    targetProducts: List[str]
    matrixData: List[UseCaseMatrixData]

class CompetitorAnalysisResponse(BaseModel):
    """Response model for competitor analysis API."""
    targetProducts: List[str]
    matrixData: List[CompetitorMatrixData]
    productTotalReviews: Dict[str, int]
    useCaseData: UseCaseData
    reviewContent: Optional[Dict[str, List[Dict[str, Any]]]] = Field(
        default=None, 
        description="Review content for matrix cell clicks, keyed by 'product_asin_category_name'"
    )
    project_id: str = Field(description="Project ID used for filtering")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# ==================== All Review Data Models ====================

class ReviewData(BaseModel):
    """Individual review data model."""
    id: str
    productId: str
    text: str
    sentiment: Literal["positive", "negative", "neutral"]
    category: str
    aspect: str
    rating: int
    verified: bool
    date: str
    brand: str

class AllReviewDataResponse(BaseModel):
    """Response model for all review data API."""
    data: Dict[str, List[ReviewData]] = Field(description="Review data grouped by aspect")
    project_id: str = Field(description="Project ID used for filtering")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")
    total_aspects: int = Field(description="Total number of aspects")
    total_reviews: int = Field(description="Total number of reviews") 

# ==================== Competitor Analysis Summary Models ====================

class CompetitorSummaryProduct(BaseModel):
    """Individual competitor product summary model."""
    asin: str = Field(description="Product ASIN")
    product_title: str = Field(description="Product title")
    rating: Optional[float] = Field(description="Product rating")
    brand: Optional[str] = Field(description="Product brand")
    product_url: Optional[str] = Field(description="Product URL")
    list_price: Optional[float] = Field(description="List price in USD")
    unique_reviews_count: int = Field(description="Number of unique reviews from review_aspect_data_view")
    additional_metrics: Optional[Dict[str, Any]] = Field(default=None, description="Additional metrics including sentiment distribution and category counts")


class CompetitorSummaryResponse(BaseModel):
    """Response model for competitor analysis summary API."""
    products: List[CompetitorSummaryProduct] = Field(description="List of competitor products with summary data")
    total_products: int = Field(description="Total number of products returned")
    selected_asins: List[str] = Field(description="List of ASINs that were requested")


# ==================== Competitor Analysis Matrix View Models ====================

class CompetitorMatrixViewFilter(BaseModel):
    """Filter for matrix view endpoint."""
    top_n: int = Field(description="Number of top aspect categories to include")


class CompetitorMatrixViewRequest(BaseModel):
    """Request model for competitor analysis matrix view API."""
    project_id: str = Field(..., description="Project ID for filtering")
    selected_asins: List[str] = Field(..., description="List of ASINs to analyze")
    aspect_type: Literal["phy_perf", "use"] = Field(..., description="Aspect type filter")
    filter: CompetitorMatrixViewFilter = Field(..., description="Filter configuration")


class AspectCategoryInfo(BaseModel):
    """Information about an aspect category."""
    category_id: int = Field(description="Category ID")
    category_name: str = Field(description="Category name")
    definition: str = Field(description="Category definition")


class ProductAspectData(BaseModel):
    """Aspect data for a specific product."""
    asin: str = Field(description="Product ASIN")
    aspect_data: List[Dict[str, Any]] = Field(description="List of aspect data for this product")


class CompetitorMatrixViewResponse(BaseModel):
    """Response model for competitor analysis matrix view API."""
    aspect_categories: List[AspectCategoryInfo] = Field(description="List of aspect categories sorted by total mentions")
    product_aspect_data: List[ProductAspectData] = Field(description="Aspect data for each product")
    selected_asins: List[str] = Field(description="List of ASINs that were requested")
    aspect_type: str = Field(description="Aspect type that was filtered")
    total_categories: int = Field(description="Total number of categories returned") 