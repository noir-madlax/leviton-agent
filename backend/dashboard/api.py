"""FastAPI router for Dashboard module."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Query, Depends

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


@router.get("/brand-analysis", response_model=BrandAnalysisResponse)
async def get_brand_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get top 10 brand category revenue analysis for a specific project.
    
    This endpoint replaces the frontend getBrandCategoryRevenue() method
    with server-side implementation that applies project ASIN filtering.
    Returns only the top 10 brands by total revenue.
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        # Initialize service with project-specific ASIN filtering
        service = BrandAnalysisService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
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
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in brand analysis API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/product-analysis", response_model=ProductAnalysisResponse)
async def get_product_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get product analysis data for a specific project.
    
    Enhanced version: Returns complete data format including segment summary, 
    segment names, and colors for frontend compatibility.
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        service = ProductAnalysisService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        raw_data = service.get_data()
        
        # Convert segments dict to TopProductsData format
        segments_dict = raw_data['topProducts']['segments']
        segments_products = {}
        for segment_name, products_list in segments_dict.items():
            segments_products[segment_name] = [
                ProductInfo(**product) for product in products_list
            ]
        
        # Convert to response format
        response = ProductAnalysisResponse(
            priceVsRevenue=[
                CategoryProducts(**category_data) for category_data in raw_data['priceVsRevenue']
            ],
            topProducts=TopProductsData(
                segments=segments_products,
                dimmerSwitches=[
                    ProductInfo(**product) for product in raw_data['topProducts']['dimmerSwitches']
                ],
                lightSwitches=[
                    ProductInfo(**product) for product in raw_data['topProducts']['lightSwitches']
                ]
            ),
            segmentSummary={
                segment_name: SegmentSummary(**summary_data) 
                for segment_name, summary_data in raw_data['segmentSummary'].items()
            },
            segmentNames=raw_data['segmentNames'],
            segmentColors=raw_data['segmentColors'],
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Product analysis API returned data for {len(raw_data['priceVsRevenue'])} categories with {len(raw_data['segmentNames'])} segments")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in product analysis API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/pricing-analysis", response_model=PricingAnalysisResponse)
async def get_pricing_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get pricing analysis data for a specific project.
    
    This endpoint replaces the frontend getPricingAnalysisData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        service = PricingAnalysisService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        raw_data = service.get_data()
        
        # Convert to response format
        response = PricingAnalysisResponse(
            priceDistribution=[
                PriceDistribution(**dist_data) for dist_data in raw_data['priceDistribution']
            ],
            brandPriceDistribution=[
                BrandPriceDistribution(**brand_data) for brand_data in raw_data['brandPriceDistribution']
            ],
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Pricing analysis API returned {len(raw_data['priceDistribution'])} price distributions")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in pricing analysis API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/market-insights", response_model=MarketInsightsResponse)
async def get_market_insights(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get market insights data for a specific project.
    
    This endpoint replaces the frontend getMarketInsightsData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        service = MarketInsightsService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        raw_data = service.get_data()
        
        # Convert to response format
        response = MarketInsightsResponse(
            segmentRevenue=SegmentRevenue(**raw_data['segmentRevenue']),
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        total_segments = len(raw_data['segmentRevenue']['dimmerSwitches']) + len(raw_data['segmentRevenue']['lightSwitches'])
        logger.info(f"Market insights API returned {total_segments} segments")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in market insights API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/package-preference", response_model=PackagePreferenceResponse)
async def get_package_preference(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get package preference data for a specific project.
    
    This endpoint replaces the frontend getPackagePreferenceData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        service = PackagePreferenceService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        raw_data = service.get_data()
        
        # Convert segment distributions to proper format
        segment_distributions = {}
        if 'segmentDistributions' in raw_data and raw_data['segmentDistributions']:
            for segment_name, segment_data in raw_data['segmentDistributions'].items():
                segment_distributions[segment_name] = [
                    PackageDistributionItem(**item_data) for item_data in segment_data
                ]
        
        # Convert to response format
        response = PackagePreferenceResponse(
            sameProductComparison=[
                SameProductComparison(**comp_data) for comp_data in raw_data['sameProductComparison']
            ],
            packageDistribution=[
                PackageDistributionItem(**dist_data) for dist_data in raw_data['packageDistribution']
            ],
            segmentDistributions=segment_distributions,
            segmentNames=raw_data.get('segmentNames', []),
            dimmerSwitches=[
                PackageDistributionItem(**dist_data) for dist_data in raw_data['dimmerSwitches']
            ],
            lightSwitches=[
                PackageDistributionItem(**dist_data) for dist_data in raw_data['lightSwitches']
            ],
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Package preference API returned {len(raw_data['packageDistribution'])} package distributions")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in package preference API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/review-insights", response_model=ReviewInsightsResponse)
async def get_review_insights_data(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get review insights data for specific project.
    
    Returns customer pain points, likes, and underserved use cases
    filtered by project ASIN list.
    """
    try:
        logger.info(f"Getting review insights data for project: {project_id}")
        
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        service = ReviewInsightsService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        data = service.get_data()
        
        return ReviewInsightsResponse(
            painPoints=data['painPoints'],
            customerLikes=data['customerLikes'],
            underservedUseCases=data['underservedUseCases']
        )
        
    except ValueError as e:
        logger.error(f"ValueError in review insights endpoint: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in review insights endpoint: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/competitor-analysis", response_model=CompetitorAnalysisResponse)
async def get_competitor_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by"),
    selected_asins: Optional[str] = Query(None, description="Comma-separated list of ASINs to analyze")
):
    """Get competitor analysis data for a specific project.
    
    This endpoint replaces the frontend getCompetitorAnalysisData() method
    with server-side implementation that applies project ASIN filtering.
    Now supports custom ASIN selection via selected_asins parameter.
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        # Parse selected ASINs if provided
        asin_list = None
        if selected_asins:
            asin_list = [asin.strip() for asin in selected_asins.split(',') if asin.strip()]
        
        service = CompetitorAnalysisService(project_id, asin_list)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        raw_data = service.get_data()
        
        # Convert to response format
        response = CompetitorAnalysisResponse(
            targetProducts=raw_data['targetProducts'],
            matrixData=raw_data['matrixData'],
            productTotalReviews=raw_data['productTotalReviews'],
            useCaseData=raw_data['useCaseData'],
            project_id=project_id,
            filtered_asin_count=len(service.project_asins),
            selected_asins=service.selected_asins
        )
        
        logger.info(f"Competitor analysis API returned {len(raw_data['matrixData'])} matrix items and {len(raw_data['useCaseData']['matrixData'])} use case items for {len(service.selected_asins)} selected ASINs")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in competitor analysis API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/all-review-data", response_model=AllReviewDataResponse)
async def get_all_review_data(
    project_id: str = Query(..., description="Project ID for ASIN filtering"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get all review data for a specific project.
    
    This endpoint replaces the frontend getAllReviewData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        service = AllReviewDataService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        raw_data = service.get_data()
        
        # Convert to response format - data is already grouped by aspect
        response = AllReviewDataResponse(
            data=raw_data['data'],  # Already grouped dict of aspect -> list of reviews
            project_id=project_id,
            filtered_asin_count=len(service.project_asins),
            total_aspects=raw_data['total_aspects'],
            total_reviews=raw_data['total_reviews']
        )
        
        logger.info(f"All review data API returned {raw_data['total_reviews']} reviews across {raw_data['total_aspects']} aspects")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in all review data API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/project-overview")
async def get_project_overview(
    project_id: str = Query(..., description="Project ID"),
    categories: Optional[str] = Query(None, description="Comma-separated list of categories to filter by"),
    packaging_types: Optional[str] = Query(None, description="Comma-separated list of packaging types to filter by"),
    segments: Optional[str] = Query(None, description="Comma-separated list of segments to filter by")
):
    """Get project data overview including basic statistics"""
    try:
        # Parse categories if provided
        category_filters = categories.split(',') if categories else None
        
        # Parse packaging types if provided
        packaging_type_filters = packaging_types.split(',') if packaging_types else None
        
        # Parse segments if provided
        segment_filters = segments.split(',') if segments else None
        
        service = ProjectOverviewService(project_id)
        
        # Apply filters if provided
        if category_filters or packaging_type_filters or segment_filters:
            service.set_filters(categories=category_filters, packaging_types=packaging_type_filters, segments=segment_filters)
        
        return service.get_project_overview()
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in project overview API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/project-segments")
async def get_project_segments(
    project_id: str = Query(..., description="Project ID")
):
    """Get project segments list"""
    try:
        service = ProjectOverviewService(project_id)
        segments = service.get_project_segments()
        
        return {
            "segments": segments,
            "project_id": project_id,
            "total_segments": len(segments)
        }
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in project segments API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/available-asins")
async def get_available_asins(
    project_id: str = Query(..., description="Project ID")
):
    """Get available ASINs with product info for competitor selection"""
    try:
        service = ProjectOverviewService(project_id)
        return service.get_available_asins_with_info()
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting available ASINs for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 