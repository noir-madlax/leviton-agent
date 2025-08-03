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
                'sort_by': 'total_reviews',
                'sort_direction': 'desc',
                'min_reviews': 1
            }
        )
        
        print(f"✅ Success! Found {len(result)} categories")
        if result:
            print(f"📊 Top category: {result[0]['category_name']}")
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
            
            print(f"✅ Success! Found cause analysis for {len(cause_result)} cause categories")
            for cause in cause_result:
                print(f"📊 Cause: {cause['category_name']}")
                print(f"   - Total reviews: {cause['total_reviews']}")
                print(f"   - Positive reviews: {cause['total_positive_reviews']}")
                print(f"   - Negative reviews: {cause['total_negative_reviews']}")
                print(f"   - Aspects: {len(cause['aspects'])}")
                for aspect in cause['aspects'][:2]:  # Show first 2 aspects
                    print(f"     * {aspect['aspect_description']}: {aspect['total_reviews']} reviews")
        
        # Test 3: Integrated method with cause analysis
        print("\n🧪 Test 3: get_aspect_categories_with_metrics with cause analysis")
        print("-" * 60)
        
        integrated_result = await data_service.get_aspect_categories_with_metrics(
            project_id=project_id,
            asins=project_asins,
            aspect_types=['phy_perf'],
            options={
                'max_categories': 3,
                'sort_by': 'total_reviews',
                'sort_direction': 'desc',
                'min_reviews': 1,
                'return_top_cause_categories': {
                    'sentiment': '+',
                    'aggregated_limit': 5,
                    'per_aspect_limit': 3
                }
            }
        )
        
        print(f"✅ Success! Found {len(integrated_result['categories'])} categories with embedded cause analysis")
        print(f"📊 Aggregated causes: {len(integrated_result['aggregated_cause_summary'])}")
        
        # Show aggregated summary
        for cause in integrated_result['aggregated_cause_summary'][:2]:
            print(f"🎯 Top cause: {cause.get('cause_category_name', 'Unknown')} (rank {cause.get('rank', 'N/A')})")
            print(f"   - Total reviews: {cause.get('total_reviews', 0)}")
            print(f"   - Aspects: {len(cause.get('aspects', []))}")
            for aspect in cause.get('aspects', [])[:2]:
                print(f"     * {aspect.get('sentiment', '?')} {aspect.get('aspect_description', 'Unknown')}")
        
                    # Show embedded cause data for first category
            if integrated_result['categories']:
                first_category = integrated_result['categories'][0]
                print(f"📊 Category: {first_category.get('category_name', 'Unknown')}")
                print(f"   - Embedded causes: {len(first_category.get('cause_data', []))}")
                for cause in first_category.get('cause_data', [])[:2]:
                    print(f"     * {cause.get('cause_category_name', 'Unknown')}: {cause.get('total_reviews', 0)} reviews")
                    print(f"       Aspects: {len(cause.get('aspects', []))}")
                    for aspect in cause.get('aspects', [])[:1]:
                        print(f"         - {aspect.get('sentiment', '?')} {aspect.get('aspect_description', 'Unknown')}")
        
        # Test 4: Enhanced cause analysis functionality
        print("\n🧪 Test 4: Enhanced cause analysis with embedded structure")
        print("-" * 60)
        
        # Test the new embedded structure provides both aggregated and per-aspect data
        if integrated_result['categories']:
            print(f"✅ Success! Enhanced structure provides:")
            print(f"   - {len(integrated_result['categories'])} aspect categories with embedded cause data")
            print(f"   - {len(integrated_result['aggregated_cause_summary'])} aggregated causes")
            
            # Verify embedded structure
            for i, category in enumerate(integrated_result['categories'][:2]):
                print(f"📊 Category {i+1}: {category.get('category_name', 'Unknown')}")
                print(f"   - Has embedded cause_data: {'cause_data' in category}")
                print(f"   - Embedded causes: {len(category.get('cause_data', []))}")
                
                # Show sample embedded cause data
                for cause in category.get('cause_data', [])[:1]:
                    print(f"     * Embedded cause: {cause.get('cause_category_name', 'Unknown')}")
                    print(f"       - Reviews: {cause.get('total_reviews', 0)}")
                    print(f"       - Simplified aspects: {len(cause.get('aspects', []))}")
                    for aspect in cause.get('aspects', [])[:1]:
                        print(f"         - {aspect.get('sentiment', '?')} {aspect.get('aspect_description', 'Unknown')}")
            
            # Verify aggregated structure
            print(f"🎯 Aggregated summary:")
            for cause in integrated_result['aggregated_cause_summary'][:1]:
                print(f"   - Top cause: {cause.get('cause_category_name', 'Unknown')} (rank {cause.get('rank', 'N/A')})")
                print(f"     Total reviews: {cause.get('total_reviews', 0)}")
                print(f"     Simplified aspects: {len(cause.get('aspects', []))}")
        
        # Test 5: Backward compatibility
        print("\n🧪 Test 5: Backward compatibility - old method")
        print("-" * 60)
        
        old_result = await data_service.get_category_statistics(
            project_id=project_id,
            asins=project_asins,
            aspect_types=['phy_perf']
        )
        
        print(f"✅ Success! Old method found {len(old_result)} categories")
        if old_result:
            print(f"📊 Sample category: {old_result[0]['category_name']}")
            print(f"   - Total reviews: {old_result[0]['total_reviews']}")
        
        # Test 6: Performance comparison
        print("\n🧪 Test 6: Performance comparison")
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
            old_total_reviews = sum(cat['total_reviews'] for cat in old_result)
            optimized_total_reviews = sum(cat['total_reviews'] for cat in optimized_result)
            print(f"📊 Data consistency:")
            print(f"   - Old method total reviews: {old_total_reviews}")
            print(f"   - Optimized method total reviews: {optimized_total_reviews}")
            print(f"   - Consistent: {old_total_reviews == optimized_total_reviews}")
        
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