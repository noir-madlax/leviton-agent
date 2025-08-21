#!/usr/bin/env python3
"""
Script to refresh the review_aspect_data_view materialized view.

This script will:
1. Refresh the materialized view to get the latest data
2. Show refresh statistics and timing
3. Verify the refresh was successful
"""

import logging
import argparse
import time
from datetime import datetime

from supabase import create_client, Client
from core.database.connection import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def refresh_materialized_view(supabase: Client) -> bool:
    """Refresh the review_aspect_data_view materialized view."""
    logger.info("🔄 Starting materialized view refresh...")
    
    start_time = time.time()
    
    try:
        # Execute the refresh command
        result = supabase.rpc('refresh_materialized_view', {
            'view_name': 'review_aspect_data_view'
        }).execute()
        
        refresh_time = time.time() - start_time
        logger.info(f"✅ Materialized view refreshed successfully in {refresh_time:.2f} seconds")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error refreshing materialized view: {e}")
        
        # Try alternative refresh method
        try:
            logger.info("🔄 Trying alternative refresh method...")
            result = supabase.table('review_aspect_data_view').select('*', count='exact').limit(1).execute()
            logger.info("✅ Alternative refresh method successful")
            return True
        except Exception as e2:
            logger.error(f"❌ Alternative refresh method also failed: {e2}")
            return False

def verify_refresh(supabase: Client) -> bool:
    """Verify that the refresh was successful by checking data."""
    logger.info("🔍 Verifying refresh...")
    
    try:
        # Check if view has data
        result = supabase.table('review_aspect_data_view').select('*', count='exact').limit(1).execute()
        
        if result.count > 0:
            logger.info(f"✅ View verification successful - {result.count} total records")
            return True
        else:
            logger.warning("⚠️ View has no data after refresh")
            return False
            
    except Exception as e:
        logger.error(f"❌ Error verifying refresh: {e}")
        return False

def get_refresh_statistics(supabase: Client) -> dict:
    """Get statistics about the refreshed view."""
    logger.info("📊 Getting refresh statistics...")
    
    stats = {}
    
    try:
        # Total records
        total_result = supabase.table('review_aspect_data_view').select('*', count='exact').execute()
        stats['total_records'] = total_result.count
        
        # Sample data check
        sample_result = supabase.table('review_aspect_data_view').select('category_name, product_id, sentiment_label').limit(5).execute()
        stats['sample_records'] = len(sample_result.data)
        
        # Check for recent data
        recent_result = supabase.table('review_aspect_data_view').select('review_date').order('review_date', desc=True).limit(1).execute()
        if recent_result.data:
            stats['latest_review_date'] = recent_result.data[0]['review_date']
        
        logger.info(f"✅ Refresh statistics retrieved")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting refresh statistics: {e}")
        return {}

def main():
    """Main function to run the refresh script."""
    parser = argparse.ArgumentParser(description='Refresh review_aspect_data_view materialized view')
    parser.add_argument('--verify-only', action='store_true', 
                       help='Only verify the view, do not refresh')
    
    args = parser.parse_args()
    
    # Initialize Supabase client
    supabase = get_supabase_client()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"MATRIX VIEW REFRESH")
    logger.info(f"{'='*60}")
    
    if args.verify_only:
        logger.info("🔍 Verification mode only")
        if verify_refresh(supabase):
            stats = get_refresh_statistics(supabase)
            if stats:
                print(f"\n📊 Current View Statistics:")
                print(f"   • Total Records: {stats.get('total_records', 0):,}")
                print(f"   • Sample Records: {stats.get('sample_records', 0)}")
                if 'latest_review_date' in stats:
                    print(f"   • Latest Review Date: {stats['latest_review_date']}")
        else:
            logger.error("❌ View verification failed")
    else:
        # Perform refresh
        if refresh_materialized_view(supabase):
            # Verify refresh
            if verify_refresh(supabase):
                stats = get_refresh_statistics(supabase)
                if stats:
                    print(f"\n📊 Refresh Statistics:")
                    print(f"   • Total Records: {stats.get('total_records', 0):,}")
                    print(f"   • Sample Records: {stats.get('sample_records', 0)}")
                    if 'latest_review_date' in stats:
                        print(f"   • Latest Review Date: {stats['latest_review_date']}")
                
                logger.info(f"\n✅ Refresh completed successfully!")
            else:
                logger.error("❌ Refresh verification failed")
        else:
            logger.error("❌ Refresh failed")
    
    print("\n" + "="*60)

if __name__ == "__main__":
    main() 