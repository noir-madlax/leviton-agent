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
    TopCategoriesRequest, TopCategoriesResponse,
    ReviewsByCategoryRequest, ReviewsByCategoryResponse
)
from .reviewAnalysis.service import ReviewAnalysisChartService

from .filters.models import AsinFilterRequest, AsinFilterResponse
from .filters.asin_filter_service import get_filtered_asins as filter_asins

from .market_analysis.models import (
    TAMMarketShareRequest, TAMMarketShareResponse
)
from .market_analysis.service import TAMMarketShareService

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
            sort_order=request.sort_order
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


@router.post("/review-analysis/top-categories", response_model=TopCategoriesResponse)
async def get_top_categories(request: TopCategoriesRequest):
    """Get top aspect categories with comprehensive statistics.
    
    This endpoint retrieves the top aspect categories for all filtered products
    under a project, with detailed statistics including mentions, sentiments,
    and review counts. Supports filtering by aspect type and various sorting options.
    
    Args:
        request: TopCategoriesRequest containing project_id, filters, and additional conditions
        
    Returns:
        TopCategoriesResponse: Top categories data with comprehensive statistics
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        logger.info(f"Getting top categories for project {request.project_id}")
        
        service = ReviewAnalysisChartService(
            project_id=request.project_id,
            filters=request.filters,
            selected_asins=request.selected_asins,
            date_range=request.date_range
        )
        
        data = await service.get_top_categories(request.options)
        response = TopCategoriesResponse(data=data)
        
        logger.info(f"Top categories analysis completed for project {request.project_id}: {len(response.data.categories)} categories")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in top categories: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in top categories: {e}", exc_info=True)
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
            filters=request.filters,
            selected_asins=request.selected_asins,
            date_range=request.date_range
        )
        
        # Get reviews with deduplication and aspect aggregation
        raw_data = await service.get_reviews_by_category(
            category_id=request.category_id,
            limit=request.limit,
            offset=request.offset,
            sort_by=request.sort_by,
            sort_order=request.sort_order
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