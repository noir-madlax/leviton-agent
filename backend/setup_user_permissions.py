#!/usr/bin/env python3
"""
Setup user permissions for existing users in Supabase database
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the backend directory to the Python path
backend_dir = Path(__file__).parent
sys.path.insert(0, str(backend_dir))

from core.database.connection import get_supabase_client
from permissions.services import PermissionService

async def setup_user_permissions():
    """Set up user permissions table and initialize permissions for existing users"""
    
    # Read SQL file
    sql_file = backend_dir / "sql" / "003_create_user_permissions.sql"
    
    if not sql_file.exists():
        print(f"Error: SQL file not found at {sql_file}")
        return False
    
    print("🔧 Setting up user permissions...")
    
    try:
        # Get Supabase client
        supabase = get_supabase_client()
        
        # Read and execute SQL file
        with open(sql_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Execute the SQL (this will create the table if it doesn't exist)
        print("📝 Creating user_permissions table...")
        # Note: Supabase Python client doesn't support raw SQL execution
        # The table should be created manually in the Supabase dashboard
        print("⚠️  Please create the user_permissions table manually in Supabase dashboard using:")
        print(f"   SQL file: {sql_file}")
        
        # Initialize permissions for existing users
        print("👥 Initializing permissions for existing users...")
        permission_service = PermissionService()
        created_count = await permission_service.initialize_permissions_for_existing_users()
        
        print(f"✅ User permissions setup completed!")
        print(f"📊 Created permissions for {created_count} users")
        print("🔒 All users have been granted default permissions:")
        print("   - can_import_data: TRUE")
        print("   - can_create_project: TRUE")
        print("   - can_send_chat: TRUE")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up user permissions: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(setup_user_permissions())
    if not success:
        sys.exit(1)
    
    print("\n🎉 Setup completed successfully!")
    print("You can now control user permissions by updating the user_permissions table.") 