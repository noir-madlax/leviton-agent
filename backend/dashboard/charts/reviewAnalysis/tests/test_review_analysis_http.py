#!/usr/bin/env python3
"""HTTP test script for Review Analysis APIs."""

import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"  # Adjust if your server runs on different port
PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"

def test_top_categories_api():
    """Test the top categories API via HTTP."""
    print("=" * 80)
    print("TESTING TOP CATEGORIES API VIA HTTP")
    print("=" * 80)
    
    url = f"{BASE_URL}/api/v1/dashboard/charts/review-analysis/top-categories"
    
    # Test different scenarios
    test_cases = [
        {
            "name": "phy_perf - sorted by mentions",
            "data": {
                "project_id": PROJECT_ID,
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
        },
        {
            "name": "phy_perf - sorted by positive mentions",
            "data": {
                "project_id": PROJECT_ID,
                "filters": {},
                "date_range": None,
                "additional_conditions": {
                    "aspect_type": "phy_perf",
                    "sort_by": "positive_mentions",
                    "sort_direction": "desc",
                    "max_categories": 3,
                    "min_mentions": 3
                }
            }
        },
        {
            "name": "use - sorted by positive ratio",
            "data": {
                "project_id": PROJECT_ID,
                "filters": {},
                "date_range": None,
                "additional_conditions": {
                    "aspect_type": "use",
                    "sort_by": "positive_ratio",
                    "sort_direction": "desc",
                    "max_categories": 3,
                    "min_mentions": 3
                }
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🧪 Testing: {test_case['name']}")
        print("-" * 60)
        
        try:
            response = requests.post(url, json=test_case['data'], timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Success!")
                print(f"📊 Found {data['data']['total_categories']} categories")
                print(f"📈 Summary: {data['data']['summary_stats']['total_mentions']} total mentions")
                
                if data['data']['categories']:
                    print(f"\n📋 Top Categories:")
                    for i, category in enumerate(data['data']['categories'][:3], 1):
                        print(f"   {i}. {category['category_name']}")
                        print(f"      - Mentions: {category['total_mentions']} (Positive: {category['positive_mentions']}, Negative: {category['negative_mentions']})")
                        print(f"      - Reviews: {category['unique_reviews']}")
                        print(f"      - Positive ratio: {category['positive_ratio']:.3f}")
                        print(f"      - Aspect type: {category['aspect_type']}")
            else:
                print(f"❌ Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")


def test_reviews_by_category_api():
    """Test the reviews by category API via HTTP."""
    print("\n" + "=" * 80)
    print("TESTING REVIEWS BY CATEGORY API VIA HTTP")
    print("=" * 80)
    
    # First get a category ID to test with
    print("🔍 Getting category ID for testing...")
    
    try:
        # Get top categories first
        top_categories_url = f"{BASE_URL}/api/v1/dashboard/charts/review-analysis/top-categories"
        top_categories_data = {
            "project_id": PROJECT_ID,
            "filters": {},
            "date_range": None,
            "additional_conditions": {
                "aspect_type": "phy_perf",
                "sort_by": "mentions",
                "sort_direction": "desc",
                "max_categories": 1,
                "min_mentions": 3
            }
        }
        
        response = requests.post(top_categories_url, json=top_categories_data, timeout=30)
        
        if response.status_code != 200:
            print(f"❌ Error getting categories: {response.text}")
            return
        
        data = response.json()
        if not data['data']['categories']:
            print("❌ No categories found to test with")
            return
        
        category_id = data['data']['categories'][0]['category_id']
        category_name = data['data']['categories'][0]['category_name']
        
        print(f"✅ Using category: {category_name} (ID: {category_id})")
        
        # Test reviews endpoint
        reviews_url = f"{BASE_URL}/api/v1/dashboard/charts/review-analysis/reviews-by-category"
        
        test_cases = [
            {
                "name": "sorted by date (desc)",
                "data": {
                    "project_id": PROJECT_ID,
                    "filters": {},
                    "date_range": None,
                    "category_id": category_id,
                    "limit": 3,
                    "offset": 0,
                    "sort_by": "date",
                    "sort_order": "desc"
                }
            },
            {
                "name": "sorted by rating (desc)",
                "data": {
                    "project_id": PROJECT_ID,
                    "filters": {},
                    "date_range": None,
                    "category_id": category_id,
                    "limit": 3,
                    "offset": 0,
                    "sort_by": "rating",
                    "sort_order": "desc"
                }
            }
        ]
        
        for test_case in test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print("-" * 60)
            
            try:
                response = requests.post(reviews_url, json=test_case['data'], timeout=30)
                
                print(f"Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success!")
                    print(f"📄 Found {data['data']['total_reviews']} total reviews")
                    print(f"📊 Showing {len(data['data']['reviews'])} reviews")
                    print(f"📋 Pagination: limit={data['data']['pagination']['limit']}, offset={data['data']['pagination']['offset']}, has_more={data['data']['pagination']['has_more']}")
                    
                    if data['data']['category_info']:
                        print(f"📋 Category Info:")
                        print(f"   - Name: {data['data']['category_info']['category_name']}")
                        print(f"   - Definition: {data['data']['category_info']['definition'][:100]}...")
                        print(f"   - Aspect type: {data['data']['category_info']['aspect_type']}")
                    
                    if data['data']['reviews']:
                        print(f"\n📝 Sample Reviews:")
                        for i, review in enumerate(data['data']['reviews'][:2], 1):
                            print(f"   {i}. Review ID: {review['review_id']}")
                            print(f"      - Product: {review['product_title'][:50]}...")
                            print(f"      - Product ID: {review['product_id']}")
                            print(f"      - Rating: {review['rating']}")
                            print(f"      - Aspects: {len(review['aspects'])} aspects")
                            for aspect in review['aspects'][:2]:  # Show first 2 aspects
                                print(f"        • {aspect['aspect_description']} ({aspect['sentiment']})")
                            print()
                else:
                    print(f"❌ Error: {response.text}")
                    
            except requests.exceptions.RequestException as e:
                print(f"❌ Request Error: {e}")
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Main test function."""
    print("🚀 Starting Review Analysis HTTP API Tests")
    print(f"📅 Project ID: {PROJECT_ID}")
    print(f"🌐 Base URL: {BASE_URL}")
    
    # Test top categories API
    test_top_categories_api()
    
    # Test reviews by category API
    test_reviews_by_category_api()
    
    print("\n" + "=" * 80)
    print("✅ ALL HTTP TESTS COMPLETED")
    print("=" * 80)


if __name__ == "__main__":
    main() 