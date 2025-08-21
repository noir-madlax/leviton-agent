#!/usr/bin/env python3
"""Test script for Competitor Analysis APIs."""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))

from dashboard.charts.competitorAnalysis.service import CompetitorAnalysisChartService
from dashboard.charts.competitorAnalysis.models import (
    CompetitorSummaryRequest, CompetitorSummaryResponse,
    CompetitorMatrixViewRequest, CompetitorMatrixViewResponse,
    ReviewRetrievalRequest, ReviewRetrievalResponse
)


async def test_competitor_summary_api():
    """Test the competitor summary API."""
    print("=" * 80)
    print("TESTING COMPETITOR SUMMARY API")
    print("=" * 80)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    test_asins = ["B00NG0ELL0", "B0BVKZLT3B", "B0BVKYKKRK", "B0BSHKS26L", "B085D8M2MR", "B01EZV35QU"]
    
    print(f"📅 Project ID: {project_id}")
    print(f"🔍 Testing with {len(test_asins)} ASINs")
    print("-" * 60)
    
    try:
        # Create service
        service = CompetitorAnalysisChartService(
            project_id=project_id,
            selected_asins=test_asins
        )
        
        # Get competitor summary
        result = await service.get_competitor_summary()
        
        # Print results
        print(f"✅ Success! Found {result['total_products']} products")
        print(f"📊 Summary:")
        print(f"   - Total products analyzed: {result['total_products']}")
        print(f"   - Selected ASINs: {len(result['selected_asins'])}")
        
        if result['products']:
            print(f"\n📋 Product Details:")
            for i, product in enumerate(result['products'][:3], 1):
                print(f"   {i}. {product['asin']}")
                print(f"      - Title: {product['product_title'][:60]}...")
                print(f"      - Brand: {product['brand']}")
                print(f"      - Rating: {product['rating']}")
                print(f"      - Reviews: {product['unique_reviews_count']}")
                print(f"      - Sentiment: {product['additional_metrics']['sentiment_distribution']}")
                if product['additional_metrics']['category_counts']:
                    top_categories = sorted(
                        product['additional_metrics']['category_counts'].items(),
                        key=lambda x: x[1], reverse=True
                    )[:3]
                    print(f"      - Top categories: {dict(top_categories)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def test_matrix_view_api():
    """Test the competitor matrix view API."""
    print("\n" + "=" * 80)
    print("TESTING COMPETITOR MATRIX VIEW API")
    print("=" * 80)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    test_asins = ["B00NG0ELL0", "B0BVKZLT3B", "B0BVKYKKRK"]
    
    # Test different aspect types and options
    test_cases = [
        {
            "name": "phy_perf - sorted by mentions",
            "aspect_type": "phy_perf",
            "options": {
                "sort_by": "mentions",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_mentions": 3
            }
        },
        {
            "name": "phy_perf - sorted by reviews",
            "aspect_type": "phy_perf",
            "options": {
                "sort_by": "reviews",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_reviews": 2
            }
        },
        {
            "name": "use - sorted by sentiment",
            "aspect_type": "use",
            "options": {
                "sort_by": "sentiment",
                "sort_direction": "desc",
                "max_categories": 3,
                "min_mentions": 1
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Create service
            service = CompetitorAnalysisChartService(
                project_id=project_id,
                selected_asins=test_asins
            )
            
            # Get matrix view data
            result = await service.get_matrix_view_data(
                test_case['aspect_type'], 
                test_case['options']
            )
            
            # Print results
            print(f"✅ Success! Found {result['total_categories']} categories")
            print(f"📊 Summary:")
            print(f"   - Aspect type: {result['aspect_type']}")
            print(f"   - Products analyzed: {len(result['selected_asins'])}")
            print(f"   - Categories found: {result['total_categories']}")
            
            if result['aspect_categories']:
                print(f"\n📋 Top Categories:")
                for i, category in enumerate(result['aspect_categories'][:3], 1):
                    print(f"   {i}. {category['category_name']}")
                    print(f"      - ID: {category['category_id']}")
                    print(f"      - Definition: {category['definition'][:80]}...")
            
            if result['product_aspect_data']:
                print(f"\n📊 Product Aspect Data:")
                for product_data in result['product_aspect_data'][:2]:
                    print(f"   - {product_data['asin']}: {len(product_data['aspect_data'])} categories")
                    for aspect in product_data['aspect_data'][:2]:
                        print(f"     • Category {aspect['category_pk']}: {aspect['mentions']} mentions, {aspect['reviews']} reviews")
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True


async def test_review_retrieval_api():
    """Test the review retrieval API."""
    print("\n" + "=" * 80)
    print("TESTING REVIEW RETRIEVAL API")
    print("=" * 80)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    # Get a category ID for testing
    print("🔍 Getting category IDs for testing...")
    try:
        service = CompetitorAnalysisChartService(
            project_id=project_id,
            selected_asins=["B00NG0ELL0"]
        )
        
        # Get some test data to find a valid category
        test_result = await service.get_matrix_view_data(
            "phy_perf", 
            {"max_categories": 1, "min_mentions": 1}
        )
        
        if not test_result['aspect_categories']:
            print("❌ No categories found for testing")
            return False
        
        category_id = test_result['aspect_categories'][0]['category_id']
        category_name = test_result['aspect_categories'][0]['category_name']
        print(f"✅ Using category: {category_name} (ID: {category_id})")
        
    except Exception as e:
        print(f"❌ Error getting category: {e}")
        return False
    
    # Test different sorting options
    test_cases = [
        {
            "name": "sorted by date (desc)",
            "sort_by": "date",
            "sort_order": "desc"
        },
        {
            "name": "sorted by rating (desc)",
            "sort_by": "rating",
            "sort_order": "desc"
        },
        {
            "name": "sorted by review_id (desc)",
            "sort_by": "review_id",
            "sort_order": "desc"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Get reviews for the category and product
            result = await service.get_reviews_by_category_product(
                category_id=category_id,
                product_id="B00NG0ELL0",
                limit=5,
                offset=0,
                sort_by=test_case['sort_by'],
                sort_order=test_case['sort_order']
            )
            
            # Print results
            print(f"✅ Success! Found {result['total_reviews']} total reviews")
            print(f"📄 Showing {len(result['reviews'])} reviews")
            print(f"📊 Pagination: limit={result['pagination']['limit']}, offset={result['pagination']['offset']}, has_more={result['pagination']['has_more']}")
            
            if result['category_info']:
                print(f"📋 Category Info:")
                print(f"   - Name: {result['category_info']['name']}")
                print(f"   - Definition: {result['category_info']['definition'][:80]}...")
                print(f"   - Aspect type: {result['category_info']['aspect_type']}")
            
            if result['reviews']:
                print(f"\n📝 Sample Reviews:")
                for i, review in enumerate(result['reviews'][:2], 1):
                    print(f"   {i}. Review ID: {review['review_id']}")
                    print(f"      - Title: {review.get('review_title', 'No title')}")
                    print(f"      - Rating: {review['rating']}")
                    print(f"      - Verified: {review.get('verified', 'Unknown')}")
                    print(f"      - Date: {review.get('review_date', 'Unknown')}")
                    print(f"      - Content: {review['review_text'][:100]}{'...' if len(review['review_text']) > 100 else ''}")
                    print(f"      - Aspects: {len(review['aspects'])} aspects")
                    for aspect in review['aspects'][:2]:
                        print(f"        • {aspect['aspect_description']} ({aspect['sentiment']})")
                    print()
        
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    return True


async def test_api_endpoints_directly():
    """Test API endpoints directly with FastAPI test client."""
    print("\n" + "=" * 80)
    print("TESTING API ENDPOINTS DIRECTLY")
    print("=" * 80)
    
    try:
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        
        project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
        test_asins = ["B00NG0ELL0", "B0BVKZLT3B"]
        
        # Test competitor summary endpoint
        print("🧪 Testing competitor summary endpoint...")
        response = client.post("/api/v1/dashboard/charts/competitor-analysis/summary", json={
            "project_id": project_id,
            "selected_asins": test_asins
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Status: {data['status']}")
            print(f"📊 Found {data['data']['total_products']} products")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
        
        # Test matrix view endpoint
        print("\n🧪 Testing matrix view endpoint...")
        response = client.post("/api/v1/dashboard/charts/competitor-analysis/matrix-view", json={
            "project_id": project_id,
            "selected_asins": test_asins,
            "aspect_type": "phy_perf",
            "options": {
                "sort_by": "mentions",
                "max_categories": 3
            }
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Status: {data['status']}")
            print(f"📊 Found {data['data']['total_categories']} categories")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
        
        # Test review retrieval endpoint
        print("\n🧪 Testing review retrieval endpoint...")
        response = client.post("/api/v1/dashboard/charts/competitor-analysis/reviews", json={
            "project_id": project_id,
            "category_id": 12515,  # Core Device Functionality
            "product_id": "B00NG0ELL0",
            "limit": 3,
            "offset": 0,
            "sort_by": "date",
            "sort_order": "desc"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Status: {data['status']}")
            print(f"📊 Found {data['data']['total_reviews']} reviews")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
        
        return True
        
    except ImportError:
        print("⚠️  FastAPI test client not available, skipping direct API tests")
        return True
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


async def main():
    """Run all tests."""
    print("🚀 Starting Competitor Analysis API Tests")
    print("📅 Project ID: d2c02b80-4c82-44cc-8093-56708a7883f7")
    
    # Run tests
    tests = [
        test_competitor_summary_api,
        test_matrix_view_api,
        test_review_retrieval_api,
        test_api_endpoints_directly
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)
    
    passed = sum(results)
    total = len(results)
    print(f"📊 Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed")


if __name__ == "__main__":
    asyncio.run(main()) 