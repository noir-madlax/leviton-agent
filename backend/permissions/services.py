"""User permissions service."""

import logging
from typing import Optional, List
from core.database.connection import get_supabase_client
from .models import UserPermissions, UserPermissionsResponse

logger = logging.getLogger(__name__)


class PermissionService:
    """Service for managing user permissions."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def get_user_permissions(self, user_id: str) -> Optional[UserPermissionsResponse]:
        """Get user permissions by user ID."""
        try:
            result = self.supabase.table('user_permissions').select(
                'user_id, can_import_data, can_create_project, can_send_chat'
            ).eq('user_id', user_id).single().execute()
            
            if result.data:
                return UserPermissionsResponse(**result.data)
            
            # If no permissions found, create default permissions
            return await self.create_default_permissions(user_id)
            
        except Exception as e:
            logger.error(f"Error getting user permissions for {user_id}: {e}")
            # Return default permissions on error
            return UserPermissionsResponse(
                user_id=user_id,
                can_import_data=True,
                can_create_project=True,
                can_send_chat=True
            )
    
    async def create_default_permissions(self, user_id: str) -> UserPermissionsResponse:
        """Create default permissions for a user."""
        try:
            permissions_data = {
                'user_id': user_id,
                'can_import_data': True,
                'can_create_project': True,
                'can_send_chat': True
            }
            
            result = self.supabase.table('user_permissions').insert(permissions_data).execute()
            
            if result.data:
                logger.info(f"Created default permissions for user {user_id}")
                return UserPermissionsResponse(**permissions_data)
            
            # If creation fails, return default permissions
            return UserPermissionsResponse(**permissions_data)
            
        except Exception as e:
            logger.error(f"Error creating default permissions for {user_id}: {e}")
            # Return default permissions on error
            return UserPermissionsResponse(
                user_id=user_id,
                can_import_data=True,
                can_create_project=True,
                can_send_chat=True
            )
    
    async def initialize_permissions_for_existing_users(self) -> int:
        """Initialize permissions for all existing users from auth.users."""
        try:
            # Get all users from auth.users table
            users_result = self.supabase.table('auth.users').select('id').execute()
            
            if not users_result.data:
                logger.warning("No users found in auth.users table")
                return 0
            
            # Get existing permissions to avoid duplicates
            existing_permissions = self.supabase.table('user_permissions').select('user_id').execute()
            existing_user_ids = {perm['user_id'] for perm in existing_permissions.data} if existing_permissions.data else set()
            
            # Create permissions for users who don't have them
            created_count = 0
            for user in users_result.data:
                user_id = user['id']
                if user_id not in existing_user_ids:
                    await self.create_default_permissions(user_id)
                    created_count += 1
            
            logger.info(f"Initialized permissions for {created_count} existing users")
            return created_count
            
        except Exception as e:
            logger.error(f"Error initializing permissions for existing users: {e}")
            return 0 