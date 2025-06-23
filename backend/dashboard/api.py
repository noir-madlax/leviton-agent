"""FastAPI router for Dashboard module."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Query

from .models import BrandAnalysisResponse, BrandCategoryData
from .services.brand_analysis_service import BrandAnalysisService

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