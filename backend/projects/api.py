"""FastAPI router for Projects module."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query

from .models import ProjectCreateRequest, ProjectCreateResponse, Project
from .services.project_service import ProjectService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_project_service() -> ProjectService:
    """Dependency injection for ProjectService."""
    return ProjectService()


@router.get("/data-confirmation", tags=["Projects"])
async def get_data_confirmation_data(
    categories: Optional[List[str]] = Query(None, description="Filter by categories"),
    sources: Optional[List[str]] = Query(None, description="Filter by sources"),
    brands: Optional[List[str]] = Query(None, description="Filter by brands"),
    top_sales_count: Optional[int] = Query(None, description="Limit to top N products by sales")
):
    """
    Get data confirmation data for Step2 with optional filters.
    Used by frontend for data scope selection.
    """
    try:
        filters = None
        if any([categories, sources, brands, top_sales_count]):
            filters = {}
            if categories:
                filters['categories'] = categories
            if sources:
                filters['sources'] = sources
            if brands:
                filters['brands'] = brands
            if top_sales_count:
                filters['topSalesCount'] = top_sales_count
        
        service = get_project_service()
        result = await service.get_data_confirmation_data(filters)
        return result
    except Exception as e:
        logger.error(f"Error in get_data_confirmation_data API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=ProjectCreateResponse)
async def create_project(
    request: ProjectCreateRequest,
    service: ProjectService = Depends(get_project_service)
):
    """Create a new project with ASIN extraction."""
    try:
        return await service.create_project(request)
    except Exception as e:
        logger.error(f"Error creating project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create project: {str(e)}")


@router.get("/", response_model=List[Project])
async def list_projects(
    service: ProjectService = Depends(get_project_service)
):
    """List all active projects."""
    try:
        return await service.list_projects()
    except Exception as e:
        logger.error(f"Error listing projects: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list projects: {str(e)}")


@router.get("/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """Get project by ID."""
    try:
        return await service.get_project(project_id)
    except Exception as e:
        logger.error(f"Error getting project: {e}")
        raise HTTPException(status_code=404, detail=f"Project not found: {str(e)}")


@router.get("/progress/{project_id}", response_model=Dict[str, Any])
async def get_project_progress(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """Get project processing progress and status."""
    try:
        progress = await service.get_project_progress(project_id)
        return progress
    except Exception as e:
        logger.error(f"Error getting project progress: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get project progress: {str(e)}") 