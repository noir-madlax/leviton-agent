"""Dashboard charts API routes."""

from fastapi import APIRouter, HTTPException
import logging

from .competitorAnalysis.models import (
    CompetitorSummaryRequest, CompetitorSummaryResponse,
    CompetitorMatrixViewRequest, CompetitorMatrixViewResponse,
    ReviewRetrievalRequest, ReviewRetrievalResponse
)
from .competitorAnalysis.service import CompetitorAnalysisChartService

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
            date_range=request.date_range
        )
        data = await service.get_competitor_summary(request.selected_asins)
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
            date_range=request.date_range
        )
        data = await service.get_matrix_view_data(
            selected_asins=request.selected_asins,
            aspect_type=request.aspect_type,
            options=request.filter
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