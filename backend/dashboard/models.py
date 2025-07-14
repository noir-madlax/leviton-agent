"""Data models for Dashboard API responses."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class BrandCategoryData(BaseModel):
    """Brand category revenue/volume data model.
    
    Matches the exact format expected by frontend components.
    Enhanced to support dynamic categories.
    """
    brand: str = Field(description="Brand name")
    categories: Optional[Dict[str, Dict[str, float]]] = Field(default={}, description="Category-wise revenue and volume data")
    dimmerRevenue: float = Field(default=0, description="Dimmer switches revenue (compatibility)")
    switchRevenue: float = Field(default=0, description="Light switches revenue (compatibility)")
    dimmerVolume: float = Field(default=0, description="Dimmer switches volume (compatibility)")
    switchVolume: float = Field(default=0, description="Light switches volume (compatibility)")


class BrandAnalysisResponse(BaseModel):
    """Response model for brand analysis API.
    
    Enhanced to support dynamic categories and limited to top 10 brands by revenue.
    """
    data: List[BrandCategoryData] = Field(description="Top 10 brand category data")
    segmentNames: Optional[List[str]] = Field(default=[], description="List of category names in the project (kept as segmentNames for API compatibility)")
    segmentColors: Optional[List[str]] = Field(default=[], description="Colors for each category (kept as segmentColors for API compatibility)")
    project_id: str = Field(description="Project ID used for filtering")
    total_brands: int = Field(description="Number of top brands returned (up to 10)")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# Product Analysis Models
class ProductInfo(BaseModel):
    """Individual product info model."""
    id: str = Field(description="Product ID (ASIN)")
    name: str = Field(description="Product name")
    brand: str = Field(description="Brand name")
    price: float = Field(description="Product price")
    unitPrice: float = Field(description="Unit price")
    revenue: float = Field(description="Estimated revenue")
    volume: float = Field(description="Sales volume")
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
    packSize: str = Field(description="Pack size label")
    count: int = Field(description="Product count")
    percentage: float = Field(description="Percentage")
    salesVolume: float = Field(description="Sales volume")
    salesRevenue: Optional[float] = Field(default=0, description="Sales revenue")


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

class UnderservedUseCase(BaseModel):
    """Underserved use case data model with enhanced fields."""
    useCase: str
    productAttribute: str
    gapLevel: float
    mentionCount: int
    # Enhanced fields for frontend optimization
    categoryDefinition: Optional[str] = Field(default="", description="Category definition for tooltips")
    productCount: Optional[int] = Field(default=0, description="Number of products mentioning this use case")

class ReviewInsightsResponse(BaseModel):
    """Review insights response model."""
    painPoints: List[PainPoint]
    customerLikes: List[CustomerLike]
    underservedUseCases: List[UnderservedUseCase]
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