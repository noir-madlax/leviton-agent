#!/usr/bin/env python3
"""Debug script for review analysis service."""

import asyncio
import logging
from dashboard.charts.reviewAnalysis.service import ReviewAnalysisChartService

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def debug_review_analysis():
    """Debug the review analysis service."""
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    print(f"🔍 Debugging Review Analysis Service")
    print(f"📅 Project ID: {project_id}")
    print("=" * 60)
    
    try:
        # Test 1: Service initialization
        print("\n1️⃣ Testing service initialization...")
        service = ReviewAnalysisChartService(
            project_id=project_id,
            filters={}
        )
        print("✅ Service initialized successfully")
        
        # Test 2: Check project ASINs
        print("\n2️⃣ Checking project ASINs...")
        project_asins = service._get_project_asins()
        print(f"📊 Project ASINs: {len(project_asins)} found")
        if project_asins:
            print(f"   Sample ASINs: {project_asins[:5]}")
        else:
            print("   ⚠️  No project ASINs found!")
        
        # Test 3: Check filtered ASINs
        print("\n3️⃣ Checking filtered ASINs...")
        filtered_asins = service._get_asins_to_analyze()
        print(f"📊 Filtered ASINs: {len(filtered_asins)} found")
        if filtered_asins:
            print(f"   Sample ASINs: {filtered_asins[:5]}")
        else:
            print("   ⚠️  No filtered ASINs found!")
        
        # Test 4: Check if we have any review data
        print("\n4️⃣ Checking review data...")
        if filtered_asins:
            # Get a sample of review data
            result = service.supabase.table('review_aspect_data_view').select(
                'product_id, category_pk, category_name'
            ).eq('project_id', project_id).in_('product_id', filtered_asins[:5]).limit(5).execute()
            
            if result.data:
                print(f"📊 Review data found: {len(result.data)} records")
                print(f"   Sample: {result.data[0]}")
            else:
                print("   ⚠️  No review data found!")
        else:
            print("   ⚠️  Skipping review data check (no filtered ASINs)")
        
        # Test 5: Try to get top categories
        print("\n5️⃣ Testing top categories...")
        if filtered_asins:
            options = {
                "aspect_type": "phy_perf",
                "sort_by": "mentions",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_mentions": 1
            }
            
            result = await service.get_top_categories(options)
            print(f"📊 Top categories result: {result['total_categories']} categories")
            if result['categories']:
                print(f"   Sample category: {result['categories'][0]['category_name']}")
            else:
                print("   ⚠️  No categories found!")
        else:
            print("   ⚠️  Skipping top categories test (no filtered ASINs)")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_review_analysis()) 