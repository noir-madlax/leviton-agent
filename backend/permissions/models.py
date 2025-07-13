"""Data models for user permissions."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class UserPermissions(BaseModel):
    """User permissions data model."""
    id: Optional[int] = None
    user_id: str
    can_import_data: bool = True
    can_create_project: bool = True
    can_send_chat: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class UserPermissionsResponse(BaseModel):
    """Response model for user permissions."""
    user_id: str
    can_import_data: bool
    can_create_project: bool
    can_send_chat: bool 