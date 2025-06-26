"""Data models for Dashboard API responses."""

from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field


class BrandCategoryData(BaseModel):
    """Brand category revenue/volume data model.
    
    Matches the exact format expected by frontend components.
    """
    brand: str = Field(description="Brand name")
    dimmerRevenue: float = Field(default=0, description="Dimmer switches revenue")
    switchRevenue: float = Field(default=0, description="Light switches revenue")
    dimmerVolume: float = Field(default=0, description="Dimmer switches volume")
    switchVolume: float = Field(default=0, description="Light switches volume")


class BrandAnalysisResponse(BaseModel):
    """Response model for brand analysis API."""
    data: List[BrandCategoryData] = Field(description="Brand category data")
    project_id: str = Field(description="Project ID used for filtering")
    total_brands: int = Field(description="Total number of brands")
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


class ProductAnalysisResponse(BaseModel):
    """Response model for product analysis API."""
    priceVsRevenue: List[CategoryProducts] = Field(description="Price vs revenue data")
    topProducts: List[CategoryProducts] = Field(description="Top products data")
    project_id: str = Field(description="Project ID used for filtering")
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
    project_id: str = Field(description="Project ID used for filtering")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# Market Insights Models
class SegmentData(BaseModel):
    """Market segment data model."""
    segment: str = Field(description="Segment name")
    revenue: float = Field(description="Segment revenue")
    volume: float = Field(description="Segment volume")
    products: int = Field(description="Number of products")


class SegmentRevenue(BaseModel):
    """Segment revenue model."""
    dimmerSwitches: List[SegmentData] = Field(description="Dimmer switches segments")
    lightSwitches: List[SegmentData] = Field(description="Light switches segments")


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
    dimmerSwitches: List[PackageDistributionItem] = Field(description="Dimmer switches package distribution")
    lightSwitches: List[PackageDistributionItem] = Field(description="Light switches package distribution")
    project_id: str = Field(description="Project ID used for filtering")
    filtered_asin_count: int = Field(description="Number of ASINs in project filter")


# ==================== Review Insights Models ====================

class PainPoint(BaseModel):
    """Pain point data model."""
    aspect: str
    category: str
    severity: float
    frequency: int
    impactedProducts: int
    type: Literal["Physical", "Performance", "Usability"]

class CustomerLike(BaseModel):
    """Customer like data model."""
    feature: str
    category: str
    frequency: int
    satisfactionLevel: Literal["High", "Medium", "Low"]

class UnderservedUseCase(BaseModel):
    """Underserved use case data model."""
    useCase: str
    productAttribute: str
    gapLevel: float
    mentionCount: int

class ReviewInsightsResponse(BaseModel):
    """Review insights response model."""
    painPoints: List[PainPoint]
    customerLikes: List[CustomerLike]
    underservedUseCases: List[UnderservedUseCase]


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