#!/usr/bin/env python3
"""
Create Sales History Tables

This script creates the sales history tables in the database using the SQL migration.
"""

import os
import sys
import logging
from pathlib import Path

# Add the backend directory to the path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from core.database.connection import get_supabase_service_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_tables():
    """Create the sales history tables."""
    try:
        logger.info("Creating sales history tables...")
        
        # Read the SQL file
        sql_file_path = Path(__file__).parent / "sql" / "001_create_sales_history_tables.sql"
        
        if not sql_file_path.exists():
            logger.error(f"SQL file not found: {sql_file_path}")
            return False
        
        with open(sql_file_path, 'r') as f:
            sql_content = f.read()
        
        logger.info(f"Read SQL file: {sql_file_path}")
        
        # Get Supabase client
        supabase = get_supabase_service_client()
        
        # Execute the SQL
        logger.info("Executing SQL to create tables...")
        result = supabase.rpc('exec_sql', {'sql': sql_content}).execute()
        
        logger.info("Tables created successfully!")
        logger.info(f"Result: {result}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating tables: {e}")
        return False

def check_tables_exist():
    """Check if the tables already exist."""
    try:
        supabase = get_supabase_service_client()
        
        # Check daily table
        result = supabase.table('sales_history_daily').select('*').limit(1).execute()
        logger.info("sales_history_daily table exists")
        
        # Check monthly table
        result = supabase.table('sales_history_monthly').select('*').limit(1).execute()
        logger.info("sales_history_monthly table exists")
        
        return True
        
    except Exception as e:
        logger.info(f"Tables don't exist yet: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 60)
    logger.info("SALES HISTORY TABLES CREATION")
    logger.info("=" * 60)
    
    # Check if tables already exist
    if check_tables_exist():
        logger.info("Tables already exist!")
    else:
        # Create tables
        if create_tables():
            logger.info("✅ Tables created successfully!")
        else:
            logger.error("❌ Failed to create tables!")
            sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("COMPLETED")
    logger.info("=" * 60) 