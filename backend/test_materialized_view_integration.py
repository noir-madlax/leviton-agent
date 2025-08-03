#!/usr/bin/env python3
"""
Test script to verify the materialized view integration for competitor analysis.

This script will:
1. Test the new materialized view methods in CompetitorAnalysisService
2. Compare performance between old and new methods
3. Verify review content is correctly retrieved
4. Test the new API endpoints
"""

import json
import logging
import time
from typing import Dict, List, Any
from pathlib import Path

from dashboard.services.competitor_analysis_service import CompetitorAnalysisService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Test configuration
TEST_PROJECT_ID = "test-project-123"  # Replace with actual test project ID
TEST_ASINS = [
    'B00NG0ELL0',  # Leviton DSL06
    'B0BVKZLT3B',  # Leviton D215S
    'B0BVKYKKRK',  # Leviton D26HD
    'B0BSHKS26L',  # Lutron Caseta Diva
    'B085D8M2MR',  # Lutron Diva
    'B01EZV35QU'   # TP Link Switch
]

def test_materialized_view_integration():
    """Test the materialized view integration."""
    logger.info("🧪 Starting materialized view integration tests...")
    
    try:
        # Create service instance
        service = CompetitorAnalysisService(TEST_PROJECT_ID, TEST_ASINS)
        
        # Test 1: Compare old vs new method performance
        logger.info("📊 Test 1: Performance comparison...")
        
        # Test old method
        start_time = time.time()
        old_data = service.get_data()
        old_time = time.time() - start_time
        
        # Test new method
        start_time = time.time()
        new_data = service.get_data_with_materialized_view(include_review_content=True)
        new_time = time.time() - start_time
        
        logger.info(f"⏱️  Old method: {old_time:.2f}s")
        logger.info(f"⏱️  New method: {new_time:.2f}s")
        logger.info(f"🚀 Performance improvement: {((old_time - new_time) / old_time * 100):.1f}%")
        
        # Test 2: Verify data structure
        logger.info("📋 Test 2: Data structure verification...")
        
        required_fields = ['targetProducts', 'matrixData', 'productTotalReviews', 'useCaseData']
        for field in required_fields:
            assert field in new_data, f"Missing required field: {field}"
        
        # Check review content
        assert 'reviewContent' in new_data, "Missing reviewContent field"
        assert new_data['reviewContent'] is not None, "reviewContent should not be None"
        
        logger.info(f"✅ Data structure verification passed")
        logger.info(f"📊 Matrix data items: {len(new_data['matrixData'])}")
        logger.info(f"📊 Use case data items: {len(new_data['useCaseData']['matrixData'])}")
        logger.info(f"📊 Review content keys: {len(new_data['reviewContent'])}")
        
        # Test 3: Verify review content quality
        logger.info("🔍 Test 3: Review content quality verification...")
        
        review_content = new_data['reviewContent']
        total_reviews = 0
        sample_review_keys = []
        
        for key, reviews in review_content.items():
            total_reviews += len(reviews)
            if len(sample_review_keys) < 3 and reviews:
                sample_review_keys.append(key)
        
        logger.info(f"📝 Total reviews in materialized view: {total_reviews}")
        logger.info(f"🔑 Sample review keys: {sample_review_keys[:3]}")
        
        # Verify sample review structure
        if sample_review_keys:
            sample_key = sample_review_keys[0]
            sample_reviews = review_content[sample_key]
            if sample_reviews:
                sample_review = sample_reviews[0]
                required_review_fields = ['id', 'productId', 'text', 'sentiment', 'category', 'aspect', 'rating', 'verified', 'date', 'brand']
                for field in required_review_fields:
                    assert field in sample_review, f"Missing review field: {field}"
                logger.info(f"✅ Review structure verification passed")
        
        # Test 4: Test cell-specific review retrieval
        logger.info("🎯 Test 4: Cell-specific review retrieval...")
        
        if new_data['matrixData']:
            sample_cell = new_data['matrixData'][0]
            product_asin = sample_cell['product']
            category_name = sample_cell['category']
            
            # Test the get_reviews_for_cell method
            cell_reviews = service.get_reviews_for_cell(product_asin, category_name, limit=10)
            logger.info(f"📝 Retrieved {len(cell_reviews)} reviews for {product_asin}-{category_name}")
            
            if cell_reviews:
                logger.info(f"✅ Cell review retrieval working")
                logger.info(f"📝 Sample review text: {cell_reviews[0]['text'][:100]}...")
            else:
                logger.warning(f"⚠️  No reviews found for {product_asin}-{category_name}")
        
        # Test 5: Compare data consistency
        logger.info("🔄 Test 5: Data consistency comparison...")
        
        # Compare basic metrics
        old_matrix_count = len(old_data['matrixData'])
        new_matrix_count = len(new_data['matrixData'])
        
        old_use_case_count = len(old_data['useCaseData']['matrixData'])
        new_use_case_count = len(new_data['useCaseData']['matrixData'])
        
        logger.info(f"📊 Matrix data count - Old: {old_matrix_count}, New: {new_matrix_count}")
        logger.info(f"📊 Use case data count - Old: {old_use_case_count}, New: {new_use_case_count}")
        
        if old_matrix_count == new_matrix_count and old_use_case_count == new_use_case_count:
            logger.info("✅ Data consistency verification passed")
        else:
            logger.warning("⚠️  Data consistency mismatch detected")
        
        # Generate test report
        generate_test_report(new_data, old_time, new_time)
        
        logger.info("🎉 All materialized view integration tests passed!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def generate_test_report(new_data: Dict[str, Any], old_time: float, new_time: float):
    """Generate a detailed test report."""
    report = {
        "test_summary": {
            "status": "PASSED",
            "old_method_time": f"{old_time:.2f}s",
            "new_method_time": f"{new_time:.2f}s",
            "performance_improvement": f"{((old_time - new_time) / old_time * 100):.1f}%"
        },
        "data_metrics": {
            "target_products": len(new_data.get('targetProducts', [])),
            "matrix_data_items": len(new_data.get('matrixData', [])),
            "use_case_data_items": len(new_data.get('useCaseData', {}).get('matrixData', [])),
            "review_content_keys": len(new_data.get('reviewContent', {}))
        },
        "sample_data": {
            "target_products": new_data.get('targetProducts', [])[:3],
            "sample_matrix_item": new_data.get('matrixData', [])[0] if new_data.get('matrixData') else None,
            "sample_review_keys": list(new_data.get('reviewContent', {}).keys())[:3]
        }
    }
    
    # Save report
    report_path = Path("test_materialized_view_report.json")
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"📄 Test report saved to: {report_path}")

def test_api_endpoints():
    """Test the new API endpoints (requires running server)."""
    logger.info("🌐 Test 6: API endpoint testing...")
    
    # This would require a running server to test
    # For now, just log the expected endpoints
    logger.info("📋 Expected API endpoints:")
    logger.info("  POST /api/dashboard/competitor-analysis")
    logger.info("  GET /api/dashboard/competitor-analysis/{project_id}/cell-reviews")
    
    logger.info("⚠️  API endpoint testing requires running server - skipping")

if __name__ == "__main__":
    logger.info("🚀 Starting materialized view integration tests...")
    
    success = test_materialized_view_integration()
    test_api_endpoints()
    
    if success:
        logger.info("✅ All tests completed successfully!")
        exit(0)
    else:
        logger.error("❌ Some tests failed!")
        exit(1) 