#!/usr/bin/env python3
"""
Debug script to understand the review_id issue for B0BVKZLT3B.
"""

import logging
from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_review_id_issue(asin: str):
    """Debug the review_id issue for a specific ASIN."""
    client = get_supabase_client()
    
    logger.info(f"🔍 Debugging review_id issue for {asin}")
    logger.info("=" * 60)
    
    # Step 1: Check review_analysis_aspect_occurrences for this ASIN
    logger.info("1. Checking review_analysis_aspect_occurrences...")
    
    # Get aspects for this ASIN first
    aspects_result = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).execute()
    if not aspects_result.data:
        logger.error(f"No aspects found for {asin}")
        return
    
    aspect_pks = [r['aspect_pk'] for r in aspects_result.data]
    logger.info(f"Found {len(aspect_pks)} aspects for {asin}")
    
    # Get ALL occurrences for these aspects (not just limit 10)
    all_occurrences = []
    batch_size = 1000
    
    for offset in range(0, len(aspect_pks), batch_size):
        batch_aspect_pks = aspect_pks[offset:offset + batch_size]
        occurrences_result = client.table('review_analysis_aspect_occurrences').select(
            'aspect_pk,review_id,sentiment'
        ).in_('aspect_pk', batch_aspect_pks).execute()
        
        if occurrences_result.data:
            all_occurrences.extend(occurrences_result.data)
    
    logger.info(f"Found {len(all_occurrences)} total occurrences")
    
    # Check for review_id = 0
    zero_review_ids = [r for r in all_occurrences if r['review_id'] == 0]
    logger.info(f"Occurrences with review_id = 0: {len(zero_review_ids)}")
    
    if zero_review_ids:
        logger.warning("⚠️  Found occurrences with review_id = 0!")
        logger.info(f"Sample zero review_id occurrence: {zero_review_ids[0]}")
    
    # Step 2: Check if review_id = '0' exists in product_reviews
    logger.info("\n2. Checking if review_id = '0' exists in product_reviews...")
    
    # Check for review_id = '0' (as string)
    pr_result = client.table('product_reviews').select('review_id,review_text').eq('review_id', '0').eq('product_id', asin).execute()
    logger.info(f"product_reviews with review_id = '0': {len(pr_result.data)}")
    
    if pr_result.data:
        logger.info(f"Sample review with review_id = '0': {pr_result.data[0]['review_text'][:100]}...")
    
    # Step 3: Check what review_ids exist in product_reviews for this ASIN
    logger.info("\n3. Checking what review_ids exist in product_reviews...")
    pr_all_result = client.table('product_reviews').select('review_id').eq('product_id', asin).limit(10).execute()
    logger.info(f"Sample review_ids in product_reviews: {[r['review_id'] for r in pr_all_result.data]}")
    
    # Step 4: Check if there are any non-zero review_ids in occurrences
    non_zero_review_ids = [r for r in all_occurrences if r['review_id'] != 0]
    logger.info(f"\n4. Occurrences with non-zero review_ids: {len(non_zero_review_ids)}")
    
    if non_zero_review_ids:
        sample_non_zero = non_zero_review_ids[0]
        logger.info(f"Sample non-zero review_id: {sample_non_zero}")
        
        # Check if this review_id exists in product_reviews
        check_result = client.table('product_reviews').select('review_id,review_text').eq('review_id', str(sample_non_zero['review_id'])).eq('product_id', asin).execute()
        logger.info(f"Found in product_reviews: {len(check_result.data) > 0}")
    
    # Step 5: Check the materialized view directly
    logger.info("\n5. Checking materialized view directly...")
    mv_result = client.table('review_aspect_data_view').select('review_id,category_name,sentiment').eq('product_id', asin).limit(10).execute()
    logger.info(f"Materialized view records: {len(mv_result.data)}")
    
    if mv_result.data:
        logger.info("Sample materialized view records:")
        for i, record in enumerate(mv_result.data[:5]):
            logger.info(f"  {i+1}. review_id={record['review_id']}, category={record['category_name']}, sentiment={record['sentiment']}")

if __name__ == "__main__":
    debug_review_id_issue('B0BVKZLT3B') 