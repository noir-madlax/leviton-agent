#!/usr/bin/env python3
"""
Simple script to check if B0BVKZLT3B exists in the materialized view.
"""

import logging
from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_asin_in_view(asin: str):
    """Check if a specific ASIN exists in the materialized view."""
    client = get_supabase_client()
    
    logger.info(f"🔍 Checking if {asin} exists in review_aspect_data_view")
    
    # Check if ASIN exists in review_aspect_data_view
    result = client.table('review_aspect_data_view').select('*').eq('product_id', asin).limit(5).execute()
    
    if result.data:
        logger.info(f"✅ {asin} found in review_aspect_data_view: {len(result.data)} records")
        logger.info(f"Sample record:")
        logger.info(f"  Category: {result.data[0].get('category_name')}")
        logger.info(f"  Sentiment: {result.data[0].get('sentiment')}")
        logger.info(f"  Review ID: {result.data[0].get('review_id')}")
        logger.info(f"  Review text length: {len(result.data[0].get('review_text', ''))}")
        return True
    else:
        logger.warning(f"❌ {asin} NOT found in review_aspect_data_view")
        return False

if __name__ == "__main__":
    # Check B0BVKZLT3B
    check_asin_in_view('B0BVKZLT3B')
    
    # Also check a working ASIN for comparison
    print("\n" + "="*50)
    check_asin_in_view('B00NG0ELL0') 