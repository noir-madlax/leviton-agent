"""FastAPI router for Categories module."""

import logging
from typing import List
from fastapi import APIRouter, HTTPException, Depends

from .models import CategoryChildrenResponse, CategoryTreeResponse, CategoryNode
from .services import CategoryService

logger = logging.getLogger(__name__)

router = APIRouter()


def get_category_service() -> CategoryService:
    """Dependency injection for CategoryService."""
    return CategoryService()


@router.get("/root", response_model=CategoryTreeResponse)
async def get_root_categories(
    service: CategoryService = Depends(get_category_service)
):
    """Get root level categories (Level 1)."""
    try:
        categories = await service.get_root_categories()
        return CategoryTreeResponse(
            success=True,
            categories=categories
        )
    except Exception as e:
        logger.error(f"Error in get_root_categories API: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/children/{parent_category_id}", response_model=CategoryChildrenResponse)
async def get_category_children(
    parent_category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    """Get children for a specific category, fetch from API if needed."""
    try:
        children = await service.get_category_children(parent_category_id)
        
        if not children:
            return CategoryChildrenResponse(
                success=True,
                children=[],
                parent_id=parent_category_id,
                message="No subcategories available",
                total_count=0
            )
        
        return CategoryChildrenResponse(
            success=True,
            children=children,
            parent_id=parent_category_id,
            total_count=len(children)
        )
        
    except Exception as e:
        logger.error(f"Error in get_category_children API for {parent_category_id}: {e}")
        return CategoryChildrenResponse(
            success=False,
            children=[],
            parent_id=parent_category_id,
            message="Failed to load subcategories",
            total_count=0
        )


@router.get("/descendants/{category_id}")
async def get_descendant_category_names(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    """Get all descendant category names for product filtering."""
    try:
        category_names = await service.get_descendant_categories(category_id)
        return {
            "success": True,
            "category_names": category_names,
            "total_count": len(category_names)
        }
    except Exception as e:
        logger.error(f"Error in get_descendant_category_names API for {category_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/path/{category_id}")
async def get_category_path(
    category_id: str,
    service: CategoryService = Depends(get_category_service)
):
    """Get the full category path from root to the specified category."""
    try:
        path = await service.get_category_path(category_id)
        return {
            "success": True,
            "path": path,
            "path_string": " > ".join([item['name'] for item in path])
        }
    except Exception as e:
        logger.error(f"Error in get_category_path API for {category_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e)) 