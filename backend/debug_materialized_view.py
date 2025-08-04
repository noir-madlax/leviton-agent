#!/usr/bin/env python3
"""
Debug script to understand why B0BVKZLT3B is not appearing in the materialized view.
"""

import logging
from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def debug_materialized_view_missing_asin(asin: str):
    """Debug why a specific ASIN is missing from the materialized view."""
    client = get_supabase_client()
    
    logger.info(f"🔍 Debugging why {asin} is missing from materialized view")
    logger.info("=" * 60)
    
    # Step 1: Check if ASIN exists in product_reviews
    result = client.table('product_reviews').select('review_id,review_text').eq('product_id', asin).limit(5).execute()
    logger.info(f"1. Product reviews for {asin}: {len(result.data)} found")
    if result.data:
        logger.info(f"   Sample review_text length: {len(result.data[0].get('review_text', ''))}")
        logger.info(f"   review_text IS NOT NULL: {result.data[0].get('review_text') is not None}")
    
    # Step 2: Check if ASIN exists in product_wide_table
    result = client.table('product_wide_table').select('platform_id').eq('platform_id', asin).execute()
    logger.info(f"2. Product wide table for {asin}: {len(result.data)} found")
    
    # Step 3: Check aspects for this ASIN
    result = client.table('review_analysis_aspects').select('aspect_pk,category_pk').eq('product_id', asin).limit(5).execute()
    logger.info(f"3. Aspects for {asin}: {len(result.data)} found")
    if result.data:
        category_pks = [r['category_pk'] for r in result.data]
        logger.info(f"   Sample category_pks: {category_pks[:3]}")
    
    # Step 4: Check if these categories are final stage
    if result.data:
        category_pks = [r['category_pk'] for r in result.data]
        result = client.table('review_analysis_aspect_categories').select('category_pk,name,stage').in_('category_pk', category_pks[:10]).execute()
        logger.info(f"4. Categories for {asin} aspects: {len(result.data)} found")
        for cat in result.data:
            logger.info(f"   Category {cat['category_pk']}: {cat['name']} (stage: {cat['stage']})")
    
    # Step 5: Check aspect occurrences
    result = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).execute()
    if result.data:
        aspect_pks = [r['aspect_pk'] for r in result.data]
        result = client.table('review_analysis_aspect_occurrences').select('aspect_pk').in_('aspect_pk', aspect_pks[:10]).execute()
        logger.info(f"5. Aspect occurrences for {asin}: {len(result.data)} found (sampling first 10 aspects)")
    
    # Step 6: Test the exact materialized view query manually
    logger.info("6. Testing manual query to replicate materialized view...")
    try:
        # This is a simplified version of the materialized view query
        query = f"""
        SELECT COUNT(*) as count
        FROM review_analysis_aspect_categories rac
        JOIN review_analysis_aspects raa ON rac.category_pk = raa.category_pk
        JOIN review_analysis_aspect_occurrences rao ON raa.aspect_pk = rao.aspect_pk
        JOIN product_reviews pr ON rao.review_id::text = pr.review_id::text AND raa.product_id = pr.product_id
        JOIN product_wide_table pwt ON raa.product_id = pwt.platform_id
        WHERE rac.stage = 'final' 
          AND rac.name != 'OUT_OF_SCOPE'
          AND pr.review_text IS NOT NULL
          AND raa.product_id = '{asin}'
        """
        
        # Use a simple count query to test
        result = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).execute()
        if result.data:
            aspect_pks = [r['aspect_pk'] for r in result.data]
            result = client.table('review_analysis_aspect_occurrences').select('aspect_pk').in_('aspect_pk', aspect_pks).execute()
            logger.info(f"   Manual count for {asin}: {len(result.data)} occurrences")
        
    except Exception as e:
        logger.error(f"   Error in manual query: {e}")
    
    logger.info("=" * 60)

def main():
    """Main function to debug the missing ASIN."""
    missing_asin = "B0BVKZLT3B"
    debug_materialized_view_missing_asin(missing_asin)

if __name__ == "__main__":
    main() 