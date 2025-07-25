"""FastAPI router for Dashboard module."""

import logging
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query, Depends

from core.models.filters import ProjectFilters, FilterOptions
from core.database.connection import get_supabase_client
from dashboard.services.filter_service import FilterService
from .models import (
    BrandAnalysisResponse, BrandCategoryData,
    ProductAnalysisResponse, CategoryProducts, ProductInfo, TopProductsData, SegmentSummary,
    PricingAnalysisResponse, PriceDistribution, BrandPriceDistribution, PriceStats, PriceStatsGroup, BrandPrices,
    MarketInsightsResponse, SegmentRevenue, SegmentData,
    PackagePreferenceResponse, SameProductComparison, PackageDistributionItem,
    ReviewInsightsResponse,
    CompetitorAnalysisResponse,
    AllReviewDataResponse, ReviewData,
    DashboardRequest, PackagePreferenceRequest, CompetitorAnalysisRequest,
    CompetitorSummaryResponse, CompetitorSummaryProduct, CompetitorSummaryRequest,
    CompetitorMatrixViewResponse, CompetitorMatrixViewRequest, AspectCategoryInfo, ProductAspectData
)
from .charts.sales_trend.models import SalesTrendRequest, SalesTrendResponse
from .charts.sales_trend.services import SalesTrendService
from .charts.customerSatisfaction.models import CustomerSatisfactionRequest, CustomerSatisfactionResponse
from .charts.customerSatisfaction.services import CustomerSatisfactionService
from .decorators import with_dashboard_service, log_request_response
from .services.brand_analysis_service import BrandAnalysisService
from .services.product_analysis_service import ProductAnalysisService
from .services.pricing_analysis_service import PricingAnalysisService
from .services.market_insights_service import MarketInsightsService
from .services.package_preference_service import PackagePreferenceService
from .services.review_insights_service import ReviewInsightsService
from .services.competitor_analysis_service import CompetitorAnalysisService
from .services.all_review_data_service import AllReviewDataService
from .services.project_overview_service import ProjectOverviewService
from .services.competitor_summary_service import CompetitorSummaryService
from review_analysis.services.db_review_analysis import DatabaseReviewAnalysisService
from .charts.api import router as charts_router

logger = logging.getLogger(__name__)

router = APIRouter()
router.include_router(charts_router, prefix="/charts")

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


@router.post("/brand-analysis", response_model=BrandAnalysisResponse)
@with_dashboard_service(BrandAnalysisService)
@log_request_response
async def get_brand_analysis(
    service: BrandAnalysisService,
    request: DashboardRequest
):
    """Get brand category revenue analysis for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        }
    }

    Returns all brands by total revenue (sorted descending).
    """
    # Get filtered data (new format with segments, returns all brands)
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
        project_id=request.project_id,
        total_brands=len(brand_category_data),  # Returns actual count (all brands)
        filtered_asin_count=len(service.project_asins)
    )

    logger.info(f"Brand analysis API returned all {len(brand_category_data)} brands with {len(category_names)} categories for project {request.project_id}")
    return response


@router.post("/sales-trend", response_model=SalesTrendResponse)
async def get_sales_trend(request: SalesTrendRequest):
    """获取品牌销售趋势数据
    
    提供Top 10品牌的月度销售趋势数据，支持revenue和volume双指标展示。
    用于前端StackedAreaChart组件的数据源。
    
    请求格式：
    {
        "project_id": "项目ID",
        "filters": {
            "categories": ["Light Switches"],
            "brands": [],
            "segments": [],
            "extend_fields": {"smart_capability": "Smart"}
        },
        "date_range": {
            "start_date": "2024-01-01",
            "end_date": "2024-06-30"
        }
    }
    
    返回格式：
    {
        "trend_data": [
            {
                "month": "2024-01",
                "Leviton": {"revenue": 850000, "volume": 12000},
                "Lutron": {"revenue": 720000, "volume": 9000}
            }
        ],
        "brands": ["Leviton", "Lutron", "GE"],
        "summary": {
            "total_brands": 3,
            "date_range": {"start": "2024-01", "end": "2024-06"},
            "total_revenue": 15230000,
            "total_volume": 89400
        }
    }
    """
    try:
        logger.info(f"Sales trend analysis request for project {request.project_id}")
        
        # 获取时间范围参数
        date_range = request.get_date_range_filter()
        
        # 创建服务实例
        service = SalesTrendService(
            project_id=request.project_id,
            filters=request.filters,
            date_range=date_range
        )
        
        # 获取分析数据
        trend_data = service.get_data()
        
        # 验证数据结构
        if not isinstance(trend_data, dict):
            raise ValueError("Service returned invalid data format")
        
        # 构建响应
        response = SalesTrendResponse(
            trend_data=trend_data.get("trend_data", []),
            brands=trend_data.get("brands", []),
            summary=trend_data.get("summary", {
                "total_brands": 0,
                "date_range": {"start": "", "end": ""},
                "total_revenue": 0.0,
                "total_volume": 0
            })
        )
        
        logger.info(
            f"Sales trend analysis completed for project {request.project_id}: "
            f"{len(response.brands)} brands, {len(response.trend_data)} months"
        )
        
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in sales trend analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error in sales trend analysis: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during sales trend analysis: {str(e)}"
        )


@router.post("/product-analysis", response_model=ProductAnalysisResponse)
@with_dashboard_service(ProductAnalysisService)
@log_request_response
async def get_product_analysis(
    service: ProductAnalysisService,
    request: DashboardRequest
):
    """Get product analysis data for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        }
    }

    Enhanced version: Returns complete data format including segment summary,
    segment names, and colors for frontend compatibility.
    """
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
        project_id=request.project_id,
        total_products=raw_data.get('totalProducts', 0),
        filtered_asin_count=len(service.project_asins)
    )

    logger.info(f"Product analysis API returned data for {len(raw_data['segmentNames'])} segments with {response.total_products} products for project {request.project_id}")
    return response


@router.post("/pricing-analysis", response_model=PricingAnalysisResponse)
@with_dashboard_service(PricingAnalysisService)
@log_request_response
async def get_pricing_analysis(
    service: PricingAnalysisService,
    request: DashboardRequest
):
    """Get pricing analysis data for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        }
    }

    Enhanced version: Returns complete pricing data with segment support.
    """
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
        project_id=request.project_id,
        total_products=raw_data.get('totalProducts', 0),
        filtered_asin_count=len(service.project_asins)
    )

    logger.info(f"Pricing analysis API returned data for {len(raw_data['categoryNames'])} categories with {response.total_products} products for project {request.project_id}")
    return response


@router.post("/market-insights", response_model=MarketInsightsResponse)
@with_dashboard_service(MarketInsightsService)
@log_request_response
async def get_market_insights(
    service: MarketInsightsService,
    request: DashboardRequest
):
    """Get market insights data for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        }
    }

    Enhanced version: Returns complete market insights with segment support.
    """
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
        project_id=request.project_id,
        filtered_asin_count=len(service.project_asins)
    )

    logger.info(f"Market insights API returned data for project {request.project_id}")
    return response


@router.post("/package-preference", response_model=PackagePreferenceResponse)
@with_dashboard_service(PackagePreferenceService)
@log_request_response
async def get_package_preference(
    service: PackagePreferenceService,
    request: PackagePreferenceRequest
):
    """Get package preference data for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        },
        "metric_type": "revenue"  // 可选: "revenue" 或 "count"
    }

    Enhanced version: Returns complete package preference data with segment support.
    """
    # Set metric type if provided
    logger.info(f"Package preference API received request: {request}")
    if request.metric_type:
        service.set_metric_type(request.metric_type)
        logger.info(f"Package preference API set metric type to {request.metric_type}")
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
        project_id=request.project_id,
        total_products=raw_data.get('totalProducts', 0),
        filtered_asin_count=len(service.project_asins)
    )

    logger.info(f"Package preference API returned data for {len(raw_data['segmentNames'])} segments with {response.total_products} products for project {request.project_id}")
    return response


@router.post("/review-insights", response_model=ReviewInsightsResponse)
@with_dashboard_service(ReviewInsightsService)
@log_request_response
async def get_review_insights_data(
    service: ReviewInsightsService,
    request: DashboardRequest
):
    """Get review insights data for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        }
    }

    Enhanced version: Returns complete review insights with segment support.
    """
    raw_data = service.get_data()

    response = ReviewInsightsResponse(
        **raw_data,
        project_id=request.project_id,
        filtered_asin_count=len(service.project_asins)
    )

    logger.info(f"Review insights API returned data for project {request.project_id}")
    return response


@router.get("/review-analysis/{project_id}/final-category-assignments")
async def get_final_category_assignments(project_id: str):
    """Get the complete final category assignments JSON structure.
    
    Returns a detailed JSON structure showing all categories and their assigned aspects
    after the review analysis consolidation process is complete.
    
    GET /api/v1/dashboard/review-analysis/{project_id}/final-category-assignments
    
    Response format:
    {
        "project_id": "...",
        "generated_at": "2025-01-18T...",
        "summary": {
            "total_categories": 45,
            "total_aspects": 256,
            "categories_by_type": {"phy": 20, "perf": 15, "use": 10}
        },
        "categories": {
            "Category Name": {
                "definition": "Category definition...",
                "aspect_type": "phy|perf|use",
                "aspect_count": 12,
                "aspects": [
                    {
                        "aspect_pk": 123,
                        "detail_text": "specific aspect text",
                        "product_id": "B00MXCRAX8",
                        "local_id": "A"
                    },
                    ...
                ]
            },
            ...
        }
    }
    """
    try:
        # Create service instance to access the method we added
        service = DatabaseReviewAnalysisService()
        
        # Get the final category assignments JSON
        final_assignments = await service._get_final_category_assignments_json(project_id)
        
        logger.info(f"Final category assignments API returned data for project {project_id}")
        logger.info(f"Summary: {final_assignments.get('summary', {})}")
        
        return final_assignments
        
    except Exception as e:
        logger.error(f"Error getting final category assignments for project {project_id}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get final category assignments: {str(e)}"
        ) from e


@router.post("/competitor-analysis", response_model=CompetitorAnalysisResponse)
@with_dashboard_service(CompetitorAnalysisService)
@log_request_response
async def get_competitor_analysis(
    service: CompetitorAnalysisService,
    request: CompetitorAnalysisRequest
):
    """Get competitor analysis data for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        },
        "selected_asins": ["ASIN1", "ASIN2"]  // 可选: 要分析的ASIN列表
    }

    Enhanced version: Returns complete competitor analysis with segment support.
    Uses materialized view for improved performance and review content.
    """
    # Use the new materialized view method for enhanced performance
    raw_data = service.get_data_with_materialized_view(include_review_content=True)

    response = CompetitorAnalysisResponse(
        targetProducts=raw_data.get('targetProducts', []),
        matrixData=raw_data.get('matrixData', []),
        productTotalReviews=raw_data.get('productTotalReviews', {}),
        useCaseData=raw_data.get('useCaseData', {'targetProducts': [], 'matrixData': []}),
        reviewContent=raw_data.get('reviewContent', {}),  # Include review content for cell clicks
        project_id=request.project_id,
        filtered_asin_count=len(service.project_asins)
    )

    logger.info(f"Competitor analysis API returned data for project {request.project_id} using materialized view")
    return response


@router.get("/competitor-analysis/{project_id}/cell-reviews")
@log_request_response
async def get_competitor_cell_reviews(
    project_id: str,
    product_asin: str = Query(..., description="Product ASIN"),
    category_name: str = Query(..., description="Category name"),
    limit: int = Query(50, description="Maximum number of reviews to return"),
    offset: int = Query(0, description="Offset for pagination")
):
    """Get reviews for a specific matrix cell (product-category combination).
    
    GET请求，用于获取矩阵单元格的详细评论数据：
    /competitor-analysis/{project_id}/cell-reviews?product_asin=B00NG0ELL0&category_name=Installation Process&limit=50&offset=0
    
    Returns:
        List of review objects for the specified cell
    """
    try:
        # Create service instance for the project
        service = CompetitorAnalysisService(project_id)
        
        # Get reviews for the specific cell
        reviews = service.get_reviews_for_cell(product_asin, category_name, limit, offset)
        
        logger.info(f"Cell reviews API returned {len(reviews)} reviews for {product_asin}-{category_name}")
        return {
            "reviews": reviews,
            "product_asin": product_asin,
            "category_name": category_name,
            "total_returned": len(reviews),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error getting cell reviews for {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cell reviews: {str(e)}")





@router.post("/competitor-analysis/summary", response_model=CompetitorSummaryResponse)
@log_request_response
async def get_competitor_summary(request: CompetitorSummaryRequest):
    """Get competitor analysis summary for selected ASINs.
    
    POST请求，获取选中ASINs的竞争对手分析摘要：
    {
        "project_id": "project-uuid",
        "selected_asins": ["ASIN1", "ASIN2", "ASIN3"]
    }
    
    Returns:
        Summary data including product info, review counts, and additional metrics
    """
    try:
        logger.info(f"Competitor summary request for ASINs: {request.selected_asins}")
        
        # Use the service to get competitor summary data
        service = CompetitorSummaryService()
        summary_data = await service.get_competitor_summary(request.project_id, request.selected_asins)
        
        # Convert to response model
        products = []
        for product_data in summary_data['products']:
            products.append(CompetitorSummaryProduct(
                asin=product_data['asin'],
                product_title=product_data['product_title'],
                rating=product_data['rating'],
                brand=product_data['brand'],
                product_url=product_data['product_url'],
                list_price=product_data['list_price'],
                unique_reviews_count=product_data['unique_reviews_count'],
                additional_metrics=product_data['additional_metrics']
            ))
        
        response = CompetitorSummaryResponse(
            products=products,
            total_products=summary_data['total_products'],
            selected_asins=summary_data['selected_asins']
        )
        
        logger.info(f"Competitor summary API returned data for {len(products)} products")
        return response
        
    except Exception as e:
        logger.error(f"Error in competitor summary API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get competitor summary: {str(e)}")


@router.post("/competitor-analysis/matrix-view", response_model=CompetitorMatrixViewResponse)
@log_request_response
async def get_competitor_matrix_view(request: CompetitorMatrixViewRequest):
    """Get competitor analysis matrix view data.
    
    POST请求，获取选中ASINs的矩阵视图数据：
    {
        "project_id": "project-uuid",
        "selected_asins": ["ASIN1", "ASIN2", "ASIN3"],
        "aspect_type": "phy_perf",
        "filter": {
            "top_n": 10
        }
    }
    
    Returns:
        Matrix view data with top aspect categories and product-category statistics
    """
    try:
        logger.info(f"Competitor matrix view request for ASINs: {request.selected_asins}, aspect_type: {request.aspect_type}")
        
        # Use the service to get matrix view data
        service = CompetitorSummaryService()
        matrix_data = await service.get_matrix_view_data(
            request.project_id,
            request.selected_asins,
            request.aspect_type,
            request.filter.top_n
        )
        
        # Convert to response model
        aspect_categories = []
        for category_data in matrix_data['aspect_categories']:
            aspect_categories.append(AspectCategoryInfo(
                category_id=category_data['category_id'],
                category_name=category_data['category_name'],
                definition=category_data['definition']
            ))
        
        product_aspect_data = []
        for aspect_data in matrix_data['product_aspect_data']:
            product_aspect_data.append(ProductAspectData(
                asin=aspect_data['asin'],
                aspect_data=aspect_data['aspect_data']
            ))
        
        response = CompetitorMatrixViewResponse(
            aspect_categories=aspect_categories,
            product_aspect_data=product_aspect_data,
            selected_asins=matrix_data['selected_asins'],
            aspect_type=matrix_data['aspect_type'],
            total_categories=matrix_data['total_categories']
        )
        
        logger.info(f"Competitor matrix view API returned data for {len(aspect_categories)} categories")
        return response
        
    except Exception as e:
        logger.error(f"Error in competitor matrix view API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get competitor matrix view: {str(e)}")


@router.post("/all-review-data", response_model=AllReviewDataResponse)
@with_dashboard_service(AllReviewDataService)
@log_request_response
async def get_all_review_data(
    service: AllReviewDataService,
    request: DashboardRequest
):
    """Get all review data for a specific project.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        }
    }

    Enhanced version: Returns complete review data with segment support.
    """
    raw_data = service.get_data()

    # Convert grouped review data to ReviewData objects
    converted_data = {}
    for aspect, reviews in raw_data['data'].items():
        converted_data[aspect] = [ReviewData(**review) for review in reviews]

    response = AllReviewDataResponse(
        data=converted_data,
        project_id=request.project_id,
        filtered_asin_count=len(service.project_asins),
        total_aspects=raw_data.get('total_aspects', 0),
        total_reviews=raw_data.get('total_reviews', 0)
    )

    logger.info(f"All review data API returned {len(raw_data['data'])} aspects with {response.total_reviews} reviews for project {request.project_id}")
    return response


@router.post("/project-overview")
@with_dashboard_service(ProjectOverviewService)
@log_request_response
async def get_project_overview(
    service: ProjectOverviewService,
    request: DashboardRequest
):
    """Get project overview data with optional filtering.

    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1", "category2"],
            "brands": ["brand1", "brand2"],
            "segments": ["segment1", "segment2"],
            "extend_fields": {"field_name": "value"}
        }
    }

    Enhanced version: Returns complete project overview with segment support.
    """
    overview_data = service.get_data()

    logger.info(f"Project overview API returned data for project {request.project_id}")
    return overview_data


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


@router.get("/projects/{project_id}/filter-defaults")
async def get_project_filter_defaults(project_id: str):
    """获取项目的默认筛选器配置
    
    从 project_filter_defaults 表中读取项目级别的筛选器配置，
    并转换为前端可以直接使用的 ProjectFilters 格式。
    """
    try:
        supabase = get_supabase_client()
        
        # 查询项目级筛选器配置
        response = supabase.table('project_filter_defaults').select('*').eq(
            'project_id', project_id
        ).eq('level', 'project').execute()
        
        # 构建 ProjectFilters 对象
        filters = ProjectFilters.empty()
        
        for record in response.data:
            filter_name = record['filter_name']
            filter_values = record['filter_values']
            
            if filter_name == 'categories':
                filters.categories = filter_values or []
            elif filter_name == 'brands':
                filters.brands = filter_values or []
            elif filter_name == 'segments':
                filters.segments = filter_values or []
            elif filter_name == 'extend_fields':
                filters.extend_fields = filter_values or {}
        
        logger.info(f"Retrieved filter defaults for project {project_id}: {filters.to_dict()}")
        
        return {
            "filters": filters.to_dict(),
            "project_id": project_id
        }
        
    except Exception as e:
        logger.error(f"Error getting project filter defaults: {e}", exc_info=True)
        # 返回空的筛选器配置而不是抛出异常，保证系统可用性
        return {
            "filters": ProjectFilters.empty().to_dict(),
            "project_id": project_id
        }


@router.get("/projects/{project_id}/filter-config")
async def get_project_filter_config(project_id: str):
    """获取项目的完整过滤器配置
    
    整合 project_filter_defaults 和 project_extend_fields，
    返回哪些过滤器应该显示以及它们的默认值。
    """
    try:
        supabase = get_supabase_client()
        
        # 查询基础过滤器配置
        filter_defaults_response = supabase.table('project_filter_defaults').select('*').eq(
            'project_id', project_id
        ).eq('level', 'project').execute()
        
        # 查询扩展字段配置
        extend_fields_response = supabase.table('project_extend_fields').select('*').eq(
            'project_id', project_id
        ).eq('is_active', True).order('sort_order').execute()
        
        # 构建配置对象
        config = {
            "visible_filters": {},
            "default_values": {},
            "extend_fields": extend_fields_response.data or []
        }
        
        # 处理基础过滤器配置
        for record in filter_defaults_response.data:
            filter_name = record['filter_name']
            filter_values = record['filter_values']
            
            # 标记为可见
            config["visible_filters"][filter_name] = True
            
            # 设置默认值
            if filter_values and len(filter_values) > 0:
                config["default_values"][filter_name] = filter_values
            else:
                config["default_values"][filter_name] = []
        
        logger.info(f"Retrieved filter config for project {project_id}: visible={list(config['visible_filters'].keys())}, extend_fields={len(config['extend_fields'])}")
        
        return {
            "config": config,
            "project_id": project_id
        }
        
    except Exception as e:
        logger.error(f"Error getting project filter config: {e}", exc_info=True)
        # 返回空配置保证系统可用性
        return {
            "config": {
                "visible_filters": {},
                "default_values": {},
                "extend_fields": []
            },
            "project_id": project_id
        }


@router.get("/projects/{project_id}/charts/{chart_type}/filter-config")
async def get_chart_filter_config(project_id: str, chart_type: str):
    """获取特定图表的筛选器配置
    
    从 project_filter_defaults 表中获取 level='chart' 且 chart_type 匹配的筛选器配置。
    
    Args:
        project_id: 项目ID
        chart_type: 图表类型，如 'market-share-analysis', 'brand-analysis' 等
    
    Returns:
        图表专属的筛选器配置，只包含该图表需要显示的筛选器
    """
    try:
        supabase = get_supabase_client()
        
        # 查询该chart的筛选器配置
        chart_filters_response = supabase.table('project_filter_defaults').select('*').eq(
            'project_id', project_id
        ).eq('level', 'chart').eq('chart_name', chart_type).execute()
        
        # 构建配置对象
        config = {
            "visible_filters": {},
            "default_values": {},
            "extend_fields": [],
            "chart_type": chart_type
        }
        
        # 收集该chart需要的extend字段名称
        required_extend_fields = set()
        
        # 处理chart级筛选器配置
        for record in chart_filters_response.data:
            filter_name = record['filter_name']
            filter_values = record['filter_values']
            
            # 标记为可见
            config["visible_filters"][filter_name] = True
            
            # 设置默认值
            if filter_values and len(filter_values) > 0:
                if filter_name == 'extend_fields':
                    # extend_fields是对象格式，解析其中的字段名
                    config["default_values"][filter_name] = filter_values
                    # 从filter_values中提取需要的字段名
                    if isinstance(filter_values, dict):
                        required_extend_fields.update(filter_values.keys())
                else:
                    # 其他是数组格式
                    config["default_values"][filter_name] = filter_values if isinstance(filter_values, list) else [filter_values]
            else:
                config["default_values"][filter_name] = {} if filter_name == 'extend_fields' else []
        
        # 查询扩展字段配置，并根据required_extend_fields过滤
        if required_extend_fields:
            extend_fields_response = supabase.table('project_extend_fields').select('*').eq(
                'project_id', project_id
            ).eq('is_active', True).in_('field_name', list(required_extend_fields)).order('sort_order').execute()
            
            config["extend_fields"] = extend_fields_response.data or []
        else:
            # 如果没有extend_fields配置，返回空数组
            config["extend_fields"] = []
        
        logger.info(f"Retrieved chart filter config for project {project_id}, chart {chart_type}: visible={list(config['visible_filters'].keys())}")
        
        return {
            "config": config,
            "project_id": project_id,
            "chart_type": chart_type
        }
        
    except Exception as e:
        logger.error(f"Error getting chart filter config for project {project_id}, chart {chart_type}: {e}", exc_info=True)
        # 返回空配置保证系统可用性
        return {
            "config": {
                "visible_filters": {},
                "default_values": {},
                "extend_fields": [],
                "chart_type": chart_type
            },
            "project_id": project_id,
            "chart_type": chart_type
        } 