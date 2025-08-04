#!/usr/bin/env python3
"""
Quick test script to verify materialized view integration using a real project ID.
"""

import logging
import time
from dashboard.services.competitor_analysis_service import CompetitorAnalysisService

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Use a real project ID
REAL_PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"  # User provided project ID
TEST_ASINS = ['B00004YUO0', 'B0000CGKLR']  # Use ASINs that have data in materialized view

def quick_test():
    """Quick test of materialized view integration."""
    logger.info("🧪 Quick test of materialized view integration...")
    
    try:
        # Create service instance with real project ID
        service = CompetitorAnalysisService(REAL_PROJECT_ID, TEST_ASINS)
        
        # Test new materialized view method
        logger.info("📊 Testing new materialized view method...")
        start_time = time.time()
        new_data = service.get_data_with_materialized_view(include_review_content=True)
        new_time = time.time() - start_time
        
        logger.info(f"⏱️  New method execution time: {new_time:.2f}s")
        
        # Verify data structure
        logger.info("📋 Verifying data structure...")
        assert 'targetProducts' in new_data, "Missing targetProducts"
        assert 'matrixData' in new_data, "Missing matrixData"
        assert 'productTotalReviews' in new_data, "Missing productTotalReviews"
        assert 'useCaseData' in new_data, "Missing useCaseData"
        assert 'reviewContent' in new_data, "Missing reviewContent"
        
        logger.info(f"✅ Data structure verification passed")
        logger.info(f"📊 Matrix data items: {len(new_data['matrixData'])}")
        logger.info(f"📊 Use case data items: {len(new_data['useCaseData']['matrixData'])}")
        logger.info(f"📊 Review content keys: {len(new_data['reviewContent'])}")
        
        # Test cell-specific review retrieval
        if new_data['matrixData']:
            sample_cell = new_data['matrixData'][0]
            product_asin = sample_cell['product']
            category_name = sample_cell['category']
            
            logger.info(f"🎯 Testing cell review retrieval for {product_asin}-{category_name}...")
            cell_reviews = service.get_reviews_for_cell(product_asin, category_name, limit=5)
            logger.info(f"📝 Retrieved {len(cell_reviews)} reviews for cell")
            
            if cell_reviews:
                logger.info(f"✅ Cell review retrieval working")
                logger.info(f"📝 Sample review: {cell_reviews[0]['text'][:100]}...")
            else:
                logger.warning(f"⚠️  No reviews found for cell")
        
        # Show sample review content
        if new_data['reviewContent']:
            sample_key = list(new_data['reviewContent'].keys())[0]
            sample_reviews = new_data['reviewContent'][sample_key]
            logger.info(f"📝 Sample review key: {sample_key}")
            logger.info(f"📝 Reviews in sample: {len(sample_reviews)}")
            if sample_reviews:
                logger.info(f"📝 Sample review text: {sample_reviews[0]['text'][:100]}...")
        
        logger.info("🎉 Quick test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Quick test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = quick_test()
    exit(0 if success else 1) 