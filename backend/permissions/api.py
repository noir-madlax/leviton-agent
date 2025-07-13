"""FastAPI router for user permissions."""

import logging
from fastapi import APIRouter, HTTPException, Query, Depends
from .services import PermissionService
from .models import UserPermissionsResponse

logger = logging.getLogger(__name__)

router = APIRouter()


def get_permission_service() -> PermissionService:
    """Dependency injection for PermissionService."""
    return PermissionService()


@router.get("/permissions/{user_id}", response_model=UserPermissionsResponse)
async def get_user_permissions(
    user_id: str,
    service: PermissionService = Depends(get_permission_service)
):
    """Get user permissions by user ID."""
    try:
        permissions = await service.get_user_permissions(user_id)
        if permissions is None:
            raise HTTPException(status_code=404, detail="User permissions not found")
        return permissions
    except Exception as e:
        logger.error(f"Error getting user permissions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get user permissions: {str(e)}")


@router.post("/permissions/initialize")
async def initialize_permissions(
    service: PermissionService = Depends(get_permission_service)
):
    """Initialize permissions for all existing users."""
    try:
        created_count = await service.initialize_permissions_for_existing_users()
        return {
            "message": f"Initialized permissions for {created_count} users",
            "created_count": created_count
        }
    except Exception as e:
        logger.error(f"Error initializing permissions: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to initialize permissions: {str(e)}") 