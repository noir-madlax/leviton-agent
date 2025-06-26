"""FastAPI router for Dashboard module."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query

from .models import (
    BrandAnalysisResponse, BrandCategoryData,
    ProductAnalysisResponse, CategoryProducts, ProductInfo,
    PricingAnalysisResponse, PriceDistribution, BrandPriceDistribution, PriceStats, PriceStatsGroup, BrandPrices,
    MarketInsightsResponse, SegmentRevenue, SegmentData,
    PackagePreferenceResponse, SameProductComparison, PackageDistributionItem,
    ReviewInsightsResponse,
    CompetitorAnalysisResponse
)
from .services.brand_analysis_service import BrandAnalysisService
from .services.product_analysis_service import ProductAnalysisService
from .services.pricing_analysis_service import PricingAnalysisService
from .services.market_insights_service import MarketInsightsService
from .services.package_preference_service import PackagePreferenceService
from .services.review_insights_service import ReviewInsightsService
from .services.competitor_analysis_service import CompetitorAnalysisService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/brand-analysis", response_model=BrandAnalysisResponse)
async def get_brand_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get brand category revenue analysis for a specific project.
    
    This endpoint replaces the frontend getBrandCategoryRevenue() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        # Initialize service with project-specific ASIN filtering
        service = BrandAnalysisService(project_id)
        
        # Get filtered data
        brand_data = service.get_data()
        
        # Prepare response with metadata
        response = BrandAnalysisResponse(
            data=[BrandCategoryData(**item) for item in brand_data],
            project_id=project_id,
            total_brands=len(brand_data),
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Brand analysis API returned {len(brand_data)} brands for project {project_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in brand analysis API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/product-analysis", response_model=ProductAnalysisResponse)
async def get_product_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get product analysis data for a specific project.
    
    This endpoint replaces the frontend getProductAnalysisData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        service = ProductAnalysisService(project_id)
        raw_data = service.get_data()
        
        # Convert to response format
        response = ProductAnalysisResponse(
            priceVsRevenue=[
                CategoryProducts(**category_data) for category_data in raw_data['priceVsRevenue']
            ],
            topProducts=[
                CategoryProducts(**category_data) for category_data in raw_data['topProducts']
            ],
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Product analysis API returned data for {len(raw_data['priceVsRevenue'])} categories")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in product analysis API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.get("/pricing-analysis", response_model=PricingAnalysisResponse)
async def get_pricing_analysis(
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get pricing analysis data for a specific project.
    
    This endpoint replaces the frontend getPricingAnalysisData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        service = PricingAnalysisService(project_id)
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
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get market insights data for a specific project.
    
    This endpoint replaces the frontend getMarketInsightsData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        service = MarketInsightsService(project_id)
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
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get package preference data for a specific project.
    
    This endpoint replaces the frontend getPackagePreferenceData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        service = PackagePreferenceService(project_id)
        raw_data = service.get_data()
        
        # Convert to response format
        response = PackagePreferenceResponse(
            sameProductComparison=[
                SameProductComparison(**comp_data) for comp_data in raw_data['sameProductComparison']
            ],
            packageDistribution=[
                PackageDistributionItem(**dist_data) for dist_data in raw_data['packageDistribution']
            ],
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
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get review insights data for specific project.
    
    Returns customer pain points, likes, and underserved use cases
    filtered by project ASIN list.
    """
    try:
        logger.info(f"Getting review insights data for project: {project_id}")
        
        service = ReviewInsightsService(project_id)
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
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get competitor analysis data for a specific project.
    
    This endpoint replaces the frontend getCompetitorAnalysisData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        service = CompetitorAnalysisService(project_id)
        raw_data = service.get_data()
        
        # Convert to response format
        response = CompetitorAnalysisResponse(
            targetProducts=raw_data['targetProducts'],
            matrixData=raw_data['matrixData'],
            productTotalReviews=raw_data['productTotalReviews'],
            useCaseData=raw_data['useCaseData'],
            project_id=project_id,
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Competitor analysis API returned {len(raw_data['matrixData'])} matrix items and {len(raw_data['useCaseData']['matrixData'])} use case items")
        return response
        
    except ValueError as e:
        logger.error(f"Invalid project {project_id}: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error in competitor analysis API for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 