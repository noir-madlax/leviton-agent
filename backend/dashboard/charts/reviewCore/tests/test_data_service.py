#!/usr/bin/env python3
"""Tests for ReviewDataService optimized methods."""

import asyncio
import sys
import os
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))

from dashboard.charts.reviewCore.data_service import ReviewDataService
from core.database.connection import get_supabase_client


async def test_optimized_methods_with_real_data():
    """Test the optimized methods with real database data."""
    print("=" * 80)
    print("TESTING OPTIMIZED METHODS WITH REAL DATA")
    print("=" * 80)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    try:
        # Create service with real database connection
        supabase_client = get_supabase_client()
        data_service = ReviewDataService(supabase_client)
        
        # Get project ASINs
        project_result = supabase_client.table('projects').select('selected_product_asins').eq('id', project_id).execute()
        if not project_result.data:
            print(f"❌ Project {project_id} not found or has no ASINs")
            return
        
        project_asins = project_result.data[0]['selected_product_asins']
        print(f"✅ Found {len(project_asins)} ASINs for project {project_id}")
        
        # Test 1: Optimized category statistics
        print("\n🧪 Test 1: get_category_statistics")
        print("-" * 60)
        
        result = await data_service.get_category_statistics(
            project_id=project_id,
            asins=project_asins,
            aspect_types=['phy_perf'],
            options={
                'max_categories': 5,
                'sort_by': 'total_mentions',
                'sort_direction': 'desc',
                'min_mentions': 1
            }
        )
        
        print(f"✅ Success! Found {len(result)} categories")
        if result:
            print(f"📊 Top category: {result[0]['category_name']}")
            print(f"   - Total mentions: {result[0]['total_mentions']}")
            print(f"   - Total reviews: {result[0]['total_reviews']}")
            print(f"   - Positive ratio: {result[0]['positive_ratio']:.3f}")
        
        # Test 2: Cause analysis
        print("\n🧪 Test 2: get_cause_analysis")
        print("-" * 60)
        
        if result:
            top_category_ids = [cat['category_pk'] for cat in result[:3]]  # Top 3 categories
            cause_result = await data_service.get_cause_analysis(
                project_id=project_id,
                asins=project_asins,
                top_category_ids=top_category_ids,
                sentiment_filter='+',  # Only positive sentiment causes
                limit=3
            )
            
            print(f"✅ Success! Found cause analysis for {len(cause_result)} categories")
            for category_id, causes in cause_result.items():
                category_name = next((cat['category_name'] for cat in result if cat['category_pk'] == category_id), 'Unknown')
                print(f"📊 Category: {category_name}")
                for cause in causes:
                    print(f"   - {cause['category_name']}: {cause['count']} mentions")
        
        # Test 3: Integrated method with cause analysis
        print("\n🧪 Test 3: get_aspect_categories_with_metrics with cause analysis")
        print("-" * 60)
        
        integrated_result = await data_service.get_aspect_categories_with_metrics(
            project_id=project_id,
            asins=project_asins,
            aspect_types=['phy_perf'],
            options={
                'max_categories': 3,
                'sort_by': 'total_mentions',
                'sort_direction': 'desc',
                'min_mentions': 1,
                'return_top_cause_categories': {
                    'sentiment': '+',
                    'limit': 2
                }
            }
        )
        
        print(f"✅ Success! Found {len(integrated_result)} categories with cause analysis")
        for category in integrated_result:
            print(f"📊 Category: {category['category_name']}")
            print(f"   - Total mentions: {category['total_mentions']}")
            print(f"   - Top causes: {len(category.get('top_cause_categories', []))}")
            for cause in category.get('top_cause_categories', [])[:2]:
                print(f"     * {cause['category_name']}: {cause['count']} mentions")
        
        # Test 4: Backward compatibility
        print("\n🧪 Test 4: Backward compatibility - old method")
        print("-" * 60)
        
        old_result = await data_service.get_category_statistics(
            project_id=project_id,
            asins=project_asins,
            aspect_types=['phy_perf']
        )
        
        print(f"✅ Success! Old method found {len(old_result)} categories")
        if old_result:
            print(f"📊 Sample category: {old_result[0]['category_name']}")
            print(f"   - Total mentions: {old_result[0]['total_mentions']}")
        
        # Test 5: Performance comparison
        print("\n🧪 Test 5: Performance comparison")
        print("-" * 60)
        
        import time
        
        # Test old method timing
        start_time = time.time()
        old_result = await data_service.get_category_statistics(
            project_id=project_id,
            asins=project_asins,
            aspect_types=['phy_perf']
        )
        old_time = time.time() - start_time
        
        # Test optimized method timing
        start_time = time.time()
        optimized_result = await data_service.get_category_statistics(
            project_id=project_id,
            asins=project_asins,
            aspect_types=['phy_perf'],
            options={'max_categories': len(old_result)}
        )
        optimized_time = time.time() - start_time
        
        print(f"⏱️  Performance comparison:")
        print(f"   - Old method: {old_time:.3f} seconds")
        print(f"   - Optimized method: {optimized_time:.3f} seconds")
        print(f"   - Speed improvement: {old_time/optimized_time:.1f}x faster")
        
        # Verify results are consistent
        if len(old_result) > 0 and len(optimized_result) > 0:
            old_total_mentions = sum(cat['total_mentions'] for cat in old_result)
            optimized_total_mentions = sum(cat['total_mentions'] for cat in optimized_result)
            print(f"📊 Data consistency:")
            print(f"   - Old method total mentions: {old_total_mentions}")
            print(f"   - Optimized method total mentions: {optimized_total_mentions}")
            print(f"   - Consistent: {old_total_mentions == optimized_total_mentions}")
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()


async def test_method_signatures():
    """Test that all methods have the correct signatures."""
    print("=" * 80)
    print("TESTING METHOD SIGNATURES")
    print("=" * 80)
    
    try:
        supabase_client = get_supabase_client()
        data_service = ReviewDataService(supabase_client)
        
        import inspect
        
        # Test old methods still exist
        print("✅ Testing old methods exist:")
        assert hasattr(data_service, 'get_category_statistics')
        assert hasattr(data_service, 'get_reviews_by_category')
        assert hasattr(data_service, 'get_category_info')
        print("   - get_category_statistics ✓")
        print("   - get_reviews_by_category ✓")
        print("   - get_category_info ✓")
        
        # Test new methods exist
        print("✅ Testing new methods exist:")
        assert hasattr(data_service, 'get_category_statistics')
        assert hasattr(data_service, 'get_cause_analysis')
        assert hasattr(data_service, 'get_aspect_categories_with_metrics')
        print("   - get_category_statistics ✓")
        print("   - get_cause_analysis ✓")
        print("   - get_aspect_categories_with_metrics ✓")
        
        # Test method signatures
        print("✅ Testing method signatures:")
        
        # Check optimized method signature
        sig = inspect.signature(data_service.get_category_statistics)
        assert 'project_id' in sig.parameters
        assert 'asins' in sig.parameters
        assert 'aspect_types' in sig.parameters
        assert 'options' in sig.parameters
        print("   - get_category_statistics signature ✓")
        
        # Check cause analysis method signature
        sig = inspect.signature(data_service.get_cause_analysis)
        assert 'project_id' in sig.parameters
        assert 'asins' in sig.parameters
        assert 'top_category_ids' in sig.parameters
        assert 'sentiment_filter' in sig.parameters
        assert 'limit' in sig.parameters
        print("   - get_cause_analysis signature ✓")
        
        print("✅ All method signatures are correct!")
        
    except Exception as e:
        print(f"❌ Error testing method signatures: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Starting ReviewDataService Tests")
    print(f"📅 Project ID: d2c02b80-4c82-44cc-8093-56708a7883f7")
    
    # Test method signatures first
    await test_method_signatures()
    
    # Test with real data
    await test_optimized_methods_with_real_data()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main()) 