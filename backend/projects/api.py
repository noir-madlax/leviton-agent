"""FastAPI router for Projects module."""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query, Request, BackgroundTasks
from fastapi.responses import StreamingResponse

from .models import ProjectCreateRequest, ProjectCreateResponse, Project
from .services.project_service import ProjectService
from core.sse_manager import sse_manager

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


@router.get("/data-confirmation-by-category", tags=["Projects"])
async def get_data_confirmation_by_category_id(
    category_id: Optional[str] = Query(None, description="Filter by Amazon category ID"),
    sources: Optional[List[str]] = Query(None, description="Filter by sources"),
    brands: Optional[List[str]] = Query(None, description="Filter by brands"),
    top_sales_count: Optional[int] = Query(None, description="Limit to top N products by sales")
):
    """
    Get data confirmation data for Step2 with category ID filter.
    Supports hierarchical category filtering - selects all products under the given category.
    """
    try:
        filters = None
        if any([category_id, sources, brands, top_sales_count]):
            filters = {}
            if category_id:
                filters['category_id'] = category_id
            if sources:
                filters['sources'] = sources
            if brands:
                filters['brands'] = brands
            if top_sales_count:
                filters['topSalesCount'] = top_sales_count
        
        service = get_project_service()
        result = await service.get_data_confirmation_data_by_category_id(filters)
        return result
    except Exception as e:
        logger.error(f"Error in get_data_confirmation_by_category_id API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/create", response_model=ProjectCreateResponse)
async def create_project(
    request: ProjectCreateRequest,
    background_tasks: BackgroundTasks,
    service: ProjectService = Depends(get_project_service)
):
    """
    Create a new project and trigger background processing for analysis.
    Returns immediately with the project ID.
    """
    try:
        return await service.create_project(request, background_tasks)
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


@router.post("/trigger-review-analysis/{project_id}")
async def trigger_review_analysis(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """Manually trigger review analysis for a project."""
    try:
        # Get project details
        project_result = service.supabase.table('projects')\
            .select('selected_product_asins, selected_categories, review_analysis_status')\
            .eq('id', project_id)\
            .single()\
            .execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        project = project_result.data
        
        # Check if already processing or completed
        if project.get('review_analysis_status') in ['processing', 'completed']:
            return {
                "message": f"Review analysis already {project['review_analysis_status']} for project {project_id}",
                "status": project['review_analysis_status']
            }
        
        # Check prerequisites
        if not project.get('selected_product_asins'):
            raise HTTPException(status_code=400, detail="Project has no selected ASINs")
        
        if not project.get('selected_categories'):
            raise HTTPException(status_code=400, detail="Project has no selected categories")
        
        # Trigger review analysis
        await service._process_project_review_analysis(
            project_id,
            project['selected_product_asins'],
            project['selected_categories'][0]
        )
        
        return {
            "message": f"Review analysis triggered for project {project_id}",
            "project_id": project_id,
            "product_count": len(project['selected_product_asins']),
            "category": project['selected_categories'][0]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering review analysis for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to trigger review analysis: {str(e)}")


@router.get("/review-analysis-status/{project_id}")
async def get_review_analysis_status(
    project_id: str,
    service: ProjectService = Depends(get_project_service)
):
    """Get the current review analysis status for a project."""
    try:
        project_result = service.supabase.table('projects')\
            .select('''
                review_analysis_status,
                review_analysis_started_at,
                review_analysis_completed_at,
                review_analysis_duration_seconds,
                review_analysis_id
            ''')\
            .eq('id', project_id)\
            .single()\
            .execute()
        
        if not project_result.data:
            raise HTTPException(status_code=404, detail="Project not found")
        
        return {
            "project_id": project_id,
            **project_result.data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review analysis status for project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get review analysis status: {str(e)}")


@router.get("/progress-stream/{project_id}")
async def stream_project_progress(
    project_id: str,
    request: Request,
    service: ProjectService = Depends(get_project_service)
):
    """Stream real-time project progress updates via Server-Sent Events."""
    try:
        # Verify project exists
        project = await service.get_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        
        # Get initial progress state to send immediately to the new client
        initial_progress = await service.get_project_progress(project_id)
        
        # Return SSE stream, passing initial data to be sent first
        return StreamingResponse(
            sse_manager.stream_for_project(project_id, request, initial_progress),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        logger.error(f"Error streaming project progress for {project_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to stream project progress: {str(e)}"
        ) 