#!/usr/bin/env python3
"""
Test script to verify all imports work correctly
"""

import sys
import os

# Add parent directories to path to import modules
current_dir = os.path.dirname(os.path.abspath(__file__))  # rerun-failed-request
scraping_dir = os.path.dirname(current_dir)  # scraping
backend_dir = os.path.dirname(scraping_dir)  # backend
project_root = os.path.dirname(backend_dir)  # project root
sys.path.insert(0, project_root)

print(f"Current directory: {current_dir}")
print(f"Scraping directory: {scraping_dir}")
print(f"Backend directory: {backend_dir}")
print(f"Project root: {project_root}")
print(f"Python path: {sys.path[0]}")

try:
    print("\n🔍 Testing imports...")
    
    # Test basic imports
    from supabase import create_client, Client
    print("✅ Supabase import successful")
    
    # Test backend config
    from backend.config import settings
    print("✅ Backend config import successful")
    print(f"  - Supabase URL: {settings.SUPABASE_URL[:50]}..." if settings.SUPABASE_URL else "  - No Supabase URL")
    print(f"  - Service key available: {'Yes' if settings.SUPABASE_SERVICE_KEY else 'No'}")
    
    # Test local config
    from retry_config import (
        RetryConfig, 
        TransformationStatus, 
        WorkflowStage,
        TABLES,
        MAX_RECORDS_PER_BATCH,
        SUPPORTED_STATUSES
    )
    print("✅ Local retry config import successful")
    
    # Test creating supabase client (same as in our script)
    if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_KEY:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        print("✅ Supabase client creation successful")
    else:
        print("❌ Missing Supabase credentials")
    
    print("\n🎉 All core imports successful!")
    print("✅ The retry tool should work correctly now.")
    
except ImportError as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Unexpected error: {e}")
    sys.exit(1) 