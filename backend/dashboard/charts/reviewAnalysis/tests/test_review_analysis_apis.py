#!/usr/bin/env python3
"""Test script for Review Analysis APIs."""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))

from dashboard.charts.reviewAnalysis.service import ReviewAnalysisChartService
from dashboard.charts.reviewAnalysis.models import (
    TopCategoriesRequest, TopCategoriesResponse,
    ReviewsByCategoryRequest, ReviewsByCategoryResponse
)


async def test_top_categories_api():
    """Test the top categories API."""
    print("=" * 80)
    print("TESTING TOP CATEGORIES API")
    print("=" * 80)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    # Test different aspect types and sorting options
    test_cases = [
        {
            "name": "phy_perf - sorted by mentions",
            "additional_conditions": {
                "aspect_type": "phy_perf",
                "sort_by": "mentions",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_mentions": 3
            }
        },
        {
            "name": "phy_perf - sorted by positive mentions",
            "additional_conditions": {
                "aspect_type": "phy_perf",
                "sort_by": "positive_mentions",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_mentions": 3
            }
        },
        {
            "name": "phy_perf - sorted by negative mentions",
            "additional_conditions": {
                "aspect_type": "phy_perf",
                "sort_by": "negative_mentions",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_mentions": 3
            }
        },
        {
            "name": "use - sorted by positive ratio",
            "additional_conditions": {
                "aspect_type": "use",
                "sort_by": "positive_ratio",
                "sort_direction": "desc",
                "max_categories": 5,
                "min_mentions": 3
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 60)
        
        try:
            # Create service
            service = ReviewAnalysisChartService(project_id=project_id)
            
            # Get top categories
            result = await service.get_top_categories(test_case['additional_conditions'])
            
            # Print results
            print(f"✅ Success! Found {result['total_categories']} categories")
            print(f"📊 Summary Stats:")
            print(f"   - Total mentions: {result['summary_stats']['total_mentions']}")
            print(f"   - Total reviews: {result['summary_stats']['total_reviews']}")
            print(f"   - Positive mentions: {result['summary_stats']['total_positive_mentions']}")
            print(f"   - Negative mentions: {result['summary_stats']['total_negative_mentions']}")
            print(f"   - Overall positive ratio: {result['summary_stats']['overall_positive_ratio']:.3f}")
            
            if result['categories']:
                print(f"\n📋 Top Categories:")
                for i, category in enumerate(result['categories'][:3], 1):
                    print(f"   {i}. {category['category_name']}")
                    print(f"      - Mentions: {category['total_mentions']} (Positive: {category['positive_mentions']}, Negative: {category['negative_mentions']})")
                    print(f"      - Reviews: {category['unique_reviews']}")
                    print(f"      - Positive ratio: {category['positive_ratio']:.3f}")
                    print(f"      - Aspect type: {category['aspect_type']}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()


async def test_reviews_by_category_api():
    """Test the reviews by category API."""
    print("\n" + "=" * 80)
    print("TESTING REVIEWS BY CATEGORY API")
    print("=" * 80)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    # First, get some category IDs to test with
    print("🔍 Getting category IDs for testing...")
    
    try:
        service = ReviewAnalysisChartService(project_id=project_id)
        
        # Get top categories to find category IDs
        categories_result = await service.get_top_categories({
            "aspect_type": "phy_perf",
            "sort_by": "mentions",
            "sort_direction": "desc",
            "max_categories": 3,
            "min_mentions": 3
        })
        
        if not categories_result['categories']:
            print("❌ No categories found to test with")
            return
        
        # Test with the first category
        test_category = categories_result['categories'][0]
        category_id = test_category['category_id']
        
        print(f"✅ Using category: {test_category['category_name']} (ID: {category_id})")
        
        # Test different sorting options
        test_cases = [
            {
                "name": "sorted by date (desc)",
                "sort_by": "date",
                "sort_order": "desc",
                "limit": 5
            },
            {
                "name": "sorted by rating (desc)",
                "sort_by": "rating",
                "sort_order": "desc",
                "limit": 5
            },
            {
                "name": "sorted by review_id (desc)",
                "sort_by": "review_id",
                "sort_order": "desc",
                "limit": 5
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print("-" * 60)
            
            try:
                # Get reviews by category
                result = await service.get_reviews_by_category(
                    category_id=category_id,
                    limit=test_case['limit'],
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
                    print(f"   - Definition: {result['category_info']['definition'][:100]}...")
                    print(f"   - Aspect type: {result['category_info']['aspect_type']}")
                
                if result['reviews']:
                    print(f"\n📝 Sample Reviews:")
                    for i, review in enumerate(result['reviews'][:2], 1):
                        print(f"   {i}. Review ID: {review['review_id']}")
                        print(f"      - Product: {review['product_title'][:50]}...")
                        print(f"      - Product ID: {review['product_id']}")
                        print(f"      - Title: {review.get('review_title', 'No title')}")
                        print(f"      - Rating: {review['rating']}")
                        print(f"      - Verified: {review.get('verified', 'Unknown')}")
                        print(f"      - Date: {review.get('review_date', 'Unknown')}")
                        print(f"      - Content: {review['review_text'][:100]}{'...' if len(review['review_text']) > 100 else ''}")
                        print(f"      - Aspects: {len(review['aspects'])} aspects")
                        for aspect in review['aspects'][:2]:  # Show first 2 aspects
                            print(f"        • {aspect['aspect_description']} ({aspect['sentiment']})")
                        print()
                
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                
    except Exception as e:
        print(f"❌ Error getting categories: {e}")
        import traceback
        traceback.print_exc()


async def test_api_endpoints_directly():
    """Test the API endpoints directly using FastAPI test client."""
    print("\n" + "=" * 80)
    print("TESTING API ENDPOINTS DIRECTLY")
    print("=" * 80)
    
    try:
        from fastapi.testclient import TestClient
        from main import app  # Assuming your FastAPI app is in main.py (backend directory)
        
        client = TestClient(app)
        project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
        
        # Test top categories endpoint
        print("🧪 Testing /api/v1/dashboard/charts/review-analysis/top-categories")
        print("-" * 60)
        
        top_categories_request = {
            "project_id": project_id,
            "filters": {},
            "date_range": None,
            "additional_conditions": {
                "aspect_type": "phy_perf",
                "sort_by": "mentions",
                "sort_direction": "desc",
                "max_categories": 3,
                "min_mentions": 3
            }
        }
        
        response = client.post(
            "/api/v1/dashboard/charts/review-analysis/top-categories",
            json=top_categories_request
        )
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Success! Found {data['data']['total_categories']} categories")
            print(f"📊 Summary: {data['data']['summary_stats']['total_mentions']} total mentions")
            
            # Use first category for reviews test
            if data['data']['categories']:
                category_id = data['data']['categories'][0]['category_id']
                
                # Test reviews endpoint
                print(f"\n🧪 Testing /api/v1/dashboard/charts/review-analysis/reviews-by-category")
                print("-" * 60)
                
                reviews_request = {
                    "project_id": project_id,
                    "filters": {},
                    "date_range": None,
                    "category_id": category_id,
                    "limit": 3,
                    "offset": 0,
                    "sort_by": "date",
                    "sort_order": "desc"
                }
                
                reviews_response = client.post(
                    "/api/v1/dashboard/charts/review-analysis/reviews-by-category",
                    json=reviews_request
                )
                
                print(f"Status Code: {reviews_response.status_code}")
                if reviews_response.status_code == 200:
                    reviews_data = reviews_response.json()
                    print(f"✅ Success! Found {reviews_data['data']['total_reviews']} total reviews")
                    print(f"📄 Showing {len(reviews_data['data']['reviews'])} reviews")
                    
                    if reviews_data['data']['reviews']:
                        review = reviews_data['data']['reviews'][0]
                        print(f"📝 Sample Review:")
                        print(f"   - Review ID: {review['review_id']}")
                        print(f"   - Product: {review['product_title'][:50]}...")
                        print(f"   - Product ID: {review['product_id']}")
                        print(f"   - Aspects: {len(review['aspects'])} aspects")
                else:
                    print(f"❌ Reviews API Error: {reviews_response.text}")
        else:
            print(f"❌ Top Categories API Error: {response.text}")
            
    except ImportError:
        print("⚠️  FastAPI test client not available, skipping direct API tests")
    except Exception as e:
        print(f"❌ Error in direct API tests: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Main test function."""
    print("🚀 Starting Review Analysis API Tests")
    print(f"📅 Project ID: d2c02b80-4c82-44cc-8093-56708a7883f7")
    
    # Test service methods directly
    await test_top_categories_api()
    await test_reviews_by_category_api()
    
    # Test API endpoints directly
    await test_api_endpoints_directly()
    
    print("\n" + "=" * 80)
    print("✅ ALL TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main()) 