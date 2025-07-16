"""FastAPI router for Dashboard module."""

import logging
import json
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends

from core.models.filters import ProjectFilters, FilterOptions
from dashboard.services.filter_service import FilterService
from .models import (
    BrandAnalysisResponse, BrandCategoryData,
    ProductAnalysisResponse, CategoryProducts, ProductInfo, TopProductsData, SegmentSummary,
    PricingAnalysisResponse, PriceDistribution, BrandPriceDistribution, PriceStats, PriceStatsGroup, BrandPrices,
    MarketInsightsResponse, SegmentRevenue, SegmentData,
    PackagePreferenceResponse, SameProductComparison, PackageDistributionItem,
    ReviewInsightsResponse,
    CompetitorAnalysisResponse,
    AllReviewDataResponse, ReviewData
)
from .services.brand_analysis_service import BrandAnalysisService
from .services.product_analysis_service import ProductAnalysisService
from .services.pricing_analysis_service import PricingAnalysisService
from .services.market_insights_service import MarketInsightsService
from .services.package_preference_service import PackagePreferenceService
from .services.review_insights_service import ReviewInsightsService
from .services.competitor_analysis_service import CompetitorAnalysisService
from .services.all_review_data_service import AllReviewDataService
from .services.project_overview_service import ProjectOverviewService

logger = logging.getLogger(__name__)

router = APIRouter()

# 公共的 filter 处理函数
def parse_filters(
    categories: Optional[str] = None,
    brands: Optional[str] = None,
    segments: Optional[str] = None,
    extend_fields: Optional[str] = None
) -> Dict[str, Any]:
    """解析前端传递的 filter 参数
    
    Args:
        categories: 逗号分隔的类别列表
        brands: 逗号分隔的品牌列表
        segments: 逗号分隔的段列表
        extend_fields: JSON 格式的扩展字段过滤器
    
    Returns:
        Dict containing parsed filter parameters
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse brands if provided
        brand_filters = brands.split(',') if brands else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        # Parse extend fields if provided
        extend_fields_filters = None
        if extend_fields:
            try:
                extend_fields_filters = json.loads(extend_fields)
            except json.JSONDecodeError:
                raise HTTPException(status_code=400, detail="Invalid JSON format for extend_fields parameter")
        
        return {
            'categories': category_filters,
            'brands': brand_filters,
            'segments': segment_filters,
            'extend_fields': extend_fields_filters
        }
    except Exception as e:
        logger.error(f"Error parsing filters: {e}")
        raise HTTPException(status_code=400, detail=f"Error parsing filters: {str(e)}")

def apply_filters_to_service(service, filters: Dict[str, Any]):
    """将解析后的过滤器应用到服务实例
    
    Args:
        service: 服务实例
        filters: 解析后的过滤器字典
    """
    if any(filters.values()):
        service.set_filters(
            categories=filters['categories'],
            brands=filters['brands'],
            segments=filters['segments'],
            extend_fields=filters['extend_fields']
        )

# 筛选器相关端点
@router.get("/projects/{project_id}/filter-options")
async def get_filter_options(
    project_id: str,
    categories: Optional[List[str]] = Query(None),
    brands: Optional[List[str]] = Query(None),
    segments: Optional[List[str]] = Query(None),
    extend_fields: Optional[str] = Query(None)  # JSON string
):
    """获取筛选器选项"""
    try:
        # 创建一个临时服务实例来获取项目ASINs
        temp_service = BrandAnalysisService(project_id)
        project_asins = temp_service.project_asins
        
        # 解析extend_fields
        extend_fields_dict = {}
        if extend_fields:
            try:
                extend_fields_dict = json.loads(extend_fields)
            except json.JSONDecodeError:
                extend_fields_dict = {}
        
        # 创建filter对象
        current_filters = ProjectFilters(
            categories=categories or [],
            brands=brands or [],
            segments=segments or [],
            extend_fields=extend_fields_dict
        )
        
        # 获取筛选器选项
        filter_service = FilterService(project_asins)
        options = filter_service.get_filter_options(current_filters)
        
        return {
            "categories": options.categories,
            "brands": options.brands,
            "segments": options.segments,
            "extend_fields": options.extend_fields
        }
    except Exception as e:
        logger.error(f"Error getting filter options: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/projects/{project_id}/charts/{chart_type}/data")
async def get_chart_data(
    project_id: str,
    chart_type: str,
    filters: Dict[str, Any]
):
    """获取图表数据"""
    try:
        # 解析筛选器
        project_filters = ProjectFilters.from_dict(filters)
        
        # 根据chart_type获取对应的服务
        service_class = get_chart_service_class(chart_type)
        service = service_class(project_id)
        
        # 应用筛选器
        if not project_filters.is_empty():
            service.set_project_filters(project_filters)
        
        # 获取数据
        data = await service.get_data()
        
        return {
            "data": data,
            "chart_type": chart_type,
            "project_id": project_id,
            "filters": filters
        }
        
    except Exception as e:
        logger.error(f"Error getting chart data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_chart_service_class(chart_type: str):
    """根据chart类型获取对应的服务类"""
    service_map = {
        'brand-analysis': BrandAnalysisService,
        'product-analysis': ProductAnalysisService,
        'pricing-analysis': PricingAnalysisService,
        'market-insights': MarketInsightsService,
        'package-preference': PackagePreferenceService,
        'review-insights': ReviewInsightsService,
        'competitor-analysis': CompetitorAnalysisService,
        'all-review-data': AllReviewDataService
    }
    
    if chart_type not in service_map:
        raise ValueError(f"Unknown chart type: {chart_type}")
    
    return service_map[chart_type]


@router.get("/projects/{project_id}/extend-fields")
async def get_project_extend_fields(
    project_id: str
):
    """Get extend field definitions for a specific project.
    
    Returns the list of extend field definitions that can be used for filtering,
    including field names, display names, types, and options.
    """
    try:
        # Use any service to get the extend fields (they all have the same method)
        service = BrandAnalysisService(project_id)
        extend_fields = service.get_project_extend_fields()
        
        return {
            "extend_fields": extend_fields,
            "project_id": project_id,
            "count": len(extend_fields)
        }
        
    except Exception as e:
        logger.error(f"Error getting project extend fields: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/brand-analysis", response_model=BrandAnalysisResponse)
async def get_brand_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters")
):
    """Get top 10 brand category revenue analysis for a specific project.
    
    This endpoint replaces the frontend getBrandCategoryRevenue() method
    with server-side implementation that applies project ASIN filtering.
    Returns only the top 10 brands by total revenue.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        # Initialize service with project-specific ASIN filtering
        service = BrandAnalysisService(project_id)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        # Get filtered data (new format with segments, limited to top 10)
        brand_data = service.get_data()
        
        # Extract data for response (fixed field mapping)
        brand_category_data = brand_data.get('brandCategoryRevenue', [])
        category_names = brand_data.get('categoryNames', [])
        category_colors = brand_data.get('categoryColors', [])
        
        # Prepare response with new format including categories
        response = BrandAnalysisResponse(
            data=[BrandCategoryData(**item) for item in brand_category_data],
            segmentNames=category_names,  # Keep API field name for compatibility
            segmentColors=category_colors,  # Keep API field name for compatibility
            project_id=project_id,
            total_brands=len(brand_category_data),  # Returns actual count (up to 10)
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Brand analysis API returned top {len(brand_category_data)} brands with {len(category_names)} categories for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in brand analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/product-analysis", response_model=ProductAnalysisResponse)
async def get_product_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters")
):
    """Get product analysis data for a specific project.
    
    Enhanced version: Returns complete data format including segment summary, 
    segment names, and colors for frontend compatibility.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        service = ProductAnalysisService(project_id)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        raw_data = service.get_data()
        
        # Convert segments dict to TopProductsData format
        segments_dict = raw_data['topProducts']['segments']
        segments_products = {}
        for segment_name, products_list in segments_dict.items():
            segments_products[segment_name] = [
                ProductInfo(**product) for product in products_list
            ]
        
        # Create TopProductsData with segments
        top_products_data = TopProductsData(
            segments=segments_products,
            dimmerSwitches=raw_data['topProducts'].get('dimmerSwitches', []),
            lightSwitches=raw_data['topProducts'].get('lightSwitches', [])
        )
        
        # Convert segment summaries to SegmentSummary objects
        segment_summaries = {}
        for segment_name, summary_dict in raw_data['segmentSummary'].items():
            segment_summaries[segment_name] = SegmentSummary(**summary_dict)
        
        response = ProductAnalysisResponse(
            priceVsRevenue=raw_data['priceVsRevenue'],
            topProducts=top_products_data,
            segmentSummary=segment_summaries,
            segmentNames=raw_data['segmentNames'],
            segmentColors=raw_data['segmentColors'],
            project_id=project_id,
            total_products=raw_data.get('totalProducts', 0),
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Product analysis API returned data for {len(raw_data['segmentNames'])} segments with {response.total_products} products for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in product analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pricing-analysis", response_model=PricingAnalysisResponse)
async def get_pricing_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters")
):
    """Get pricing analysis data for a specific project.
    
    Enhanced version: Returns complete pricing data with segment support.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        service = PricingAnalysisService(project_id)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        raw_data = service.get_data()
        
        # Convert price distribution data
        price_distribution = [
            PriceDistribution(**item) for item in raw_data['priceDistribution']
        ]
        
        # Convert brand price distribution data
        brand_price_distribution = [
            BrandPriceDistribution(**item) for item in raw_data['brandPriceDistribution']
        ]
        
        response = PricingAnalysisResponse(
            priceDistribution=price_distribution,
            brandPriceDistribution=brand_price_distribution,
            segmentNames=raw_data['categoryNames'],
            segmentColors=raw_data['categoryColors'],
            project_id=project_id,
            total_products=raw_data.get('totalProducts', 0),
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Pricing analysis API returned data for {len(raw_data['categoryNames'])} categories with {response.total_products} products for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in pricing analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-insights", response_model=MarketInsightsResponse)
async def get_market_insights(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters")
):
    """Get market insights data for a specific project.
    
    Enhanced version: Returns complete market insights with segment support.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        service = MarketInsightsService(project_id)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        raw_data = service.get_data()
        
        # Extract segmentRevenue data - it's already a dict structure
        segment_revenue_data = raw_data.get('segmentRevenue', {})
        
        # Convert segment data to SegmentData objects
        segment_data_list = []
        if 'segments' in segment_revenue_data:
            segments = segment_revenue_data['segments']
            
            for item in segments:
                try:
                    if isinstance(item, dict):
                        segment_data_list.append(SegmentData(**item))
                except Exception as e:
                    logger.error(f"Error creating SegmentData for item {item}: {e}")
        
        # Create SegmentRevenue object
        dimmer_switches = []
        light_switches = []
        
        dimmer_items = segment_revenue_data.get('dimmerSwitches', [])
        for item in dimmer_items:
            try:
                if isinstance(item, dict):
                    dimmer_switches.append(SegmentData(**item))
            except Exception as e:
                logger.error(f"Error creating SegmentData for dimmer item {item}: {e}")
        
        light_items = segment_revenue_data.get('lightSwitches', [])
        for item in light_items:
            try:
                if isinstance(item, dict):
                    light_switches.append(SegmentData(**item))
            except Exception as e:
                logger.error(f"Error creating SegmentData for light item {item}: {e}")
        
        segment_revenue = SegmentRevenue(
            segments=segment_data_list,
            segmentNames=segment_revenue_data.get('segmentNames', []),
            dimmerSwitches=dimmer_switches,
            lightSwitches=light_switches
        )
        
        response = MarketInsightsResponse(
            segmentRevenue=segment_revenue,
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Market insights API returned data for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in market insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/package-preference", response_model=PackagePreferenceResponse)
async def get_package_preference(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters"),
    metric_type: Optional[str] = Query("revenue", description="Metric type for calculations: 'revenue' or 'count'")
):
    """Get package preference data for a specific project.
    
    Enhanced version: Returns complete package preference data with segment support.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        service = PackagePreferenceService(project_id)
        
        # Set metric type if provided
        if metric_type:
            service.set_metric_type(metric_type)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        raw_data = service.get_data()
        
        # Convert package distribution data (this is a list, not dict)
        package_distribution = [
            PackageDistributionItem(**item) for item in raw_data['packageDistribution']
        ]
        
        # Convert segment distributions data (this is a dict with segment names as keys)
        segment_distributions = {}
        if 'segmentDistributions' in raw_data:
            for segment_name, distribution_list in raw_data['segmentDistributions'].items():
                segment_distributions[segment_name] = [
                    PackageDistributionItem(**item) for item in distribution_list
                ]
        
        # Convert same product comparison data
        same_product_comparisons = [
            SameProductComparison(**item) for item in raw_data['sameProductComparison']
        ]
        
        response = PackagePreferenceResponse(
            packageDistribution=package_distribution,
            segmentDistributions=segment_distributions,
            sameProductComparison=same_product_comparisons,
            segmentNames=raw_data.get('segmentNames', []),
            segmentColors=raw_data.get('segmentColors', []),
            dimmerSwitches=[PackageDistributionItem(**item) for item in raw_data.get('dimmerSwitches', [])],
            lightSwitches=[PackageDistributionItem(**item) for item in raw_data.get('lightSwitches', [])],
            project_id=project_id,
            total_products=raw_data.get('totalProducts', 0),
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Package preference API returned data for {len(raw_data['segmentNames'])} segments with {response.total_products} products for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in package preference: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/review-insights", response_model=ReviewInsightsResponse)
async def get_review_insights_data(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters")
):
    """Get review insights data for a specific project.
    
    Enhanced version: Returns complete review insights with segment support.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        service = ReviewInsightsService(project_id)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        raw_data = service.get_data()
        
        response = ReviewInsightsResponse(
            **raw_data,
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Review insights API returned data for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in review insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/competitor-analysis", response_model=CompetitorAnalysisResponse)
async def get_competitor_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters"),
    selected_asins: Optional[str] = Query(None, description="Comma-separated list of ASINs to analyze")
):
    """Get competitor analysis data for a specific project.
    
    Enhanced version: Returns complete competitor analysis with segment support.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        # Parse selected ASINs if provided
        selected_asins_list = selected_asins.split(',') if selected_asins else None
        
        service = CompetitorAnalysisService(project_id, selected_asins=selected_asins_list)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        raw_data = service.get_data()
        
        response = CompetitorAnalysisResponse(
            targetProducts=raw_data.get('targetProducts', []),
            matrixData=raw_data.get('matrixData', []),
            productTotalReviews=raw_data.get('productTotalReviews', {}),
            useCaseData=raw_data.get('useCaseData', {'targetProducts': [], 'matrixData': []}),
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Competitor analysis API returned data for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in competitor analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/all-review-data", response_model=AllReviewDataResponse)
async def get_all_review_data(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters")
):
    """Get all review data for a specific project.
    
    Enhanced version: Returns complete review data with segment support.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        service = AllReviewDataService(project_id)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        raw_data = service.get_data()
        
        # Convert grouped review data to ReviewData objects
        converted_data = {}
        for aspect, reviews in raw_data['data'].items():
            converted_data[aspect] = [ReviewData(**review) for review in reviews]
        
        response = AllReviewDataResponse(
            data=converted_data,
            project_id=project_id,
            filtered_asin_count=len(service.project_asins),
            total_aspects=raw_data.get('total_aspects', 0),
            total_reviews=raw_data.get('total_reviews', 0)
        )
        
        logger.info(f"All review data API returned {len(raw_data['data'])} aspects with {response.total_reviews} reviews for project {project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in all review data: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-overview")
async def get_project_overview(
    project_id: str = Query(..., description="Project ID"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    brands: Optional[str] = Query(None, description="Comma-separated list of brands to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    extend_fields: Optional[str] = Query(None, description="JSON string of extend field filters")
):
    """Get project overview data with optional filtering.
    
    Enhanced version: Returns complete project overview with segment support.
    """
    try:
        # 解析过滤器
        filters = parse_filters(categories, brands, segments, extend_fields)
        
        service = ProjectOverviewService(project_id)
        
        # Apply filters if provided
        apply_filters_to_service(service, filters)
        
        overview_data = service.get_data()
        
        logger.info(f"Project overview API returned data for project {project_id}")
        return overview_data
        
    except Exception as e:
        logger.error(f"Error in project overview: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/project-segments")
async def get_project_segments(
    project_id: str = Query(..., description="Project ID")
):
    """Get available segments for a project.
    
    Returns all available segments for the specified project.
    """
    try:
        # Use any service to get segments (they all have the same method)
        service = ProjectOverviewService(project_id)
        segments = service.get_project_segments()
        
        return {
            "segments": segments,
            "project_id": project_id,
            "count": len(segments)
        }
        
    except Exception as e:
        logger.error(f"Error getting project segments: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-asins")
async def get_available_asins(
    project_id: str = Query(..., description="Project ID")
):
    """Get available ASINs for a project.
    
    Returns all available ASINs for the specified project.
    """
    try:
        # Use any service to get ASINs (they all have the same method)
        service = ProjectOverviewService(project_id)
        asins = service.project_asins
        
        return {
            "asins": asins,
            "project_id": project_id,
            "count": len(asins)
        }
        
    except Exception as e:
        logger.error(f"Error getting available ASINs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 