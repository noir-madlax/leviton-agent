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
from core.database.connection import get_supabase_client

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
        
        # Get filtered data (new format with segments)
        brand_data = service.get_data()
        
        # Extract data for response
        brand_category_data = brand_data.get('brandCategoryRevenue', [])
        segment_names = brand_data.get('segmentNames', [])
        segment_colors = brand_data.get('segmentColors', [])
        
        # Prepare response with new format including segments
        response = BrandAnalysisResponse(
            data=[BrandCategoryData(**item) for item in brand_category_data],
            segmentNames=segment_names,
            segmentColors=segment_colors,
            project_id=project_id,
            total_brands=len(brand_category_data),
            filtered_asin_count=len(service.project_asins)
        )
        
        logger.info(f"Brand analysis API returned {len(brand_category_data)} brands with {len(segment_names)} segments for project {project_id}")
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
    
    Enhanced version: Returns complete data format including segment summary, 
    segment names, and colors for frontend compatibility.
    """
    try:
        service = ProductAnalysisService(project_id)
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


@router.get("/all-review-data", response_model=AllReviewDataResponse)
async def get_all_review_data(
    project_id: str = Query(..., description="Project ID for ASIN filtering")
):
    """Get all review data for a specific project.
    
    This endpoint replaces the frontend getAllReviewData() method
    with server-side implementation that applies project ASIN filtering.
    """
    try:
        service = AllReviewDataService(project_id)
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
    project_id: str = Query(..., description="Project ID")
):
    """Get project data overview including basic statistics"""
    try:
        supabase = get_supabase_client()
        
        # Get project basic info
        project_response = supabase.table('projects').select(
            'project_name, total_products, total_brands, total_reviews, '
            'selected_categories, selected_sources, selected_product_asins, created_at'
        ).eq('id', project_id).single().execute()
        
        if not project_response.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project_info = project_response.data
        
        # Get segment count from products in this project
        if project_info.get('selected_product_asins'):
            asins_list = project_info['selected_product_asins']
            
            # Get distinct product segments
            segments_response = supabase.table('product_wide_table').select(
                'product_segment'
            ).in_('platform_id', asins_list).neq('product_segment', None).execute()
            
            unique_segments = set()
            if segments_response.data:
                for item in segments_response.data:
                    if item.get('product_segment'):
                        unique_segments.add(item['product_segment'])
            
            segment_count = len(unique_segments)
            
            # Get categories available in this project
            categories_response = supabase.table('product_wide_table').select(
                'category'
            ).in_('platform_id', asins_list).neq('category', None).execute()
            
            unique_categories = set()
            if categories_response.data:
                for item in categories_response.data:
                    if item.get('category'):
                        unique_categories.add(item['category'])
            
            available_categories = sorted(list(unique_categories))
            
            # Get data source distribution
            sources_response = supabase.table('product_wide_table').select(
                'source'
            ).in_('platform_id', asins_list).neq('source', None).execute()
            
            sources_count = {}
            total_sources = 0
            if sources_response.data:
                for item in sources_response.data:
                    source = item.get('source')
                    if source:
                        sources_count[source] = sources_count.get(source, 0) + 1
                        total_sources += 1
            
            sources_distribution = []
            for source, count in sources_count.items():
                percentage = round(count * 100.0 / total_sources, 1) if total_sources > 0 else 0
                sources_distribution.append({
                    "name": source,
                    "count": count,
                    "percentage": percentage
                })
            sources_distribution.sort(key=lambda x: x['count'], reverse=True)
            
            # Get category distribution
            categories_response = supabase.table('product_wide_table').select(
                'category'
            ).in_('platform_id', asins_list).neq('category', None).execute()
            
            categories_count = {}
            total_categories = 0
            if categories_response.data:
                for item in categories_response.data:
                    category = item.get('category')
                    if category:
                        categories_count[category] = categories_count.get(category, 0) + 1
                        total_categories += 1
            
            categories_distribution = []
            for category, count in categories_count.items():
                percentage = round(count * 100.0 / total_categories, 1) if total_categories > 0 else 0
                categories_distribution.append({
                    "name": category,
                    "count": count,
                    "percentage": percentage
                })
            categories_distribution.sort(key=lambda x: x['count'], reverse=True)
            
        else:
            segment_count = 0
            available_categories = []
            sources_distribution = []
            categories_distribution = []
        
        return {
            "project_name": project_info['project_name'],
            "created_at": project_info['created_at'],
            "stats": {
                "total_products": project_info['total_products'],
                "total_brands": project_info['total_brands'], 
                "total_reviews": project_info['total_reviews'],
                "segment_count": segment_count
            },
            "distributions": {
                "sources": sources_distribution,
                "categories": categories_distribution
            },
            "available_categories": available_categories
        }
        
    except Exception as e:
        logger.error(f"Error getting project overview: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 