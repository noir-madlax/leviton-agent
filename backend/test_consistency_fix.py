#!/usr/bin/env python3
"""Test to verify that tooltip and clicked view are now consistent."""

import asyncio
import logging
from typing import Dict, Any

from dashboard.charts.reviewCore.data_service import ReviewDataService
from core.database.connection import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test parameters
PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"
CATEGORY_NAME = "Core Device Functionality"

async def test_consistency_fix():
    """Test to verify that tooltip and clicked view are now consistent."""
    
    supabase = get_supabase_client()
    data_service = ReviewDataService(supabase)
    
    try:
        # Find category ID
        logger.info(f"🔍 Testing consistency for '{CATEGORY_NAME}' in project {PROJECT_ID}")
        category_result = supabase.table('review_analysis_aspect_categories').select(
            'category_pk, name, aspect_type'
        ).eq('project_id', PROJECT_ID).eq('name', CATEGORY_NAME).execute()
        
        if not category_result.data:
            logger.error(f"❌ Category '{CATEGORY_NAME}' not found in project {PROJECT_ID}")
            return
        
        category_id = category_result.data[0]['category_pk']
        logger.info(f"✅ Found category ID: {category_id}")
        
        # Get project ASINs
        project_result = supabase.table('projects').select('selected_product_asins').eq('id', PROJECT_ID).execute()
        project_asins = project_result.data[0]['selected_product_asins']
        
        # Test 1: Tooltip data (get_category_statistics)
        logger.info(f"\n🔍 Test 1: Tooltip data (get_category_statistics)")
        
        category_stats = await data_service.get_category_statistics(
            project_id=PROJECT_ID,
            asins=project_asins,
            aspect_types=['phy_perf']
        )
        
        # Find our specific category
        tooltip_category = None
        for cat in category_stats:
            if cat['category_pk'] == category_id:
                tooltip_category = cat
                break
        
        if tooltip_category:
            logger.info(f"📊 Tooltip data for '{CATEGORY_NAME}':")
            logger.info(f"   - Total Reviews: {tooltip_category['total_reviews']}")
            logger.info(f"   - Positive Reviews: {tooltip_category['positive_reviews']}")
            logger.info(f"   - Negative Reviews: {tooltip_category['negative_reviews']}")
            logger.info(f"   - Neutral Reviews: {tooltip_category['neutral_reviews']}")
        else:
            logger.warning(f"⚠️  Category '{CATEGORY_NAME}' not found in tooltip data")
        
        # Test 2: Clicked view data (get_reviews_by_category)
        logger.info(f"\n🔍 Test 2: Clicked view data (get_reviews_by_category)")
        
        clicked_result = await data_service.get_reviews_by_category(
            project_id=PROJECT_ID,
            category_id=category_id,
            asins=project_asins,
            aspect_types=['phy_perf']
        )
        
        logger.info(f"📊 Clicked view data for '{CATEGORY_NAME}':")
        logger.info(f"   - Total Reviews: {clicked_result['total_count']}")
        logger.info(f"   - Reviews Returned: {len(clicked_result['reviews'])}")
        
        # Test 3: Consistency check
        logger.info(f"\n🔍 Test 3: Consistency check")
        
        if tooltip_category:
            tooltip_total = tooltip_category['total_reviews']
            clicked_total = clicked_result['total_count']
            
            if tooltip_total == clicked_total:
                logger.info(f"✅ CONSISTENCY ACHIEVED!")
                logger.info(f"   - Tooltip Total Reviews: {tooltip_total}")
                logger.info(f"   - Clicked View Total Reviews: {clicked_total}")
                logger.info(f"   - Both methods now return the same count!")
            else:
                logger.warning(f"⚠️  Still inconsistent:")
                logger.info(f"   - Tooltip Total Reviews: {tooltip_total}")
                logger.info(f"   - Clicked View Total Reviews: {clicked_total}")
                logger.info(f"   - Difference: {abs(tooltip_total - clicked_total)}")
        else:
            logger.warning(f"⚠️  Cannot check consistency - tooltip data not found")
        
        # Test 4: Verify the business logic is working
        logger.info(f"\n🔍 Test 4: Verify business logic")
        
        # Count reviews with mixed sentiments in the clicked view
        mixed_sentiment_reviews = 0
        for review in clicked_result['reviews']:
            aspects = review.get('aspects', [])
            has_positive = any(aspect.get('sentiment') == '+' for aspect in aspects)
            has_negative = any(aspect.get('sentiment') == '-' for aspect in aspects)
            
            if has_positive and has_negative:
                mixed_sentiment_reviews += 1
        
        logger.info(f"📊 Business logic verification:")
        logger.info(f"   - Reviews with mixed sentiments in clicked view: {mixed_sentiment_reviews}")
        logger.info(f"   - Expected: 0 (should be filtered out by business logic)")
        
        if mixed_sentiment_reviews == 0:
            logger.info(f"✅ Business logic correctly applied - no mixed sentiment reviews in clicked view")
        else:
            logger.warning(f"⚠️  Business logic not working - found {mixed_sentiment_reviews} mixed sentiment reviews")
        
    except Exception as e:
        logger.error(f"❌ Error during testing: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(test_consistency_fix()) 