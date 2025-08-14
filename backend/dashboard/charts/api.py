"""Dashboard charts API routes."""

from fastapi import APIRouter, HTTPException
import logging

from .competitorAnalysis.models import (
    CompetitorSummaryRequest, CompetitorSummaryResponse,
    CompetitorMatrixViewRequest, CompetitorMatrixViewResponse,
    ReviewRetrievalRequest, ReviewRetrievalResponse
)
from .competitorAnalysis.service import CompetitorAnalysisChartService

from .reviewAnalysis.models import (
    ReviewsByCategoryRequest, ReviewsByCategoryResponse,
    CustomerPainPointsRequest, CustomerPainPointsResponse, CustomerPainPointsData, CustomerPainPointItem,
    CustomerPainPointsGroupedResponse, CustomerPainPointsGroupedData, CustomerPainPointsGroup,
    CustomerDelightsRequest, CustomerDelightsGroupedResponse, CustomerDelightsGroupedData, CustomerDelightsGroup, CustomerDelightItem,
    UseCaseSentimentRequest, UseCaseSentimentGroupedResponse, UseCaseSentimentGroupedData, UseCaseSentimentGroup, UseCaseSentimentItem
)
from .reviewAnalysis.service import ReviewAnalysisChartService

from .filters.models import AsinFilterRequest, AsinFilterResponse
from .filters.asin_filter_service import get_filtered_asins as filter_asins

from .market_analysis.models import (
    TAMMarketShareRequest, TAMMarketShareResponse,
    TopSegmentsByRevenueRequest, TopSegmentsByRevenueResponse,
    PackageTypeDistributionRequest, PackageTypeDistributionResponse
)
from .market_analysis.service import TAMMarketShareService, TopSegmentsByRevenueService, PackageTypeDistributionService

from .pricing_analysis.models import (
    PriceDistributionRequest, PriceDistributionResponse,
    PriceVsRevenueRequest, PriceVsRevenueResponse,
    BrandPriceDistributionRequest, BrandPriceDistributionResponse,
    PriceDistributionOverviewRequest, PriceDistributionOverviewResponse
)
from .pricing_analysis.services import (
    PriceDistributionService,
    PriceVsRevenueService,
    BrandPriceDistributionService,
    PriceDistributionOverviewService
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/competitor-analysis/summary", response_model=CompetitorSummaryResponse)
async def get_competitor_summary(request: CompetitorSummaryRequest):
    """Get competitor analysis summary data.
    
    Args:
        request: Competitor summary request with project_id and selected_asins
        
    Returns:
        CompetitorSummaryResponse: Competitor summary data
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        service = CompetitorAnalysisChartService(
            project_id=request.project_id,
            filters=request.filters,
            selected_asins=request.selected_asins,
            date_range=request.date_range
        )
        data = await service.get_competitor_summary()
        response = CompetitorSummaryResponse(data=data)
        
        logger.info(f"Competitor summary analysis completed for project {request.project_id}: {len(response.data.products)} products")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in competitor summary: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in competitor summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/competitor-analysis/matrix-view", response_model=CompetitorMatrixViewResponse)
async def get_competitor_matrix_view(request: CompetitorMatrixViewRequest):
    """Get competitor analysis matrix view data.
    
    Args:
        request: Competitor matrix view request with project_id, selected_asins, aspect_type, and filter options
        
    Returns:
        CompetitorMatrixViewResponse: Competitor matrix view data
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        service = CompetitorAnalysisChartService(
            project_id=request.project_id,
            filters=request.filters,
            selected_asins=request.selected_asins,
            date_range=request.date_range
        )
        data = await service.get_matrix_view_data(
            aspect_type=request.aspect_type,
            options=request.options
        )
        response = CompetitorMatrixViewResponse(data=data)
        
        logger.info(f"Competitor matrix view analysis completed for project {request.project_id}: {len(response.data.aspect_categories)} categories")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in competitor matrix view: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in competitor matrix view: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/competitor-analysis/reviews", response_model=ReviewRetrievalResponse)
async def get_reviews_by_category_product(request: ReviewRetrievalRequest):
    """Get reviews for a specific category and product with deduplication and aspect aggregation.
    
    This endpoint retrieves all reviews that mention a specific aspect category
    for a particular product within a project. It provides detailed review information
    including sentiment, aspect descriptions, and review metadata. Reviews are deduplicated
    and aspects are aggregated per review.
    
    Args:
        request: ReviewRetrievalRequest containing project_id, category_id, product_id, and pagination options
        
    Returns:
        ReviewRetrievalResponse: Detailed review data with aggregated aspects and pagination support
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        logger.info(f"Getting reviews for project {request.project_id}, category {request.category_id}, product {request.product_id}")
        
        service = CompetitorAnalysisChartService(
            project_id=request.project_id,
            filters=request.filters,
            selected_asins=request.selected_asins,
            date_range=request.date_range
        )
        
        # Get reviews with deduplication and aspect aggregation
        raw_data = await service.get_reviews_by_category_product(
            category_id=request.category_id,
            product_id=request.product_id,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            sentiment_filter=request.sentiment_filter,
            rating_filter=request.rating_filter
        )
        
        # Convert raw data to response format
        from .competitorAnalysis.models import (
            ReviewAspect, ReviewDetail, PaginationInfo, CategoryInfo, ReviewRetrievalData
        )
        
        # Convert reviews
        reviews = []
        for review_data in raw_data['reviews']:
            # Convert aspects
            aspects = []
            for aspect_data in review_data['aspects']:
                aspect = ReviewAspect(
                    aspect_description=aspect_data['aspect_description'],
                    sentiment=aspect_data['sentiment'],
                    aspect_type=aspect_data['aspect_type']
                )
                aspects.append(aspect)
            
            # Create review detail
            review = ReviewDetail(
                review_id=review_data['review_id'],
                review_title=review_data.get('review_title'),
                review_text=review_data['review_text'],
                rating=review_data.get('rating'),
                verified=review_data.get('verified'),
                review_date=review_data.get('review_date'),
                aspects=aspects,
                category_name=review_data['category_name'],
                category_definition=review_data.get('category_definition'),
                aspect_type=review_data['aspect_type']
            )
            reviews.append(review)
        
        # Convert category info
        category_info = None
        if raw_data['category_info']:
            category_info = CategoryInfo(
                category_pk=raw_data['category_info']['category_pk'],
                name=raw_data['category_info']['name'],
                definition=raw_data['category_info']['definition'],
                aspect_type=raw_data['category_info']['aspect_type'],
                stage=raw_data['category_info']['stage']
            )
        
        # Create pagination info
        pagination = PaginationInfo(
            limit=raw_data['pagination']['limit'],
            offset=raw_data['pagination']['offset'],
            has_more=raw_data['pagination']['has_more']
        )
        
        # Create response data
        response_data = ReviewRetrievalData(
            reviews=reviews,
            total_reviews=raw_data['total_reviews'],
            project_id=raw_data['project_id'],
            category_id=raw_data['category_id'],
            product_id=raw_data['product_id'],
            category_info=category_info,
            pagination=pagination
        )
        
        response = ReviewRetrievalResponse(data=response_data)
        
        logger.info(f"Review retrieval completed for project {request.project_id}: {len(reviews)} reviews returned out of {raw_data['total_reviews']} total")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in review retrieval: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in review retrieval: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")





@router.post("/review-analysis/reviews-by-category", response_model=ReviewsByCategoryResponse)
async def get_reviews_by_category(request: ReviewsByCategoryRequest):
    """Get reviews for a specific category with product information.
    
    This endpoint retrieves all reviews that mention a specific aspect category
    across all filtered products under a project. It provides detailed review information
    including product details, sentiment, aspect descriptions, and review metadata.
    Reviews are deduplicated and aspects are aggregated per review.
    
    Args:
        request: ReviewsByCategoryRequest containing project_id, category_id, and pagination options
        
    Returns:
        ReviewsByCategoryResponse: Detailed review data with product information and pagination
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        logger.info(f"Getting reviews by category for project {request.project_id}, category {request.category_id}")
        
        service = ReviewAnalysisChartService(
            project_id=request.project_id,
            filters=request.filters.dict() if request.filters else {},
            selected_asins=request.selected_asins,
            date_range=request.date_range.dict() if request.date_range else None
        )
        
        # Get reviews with deduplication and aspect aggregation
        raw_data = await service.get_reviews_by_category(
            category_id=request.category_id,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            sort_order=request.sort_order,
            sentiment_filter=request.sentiment_filter,
            rating_filter=request.rating_filter
        )
        
        # Convert raw data to response format
        from .reviewAnalysis.models import (
            ReviewAspectBase, ReviewWithProductInfo, CategoryInfoBase, PaginationBase, ReviewsByCategoryData
        )
        
        # Convert reviews
        reviews = []
        for review_data in raw_data['reviews']:
            # Convert aspects
            aspects = []
            for aspect_data in review_data['aspects']:
                aspect = ReviewAspectBase(
                    aspect_description=aspect_data['aspect_description'],
                    sentiment=aspect_data['sentiment'],
                    aspect_type=aspect_data['aspect_type']
                )
                aspects.append(aspect)
            
            # Create review with product information
            review = ReviewWithProductInfo(
                review_id=review_data['review_id'],
                review_title=review_data.get('review_title'),
                review_text=review_data['review_text'],
                rating=review_data.get('rating'),
                verified=review_data.get('verified'),
                review_date=review_data.get('review_date'),
                aspects=aspects,
                product_id=review_data['product_id'],
                product_title=review_data.get('product_title'),
                product_brand=review_data.get('product_brand'),
                product_url=review_data.get('product_url')
            )
            reviews.append(review)
        
        # Convert category info
        category_info = None
        if raw_data['category_info']:
            category_info = CategoryInfoBase(
                category_id=raw_data['category_info']['category_pk'],
                category_name=raw_data['category_info']['name'],
                definition=raw_data['category_info']['definition'],
                aspect_type=raw_data['category_info']['aspect_type']
            )
        
        # Create pagination info
        pagination = PaginationBase(
            limit=raw_data['pagination']['limit'],
            offset=raw_data['pagination']['offset'],
            has_more=raw_data['pagination']['has_more']
        )
        
        # Create response data
        response_data = ReviewsByCategoryData(
            reviews=reviews,
            total_reviews=raw_data['total_reviews'],
            project_id=raw_data['project_id'],
            category_id=raw_data['category_id'],
            category_info=category_info,
            pagination=pagination
        )
        
        response = ReviewsByCategoryResponse(data=response_data)
        
        logger.info(f"Reviews by category completed for project {request.project_id}: {len(reviews)} reviews returned out of {raw_data['total_reviews']} total")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in reviews by category: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in reviews by category: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/filters/asins", response_model=AsinFilterResponse)
async def get_filtered_asins(request: AsinFilterRequest):
    """获取过滤后的ASIN列表

    使用链式过滤器系统，根据项目ID和过滤条件返回符合条件的ASIN列表。
    支持品牌、类别、细分市场和扩展字段的组合过滤。

    Args:
        request: ASIN过滤器请求，包含：
                - project_id: 项目ID（必传）
                - filters: 过滤条件对象（可选），包含：
                  - categories: 产品类别列表
                  - brands: 品牌列表
                  - segments: 细分市场列表
                  - extend_fields: 扩展字段过滤条件

    Returns:
        AsinFilterResponse: 继承自BaseResponseModel的响应，包含：
                          - status: 响应状态
                          - message: 响应消息
                          - timestamp: 时间戳
                          - data: 过滤后的ASIN列表

    Raises:
        HTTPException: 当请求处理失败时
    """
    try:
        from core.database.connection import get_supabase_client

        # 获取Supabase客户端
        supabase_client = get_supabase_client()

        # 使用公共的ASIN过滤服务
        filtered_asins = filter_asins(supabase_client, request)

        # 创建响应对象
        response = AsinFilterResponse(data=filtered_asins)

        logger.info(f"ASIN filtering completed for project {request.project_id}: {len(filtered_asins)} ASINs returned")

        return response

    except ValueError as e:
        logger.error(f"Validation error in ASIN filtering: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in ASIN filtering: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/market-analysis/tam-market-share", response_model=TAMMarketShareResponse)
async def get_tam_market_share(request: TAMMarketShareRequest):
    """Get Total Addressable Market (TAM) and Market Share analysis.

    This endpoint calculates the total addressable market and detailed market share
    analysis by category and brand. All calculations are performed on the backend
    using filtered product data.

    **Example Request:**
    ```json
    {
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
    ```
    
    **Timeframe Options:**
    - `"month"`: Use past_month_revenue for analysis (过去1个月收入)
    - `"6months"`: Use past_6_month_revenue for analysis (过去6个月收入)
    - `"year"`: Use past_year_revenue and past_year_volume for analysis (过去1年收入和销量)

    **Example Response:**
    ```json
    {
        "tam_data": {
            "total_market_revenue": 15000000.50,
            "total_market_volume": 25000,
            "total_products": 1250,
            "currency": "USD"
        },
        "market_share_by_category": [
            {
                "category": "Dimmer Switches",
                "total_revenue": 8000000.25,
                "total_volume": 12000,
                "total_products": 600,
                "brand_shares": [
                    {
                        "brand": "Leviton",
                        "revenue": 3200000.10,
                        "volume": 4800,
                        "product_count": 240,
                        "market_share_percentage": 40.0,
                        "rank": 1
                    }
                ]
            }
        ],
        "metadata": {
            "filtered_asins_count": 1250,
            "total_categories": 2,
            "total_brands": 15,
            "calculation_timestamp": "2024-01-15T10:30:00Z"
        }
    }
    ```

    Args:
        request: TAM Market Share request with project_id and filters

    Returns:
        TAMMarketShareResponse: Complete TAM and market share analysis

    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        from core.database.connection import get_supabase_client

        # Initialize service with Supabase client
        supabase_client = get_supabase_client()
        service = TAMMarketShareService(supabase_client)

        # Get TAM and market share data
        response = service.get_tam_market_share_data(request)

        logger.info(f"TAM Market Share analysis completed for project {request.project_id}: "
                   f"${response.tam_data.total_market_revenue:,.2f} TAM with "
                   f"{len(response.market_share_by_category)} categories")

        return response

    except ValueError as e:
        logger.error(f"Validation error in TAM Market Share analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in TAM Market Share analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/market-analysis/top-segments-by-revenue", response_model=TopSegmentsByRevenueResponse)
async def get_top_segments_by_revenue(request: TopSegmentsByRevenueRequest):
    """获取按收入排名的 Top Segments 数据.

    这个端点专门为 "Top 10 Segments by Revenue" 图表提供数据，
    在后端完成所有数据处理和排序逻辑，简化前端实现。

    **示例请求:**
    ```json
    {
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
    ```
    
    **参数说明:**
    - `limit`: 返回的 segment 数量限制 (1-50，默认 10)
    - `metric_type`: 排序指标类型
      - `"revenue"`: 按收入排序 (默认)
      - `"volume"`: 按销量排序
      - `"products"`: 按产品数量排序
    - `timeframe.period`: 时间周期
      - `"month"`: 过去1个月数据
      - `"6months"`: 过去6个月数据
      - `"year"`: 过去1年数据 (默认)

    **示例响应:**
    ```json
    {
        "data": {
            "total_market_revenue": 15250000.5,
            "total_market_volume": 45210,
            "total_products": 1320,
            "currency": "USD",
            "top_segments_by_category": [
                {
                    "category": "Dimmer Switches",
                    "total_revenue": 8350000.2,
                    "total_volume": 24680,
                    "total_products": 640,
                    "segments": [
                        {
                            "segment": "Premium Smart Dimmer",
                            "revenue": 3200000.1,
                            "volume": 8400,
                            "products": 128,
                            "market_share_percentage": 38.33,
                            "rank": 1,
                            "avg_price": 380.95,
                            "top_brand": "Leviton"
                        }
                    ]
                }
            ]
        },
        "metadata": {
            "filtered_asins_count": 1250,
            "total_categories": 2,
            "total_segments": 24,
            "returned_segments": 4,
            "metric_type": "revenue",
            "timeframe_used": "year",
            "limit_per_category": 2,
            "calculation_timestamp": "2024-01-15T10:30:00Z"
        }
    }
    ```

    Args:
        request: Top Segments 请求参数

    Returns:
        TopSegmentsByRevenueResponse: 完整的 Top Segments 分析数据

    Raises:
        HTTPException: 参数验证或系统错误的响应
    """
    try:
        from core.database.connection import get_supabase_client

        # Initialize service with Supabase client
        supabase_client = get_supabase_client()
        service = TopSegmentsByRevenueService(supabase_client)

        # Get Top Segments data
        response = service.get_top_segments_data(request)

        logger.info(f"Top Segments analysis completed for project {request.project_id}: "
                   f"returned {response.metadata.returned_segments}/{response.metadata.total_segments} segments, "
                   f"sorted by {response.metadata.metric_type}")

        return response

    except ValueError as e:
        logger.error(f"Validation error in Top Segments analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in Top Segments analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/market-analysis/package-type-distribution", response_model=PackageTypeDistributionResponse)
async def get_package_type_distribution(request: PackageTypeDistributionRequest):
    """Get Package Type Distribution analysis.

    This endpoint calculates package type distribution analysis with support for 
    both revenue and product count metrics. All calculations are performed on 
    the backend using filtered product data.

    **Example Request:**
    ```json
    {
        "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
        "filters": {
            "categories": ["Dimmer Switches", "Light Switches"],
            "brands": ["Leviton", "Lutron"],
            "extend_fields": {
                "smart_capability": "Smart"
            }
        },
        "timeframe": {
            "period": "year"
        },
        "metric_type": "revenue"
    }
    ```

    **Metric Types:**
    - `"revenue"`: Analyze by revenue distribution
    - `"products"`: Analyze by product count distribution

    **Example Response:**
    ```json
    {
        "data": {
            "overall_distribution": [
                {
                    "package_type": "Single",
                    "revenue": 5000000.0,
                    "product_count": 1200,
                    "percentage": 65.5,
                    "rank": 1
                }
            ],
            "distribution_by_category": [
                {
                    "category": "Dimmer Switches",
                    "total_revenue": 3000000.0,
                    "total_products": 800,
                    "package_types": [...]
                }
            ],
            "metric_type": "revenue"
        },
        "metadata": {
            "filtered_asins_count": 2500,
            "total_package_types": 4,
            "calculation_timestamp": "2024-01-01T00:00:00Z"
        }
    }
    ```
    """
    try:
        from core.database.connection import get_supabase_client

        # Initialize service with Supabase client
        supabase_client = get_supabase_client()
        service = PackageTypeDistributionService(supabase_client)

        # Get package type distribution data
        response = service.get_package_type_distribution_data(request)

        logger.info(f"Package Type Distribution analysis completed for project {request.project_id}: "
                   f"{len(response.data.overall_distribution)} package types with "
                   f"{response.data.total_products} total products")

        return response

    except ValueError as e:
        logger.error(f"Validation error in Package Type Distribution analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in Package Type Distribution analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pricing-analysis/price-distribution-by-type", response_model=PriceDistributionResponse)
async def get_price_distribution_by_type(request: PriceDistributionRequest):
    """Get price distribution analysis data by product type.
    
    This endpoint provides violin chart data for price distributions across product types,
    supporting both SKU and unit price analysis with comprehensive statistics.
    
    Args:
        request: Price distribution request with project_id, filters, and timeframe
        
    Returns:
        PriceDistributionResponse: Price distribution data by category with statistics
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        logger.info(f"💰 Starting Price Distribution analysis for project {request.project_id}")
        
        # Import supabase client
        from core.database.connection import get_supabase_client
        supabase = get_supabase_client()
        
        # Initialize service
        service = PriceDistributionService(supabase)
        
        # Get price distribution data
        response = service.get_price_distribution_data(request)
        
        logger.info(f"Price Distribution analysis completed for project {request.project_id}: "
                   f"{len(response.priceDistribution)} categories with "
                   f"{response.metadata.filtered_asins_count} total products")

        return response

    except ValueError as e:
        logger.error(f"Validation error in Price Distribution analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in Price Distribution analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pricing-analysis/price-vs-revenue", response_model=PriceVsRevenueResponse)
async def get_price_vs_revenue(request: PriceVsRevenueRequest):
    """Get price vs revenue scatter chart data.
    
    This endpoint provides scatter plot data showing the relationship between product prices
    and revenue, with products grouped by category. Used for identifying price-revenue patterns
    and top-performing products.
    
    Args:
        request: Price vs revenue request with project_id, filters, and timeframe
        
    Returns:
        PriceVsRevenueResponse: Scatter plot data with top products by category
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        logger.info(f"📈 Starting Price vs Revenue analysis for project {request.project_id}")
        
        # Import supabase client
        from core.database.connection import get_supabase_client
        supabase = get_supabase_client()
        
        # Initialize service
        service = PriceVsRevenueService(supabase)
        
        # Get price vs revenue data
        response = service.get_price_vs_revenue_data(request)
        
        logger.info(f"Price vs Revenue analysis completed for project {request.project_id}: "
                   f"{len(response.segments)} segments with "
                   f"{response.meta.filtered_asins_count} total products")

        return response

    except ValueError as e:
        logger.error(f"Validation error in Price vs Revenue analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in Price vs Revenue analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pricing-analysis/brand-price-distribution", response_model=BrandPriceDistributionResponse)
async def get_brand_price_distribution(request: BrandPriceDistributionRequest):
    """Get brand price distribution analysis data.
    
    This endpoint provides violin chart data for price distributions by brand within each
    product category. Useful for understanding brand positioning and price competitiveness.
    
    Args:
        request: Brand price distribution request with project_id, filters, and timeframe
        
    Returns:
        BrandPriceDistributionResponse: Brand price distribution data by category
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        logger.info(f"🏷️ Starting Brand Price Distribution analysis for project {request.project_id}")
        
        # Import supabase client
        from core.database.connection import get_supabase_client
        supabase = get_supabase_client()
        
        # Initialize service
        service = BrandPriceDistributionService(supabase)
        
        # Get brand price distribution data
        response = service.get_brand_price_distribution_data(request)
        
        logger.info(f"Brand Price Distribution analysis completed for project {request.project_id}: "
                   f"{len(response.brandPriceDistribution)} categories with "
                   f"{response.metadata.filtered_asins_count} total products")

        return response

    except ValueError as e:
        logger.error(f"Validation error in Brand Price Distribution analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in Brand Price Distribution analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/pricing-analysis/price-distribution-overview", response_model=PriceDistributionOverviewResponse)
async def get_price_distribution_overview(request: PriceDistributionOverviewRequest):
    """Get price distribution overview table data.
    
    This endpoint provides overview statistics for price distributions across all product 
    categories without applying filters. Used for the overview table showing segment 
    summaries with product counts, min/median/max/average prices.
    
    Args:
        request: Price distribution overview request with project_id and timeframe
        
    Returns:
        PriceDistributionOverviewResponse: Overview table data with statistics
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        logger.info(f"📊 Starting Price Distribution Overview analysis for project {request.project_id}")
        
        # Import supabase client
        from core.database.connection import get_supabase_client
        supabase = get_supabase_client()
        
        # Initialize service
        service = PriceDistributionOverviewService(supabase)
        
        # Get overview data
        response = service.get_overview_data(request)
        
        logger.info(f"Price Distribution Overview analysis completed for project {request.project_id}: "
                   f"{len(response.overview_data)} segments with "
                   f"{response.metadata.filtered_asins_count} total products")

        return response

    except ValueError as e:
        logger.error(f"Validation error in Price Distribution Overview analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in Price Distribution Overview analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/review-insights/customer-pain-points", response_model=CustomerPainPointsGroupedResponse)
async def get_customer_pain_points(request: CustomerPainPointsRequest):
    """Get Customer Pain Points (Top categories by negative reviews under phy/perf).

    Applies unified ASIN filtering via chain filter, then queries top categories
    with aspect_type='phy_perf' sorted by negative_reviews.
    """
    try:
        from core.database.connection import get_supabase_client

        supabase_client = get_supabase_client()

        # Determine selected product categories from request filters (single or multiple)
        selected_categories = []
        if request.filters and request.filters.categories:
            selected_categories = request.filters.categories

        # If未选择，保持空数组表示“无类别限定”，但仍返回空groups以显式表达

        groups: list[CustomerPainPointsGroup] = []

        # 遍历每个选择的产品类别，分别过滤ASIN并计算痛点
        for product_category in selected_categories:
            # 构造子请求，仅包含该产品类别
            sub_filters = request.filters.copy() if request.filters else None
            if sub_filters:
                sub_filters.categories = [product_category]

            sub_request = CustomerPainPointsRequest(
                project_id=request.project_id,
                filters=sub_filters,
                selected_asins=request.selected_asins,
                timeframe=request.timeframe,
                date_range=request.date_range,
                limit=request.limit
            )

            # 1) 过滤ASIN
            filtered_asins = filter_asins(supabase_client, sub_request)

            # 2) 初始化服务（优先selected_asins -> 这里传入filtered_asins）
            service = ReviewAnalysisChartService(
                project_id=sub_request.project_id,
                filters=sub_request.filters.dict() if sub_request.filters else {},
                selected_asins=filtered_asins or None,
                date_range=sub_request.date_range.dict() if sub_request.date_range else None
            )

            # 3) 查询该产品类别下的痛点
            top_data = await service.get_top_categories({
                'aspect_type': 'phy_perf',
                'sortBy': 'negative_reviews',
                'sortDirection': 'desc',
                'maxCategories': max(1, min(sub_request.limit, 100))
            })

            categories = top_data.get('categories', [])

            # 4) 映射结果
            items = []
            for cat in categories:
                total_reviews = cat.get('total_reviews', 0) or 0
                negative_reviews = cat.get('negative_reviews', 0) or 0
                positive_reviews = cat.get('positive_reviews', 0) or 0
                negative_rate = (negative_reviews / total_reviews * 100.0) if total_reviews > 0 else 0.0
                satisfaction_rate = 100.0 - negative_rate

                aspect_type = cat.get('aspect_type', 'phy')
                display_type = 'Physical' if aspect_type == 'phy' else ('Performance' if aspect_type == 'perf' else 'Physical')

                item = CustomerPainPointItem(
                    category_id=cat.get('category_id') or cat.get('category_pk'),
                    category_name=cat.get('category_name', ''),
                    category_definition=cat.get('definition', ''),
                    type=display_type,
                    total_reviews=total_reviews,
                    positive_reviews=positive_reviews,
                    negative_reviews=negative_reviews,
                    negative_rate=negative_rate,
                    satisfaction_rate=satisfaction_rate,
                    impacted_products=max(1, int((cat.get('total_mentions', 0) or 0) > 0)),
                    related_detail_texts=None
                )
                items.append(item)

            group = CustomerPainPointsGroup(
                product_category=product_category,
                pain_points=items[: sub_request.limit],
                filtered_asins_count=len(filtered_asins),
                total_categories=top_data.get('total_categories', len(categories))
            )
            groups.append(group)

        # 构造分组响应（若未选择类别，则groups为空）
        grouped_data = CustomerPainPointsGroupedData(
            project_id=request.project_id,
            selected_categories=selected_categories,
            groups=groups
        )

        response = CustomerPainPointsGroupedResponse(data=grouped_data)
        logger.info(f"Customer Pain Points (grouped) returned {sum(len(g.pain_points) for g in groups)} items across {len(groups)} product categories for project {request.project_id}")
        return response

    except ValueError as e:
        logger.error(f"Validation error in customer pain points: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        logger.error(f"System error in customer pain points: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/review-insights/customer-delights", response_model=CustomerDelightsGroupedResponse)
async def get_customer_delights(request: CustomerDelightsRequest):
    """Get Customer Delights (Top categories by positive reviews under phy/perf), grouped by product category.

    Applies unified ASIN filtering via chain filter, then for each selected product category
    queries top categories with aspect_type='phy_perf' sorted by positive_reviews.
    """
    try:
        from core.database.connection import get_supabase_client

        supabase_client = get_supabase_client()

        # Determine selected product categories from request filters (single or multiple)
        selected_categories = []
        if request.filters and request.filters.categories:
            selected_categories = request.filters.categories

        groups: list[CustomerDelightsGroup] = []

        for product_category in selected_categories:
            sub_filters = request.filters.copy() if request.filters else None
            if sub_filters:
                sub_filters.categories = [product_category]

            sub_request = CustomerDelightsRequest(
                project_id=request.project_id,
                filters=sub_filters,
                selected_asins=request.selected_asins,
                timeframe=request.timeframe,
                date_range=request.date_range,
                limit=request.limit
            )

            # 1) 过滤ASIN
            filtered_asins = filter_asins(supabase_client, sub_request)

            # 2) 初始化服务（优先selected_asins -> 这里传入filtered_asins）
            service = ReviewAnalysisChartService(
                project_id=sub_request.project_id,
                filters=sub_request.filters.dict() if sub_request.filters else {},
                selected_asins=filtered_asins or None,
                date_range=sub_request.date_range.dict() if sub_request.date_range else None
            )

            # 3) 查询该产品类别下的正向分类
            top_data = await service.get_top_categories({
                'aspect_type': 'phy_perf',
                'sortBy': 'positive_reviews',
                'sortDirection': 'desc',
                'maxCategories': max(1, min(sub_request.limit, 100))
            })

            categories = top_data.get('categories', [])

            # 4) 映射结果
            items = []
            for cat in categories:
                total_reviews = cat.get('total_reviews', 0) or 0
                positive_reviews = cat.get('positive_reviews', 0) or 0
                negative_reviews = cat.get('negative_reviews', 0) or 0
                positive_rate = (positive_reviews / total_reviews * 100.0) if total_reviews > 0 else 0.0

                # satisfaction_level: >=70 High, >=40 Medium, else Low
                if positive_rate >= 70:
                    satisfaction_level = 'High'
                elif positive_rate >= 40:
                    satisfaction_level = 'Medium'
                else:
                    satisfaction_level = 'Low'

                aspect_type = cat.get('aspect_type', 'perf')
                display_type = 'Physical' if aspect_type == 'phy' else ('Performance' if aspect_type == 'perf' else 'Performance')

                item = CustomerDelightItem(
                    category_id=cat.get('category_id') or cat.get('category_pk'),
                    category_name=cat.get('category_name', ''),
                    category_definition=cat.get('definition', ''),
                    type=display_type,
                    total_reviews=total_reviews,
                    positive_reviews=positive_reviews,
                    negative_reviews=negative_reviews,
                    positive_rate=positive_rate,
                    satisfaction_level=satisfaction_level,
                    impacted_products=max(1, int((cat.get('total_mentions', 0) or 0) > 0)),
                    related_detail_texts=None
                )
                items.append(item)

            group = CustomerDelightsGroup(
                product_category=product_category,
                customer_likes=items[: sub_request.limit],
                filtered_asins_count=len(filtered_asins),
                total_categories=top_data.get('total_categories', len(categories))
            )
            groups.append(group)

        grouped_data = CustomerDelightsGroupedData(
            project_id=request.project_id,
            selected_categories=selected_categories,
            groups=groups
        )

        response = CustomerDelightsGroupedResponse(data=grouped_data)
        logger.info(f"Customer Delights (grouped) returned {sum(len(g.customer_likes) for g in groups)} items across {len(groups)} product categories for project {request.project_id}")
        return response

    except ValueError as e:
        logger.error(f"Validation error in customer delights: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"System error in customer delights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/review-insights/use-case-sentiment", response_model=UseCaseSentimentGroupedResponse)
async def get_use_case_sentiment(request: UseCaseSentimentRequest):
    """Get Use Case Sentiment (Top use cases under 'use' aspect), grouped by product category.

    For each selected product category, applies ASIN filtering then queries top categories with
    aspect_type='use' sorted by total_reviews.
    """
    try:
        from core.database.connection import get_supabase_client

        supabase_client = get_supabase_client()

        selected_categories = []
        if request.filters and request.filters.categories:
            selected_categories = request.filters.categories

        groups: list[UseCaseSentimentGroup] = []

        for product_category in selected_categories:
            sub_filters = request.filters.copy() if request.filters else None
            if sub_filters:
                sub_filters.categories = [product_category]

            sub_request = UseCaseSentimentRequest(
                project_id=request.project_id,
                filters=sub_filters,
                selected_asins=request.selected_asins,
                timeframe=request.timeframe,
                date_range=request.date_range,
                limit=request.limit
            )

            # 1) Filter ASINs for this product category
            filtered_asins = filter_asins(supabase_client, sub_request)

            # 2) Initialize service prioritizing selected_asins
            service = ReviewAnalysisChartService(
                project_id=sub_request.project_id,
                filters=sub_request.filters.dict() if sub_request.filters else {},
                selected_asins=filtered_asins or None,
                date_range=sub_request.date_range.dict() if sub_request.date_range else None
            )

            # 3) Query top 'use' categories sorted by total_reviews
            top_data = await service.get_top_categories({
                'aspect_type': 'use',
                'sortBy': 'total_reviews',
                'sortDirection': 'desc',
                'maxCategories': max(1, min(sub_request.limit, 100))
            })

            categories = top_data.get('categories', [])

            items = []
            total_use_reviews = 0
            for cat in categories:
                total_reviews = cat.get('total_reviews', 0) or 0
                positive_reviews = cat.get('positive_reviews', 0) or 0
                negative_reviews = cat.get('negative_reviews', 0) or 0
                total_use_reviews += total_reviews

                denom = positive_reviews + negative_reviews
                satisfaction_rate = (positive_reviews / denom * 100.0) if denom > 0 else 50.0

                item = UseCaseSentimentItem(
                    category_id=cat.get('category_id') or cat.get('category_pk'),
                    use_case=cat.get('category_name', ''),
                    product_attribute='USE',
                    total_reviews=total_reviews,
                    positive_reviews=positive_reviews,
                    negative_reviews=negative_reviews,
                    satisfaction_rate=satisfaction_rate,
                    product_count=max(1, int((cat.get('total_mentions', 0) or 0) > 0)),
                    category_definition=cat.get('definition', ''),
                    related_detail_texts=None
                )
                items.append(item)

            group = UseCaseSentimentGroup(
                product_category=product_category,
                all_use_cases=items[: sub_request.limit],
                filtered_asins_count=len(filtered_asins),
                total_use_reviews=total_use_reviews,
                total_categories=top_data.get('total_categories', len(categories))
            )
            groups.append(group)

        grouped_data = UseCaseSentimentGroupedData(
            project_id=request.project_id,
            selected_categories=selected_categories,
            groups=groups
        )

        response = UseCaseSentimentGroupedResponse(data=grouped_data)
        logger.info(f"Use Case Sentiment (grouped) returned {sum(len(g.all_use_cases) for g in groups)} items across {len(groups)} product categories for project {request.project_id}")
        return response

    except ValueError as e:
        logger.error(f"Validation error in use case sentiment: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"System error in use case sentiment: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")