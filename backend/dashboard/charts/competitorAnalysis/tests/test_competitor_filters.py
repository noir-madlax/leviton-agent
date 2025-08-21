#!/usr/bin/env python3
"""Test script for competitor analysis review filters."""

import asyncio
import logging
from typing import Dict, Any
from collections import Counter, defaultdict

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import the service
import sys
import os
# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))

from dashboard.charts.competitorAnalysis.service import CompetitorAnalysisChartService

def analyze_review_statistics(reviews: list) -> Dict[str, Any]:
    """Analyze review statistics for validation."""
    if not reviews:
        return {
            'total_reviews': 0,
            'rating_stats': {'high_ratings_4_5': 0, 'mid_ratings_3': 0, 'low_ratings_1_2': 0},
            'sentiment_stats': {'positive_count': 0, 'negative_count': 0, 'neutral_count': 0}
        }
    
    rating_stats = Counter()
    sentiment_stats = Counter()
    
    for review in reviews:
        # Analyze rating
        rating = review.get('rating')
        if rating is not None:
            if rating in [4, 5]:
                rating_stats['high_ratings_4_5'] += 1
            elif rating == 3:
                rating_stats['mid_ratings_3'] += 1
            elif rating in [1, 2]:
                rating_stats['low_ratings_1_2'] += 1
        
        # Analyze aspects for sentiment
        aspects = review.get('aspects', [])
        for aspect in aspects:
            sentiment = aspect.get('sentiment', '')
            if sentiment == '+':
                sentiment_stats['positive_count'] += 1
            elif sentiment == '-':
                sentiment_stats['negative_count'] += 1
            else:
                sentiment_stats['neutral_count'] += 1
    
    return {
        'total_reviews': len(reviews),
        'rating_stats': dict(rating_stats),
        'sentiment_stats': dict(sentiment_stats)
    }

async def test_competitor_review_filters():
    """Test the new sentiment and rating filters for competitor analysis reviews."""
    
    print("=" * 80)
    print("TESTING COMPETITOR ANALYSIS REVIEW FILTERS")
    print("=" * 80)
    
    # Test configuration
    PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    CATEGORY_ID = 12499  # Physical Installation Process
    PRODUCT_ID = "B0033PSGEQ"  # Example product ASIN
    
    try:
        # Create service instance
        service = CompetitorAnalysisChartService(
            project_id=PROJECT_ID,
            selected_asins=[PRODUCT_ID]
        )
        
        # First, get baseline data without filters
        print("\n📊 Getting baseline data (no filters)...")
        baseline_result = await service.get_reviews_by_category_product(
            category_id=CATEGORY_ID,
            product_id=PRODUCT_ID,
            limit=100,
            offset=0,
            sort_by="review_id",
            sort_order="desc"
        )
        
        baseline_reviews = baseline_result.get('reviews', [])
        baseline_stats = analyze_review_statistics(baseline_reviews)
        
        print(f"📈 Baseline Statistics:")
        print(f"   - Total reviews: {baseline_stats['total_reviews']}")
        print(f"   - Rating distribution: {baseline_stats['rating_stats']}")
        print(f"   - Sentiment distribution: {baseline_stats['sentiment_stats']}")
        
        # Test cases with assertions
        test_cases = [
            {
                "name": "No filters (all reviews)",
                "filters": {},
                "expected_count": baseline_stats['total_reviews'],
                "expected_rating_range": None,
                "expected_sentiment": None
            },
            {
                "name": "Positive sentiment only",
                "filters": {"sentiment_filter": "positive"},
                "expected_count": baseline_stats['sentiment_stats']['positive_count'],
                "expected_rating_range": None,
                "expected_sentiment": "positive"
            },
            {
                "name": "Negative sentiment only",
                "filters": {"sentiment_filter": "negative"},
                "expected_count": baseline_stats['sentiment_stats']['negative_count'],
                "expected_rating_range": None,
                "expected_sentiment": "negative"
            },
            {
                "name": "High rating only (4-5 stars)",
                "filters": {"rating_filter": "high"},
                "expected_count": baseline_stats['rating_stats']['high_ratings_4_5'],
                "expected_rating_range": (4, 5),
                "expected_sentiment": None
            },
            {
                "name": "Mid rating only (3 stars)",
                "filters": {"rating_filter": "mid"},
                "expected_count": baseline_stats['rating_stats']['mid_ratings_3'],
                "expected_rating_range": (3, 3),
                "expected_sentiment": None
            },
            {
                "name": "Low rating only (1-2 stars)",
                "filters": {"rating_filter": "low"},
                "expected_count": baseline_stats['rating_stats']['low_ratings_1_2'],
                "expected_rating_range": (1, 2),
                "expected_sentiment": None
            },
            {
                "name": "Positive sentiment + High rating",
                "filters": {"sentiment_filter": "positive", "rating_filter": "high"},
                "expected_count": min(baseline_stats['sentiment_stats']['positive_count'], 
                                    baseline_stats['rating_stats']['high_ratings_4_5']),
                "expected_rating_range": (4, 5),
                "expected_sentiment": "positive"
            },
            {
                "name": "Negative sentiment + Low rating",
                "filters": {"sentiment_filter": "negative", "rating_filter": "low"},
                "expected_count": min(baseline_stats['sentiment_stats']['negative_count'], 
                                    baseline_stats['rating_stats']['low_ratings_1_2']),
                "expected_rating_range": (1, 2),
                "expected_sentiment": "negative"
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            print(f"   Expected count: {test_case['expected_count']}")
            
            try:
                # Call the service with filters
                result = await service.get_reviews_by_category_product(
                    category_id=CATEGORY_ID,
                    product_id=PRODUCT_ID,
                    limit=100,
                    offset=0,
                    sort_by="review_id",
                    sort_order="desc",
                    sentiment_filter=test_case["filters"].get("sentiment_filter"),
                    rating_filter=test_case["filters"].get("rating_filter")
                )
                
                # Extract results
                total_reviews = result.get('total_reviews', 0)
                reviews = result.get('reviews', [])
                
                print(f"   ✅ Success: Found {total_reviews} total reviews, returned {len(reviews)} reviews")
                
                # ===== ASSERTIONS =====
                
                # 1. Basic response structure assertions
                assert isinstance(result, dict), f"Result should be a dictionary, got {type(result)}"
                assert 'reviews' in result, "Result should contain 'reviews' key"
                assert 'total_reviews' in result, "Result should contain 'total_reviews' key"
                assert 'project_id' in result, "Result should contain 'project_id' key"
                assert 'category_id' in result, "Result should contain 'category_id' key"
                assert 'product_id' in result, "Result should contain 'product_id' key"
                assert isinstance(reviews, list), f"Reviews should be a list, got {type(reviews)}"
                
                # 2. Count assertions
                if test_case['expected_count'] > 0:
                    assert len(reviews) <= test_case['expected_count'], \
                        f"Filtered reviews ({len(reviews)}) should not exceed expected count ({test_case['expected_count']})"
                
                # 3. Rating filter assertions
                if test_case['expected_rating_range']:
                    min_rating, max_rating = test_case['expected_rating_range']
                    for review in reviews:
                        rating = review.get('rating')
                        if rating is not None:
                            assert min_rating <= rating <= max_rating, \
                                f"Review rating {rating} should be between {min_rating} and {max_rating}"
                
                # 4. Sentiment filter assertions
                if test_case['expected_sentiment']:
                    expected_sentiment_symbol = '+' if test_case['expected_sentiment'] == 'positive' else '-'
                    for review in reviews:
                        aspects = review.get('aspects', [])
                        if aspects:  # Only check if review has aspects
                            aspect_sentiments = [aspect.get('sentiment') for aspect in aspects]
                            # At least one aspect should match the expected sentiment
                            assert expected_sentiment_symbol in aspect_sentiments, \
                                f"Review should have at least one {test_case['expected_sentiment']} aspect"
                
                # 5. Review structure assertions
                for review in reviews:
                    assert 'review_id' in review, "Review should have 'review_id'"
                    assert 'review_text' in review, "Review should have 'review_text'"
                    assert 'aspects' in review, "Review should have 'aspects'"
                    assert isinstance(review['aspects'], list), "Aspects should be a list"
                    
                    # Check aspect structure
                    for aspect in review['aspects']:
                        assert 'aspect_description' in aspect, "Aspect should have 'aspect_description'"
                        assert 'sentiment' in aspect, "Aspect should have 'sentiment'"
                        assert 'aspect_type' in aspect, "Aspect should have 'aspect_type'"
                
                print(f"   ✅ All assertions passed!")
                
                # Show sample review details if available
                if reviews:
                    sample_review = reviews[0]
                    print(f"   📝 Sample review:")
                    print(f"      - Review ID: {sample_review.get('review_id')}")
                    print(f"      - Rating: {sample_review.get('rating')}")
                    print(f"      - Aspects: {len(sample_review.get('aspects', []))}")
                    
                    # Show aspect sentiments
                    aspects = sample_review.get('aspects', [])
                    if aspects:
                        sentiments = [aspect.get('sentiment') for aspect in aspects]
                        print(f"      - Aspect sentiments: {sentiments}")
                else:
                    print(f"   📝 No reviews returned for this filter combination")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                logger.error(f"Test case failed: {e}", exc_info=True)
                raise  # Re-raise to fail the test
        
        print("\n" + "=" * 70)
        print("🎉 All competitor review filter tests passed!")
        
    except Exception as e:
        print(f"❌ Error in competitor filter testing: {e}")
        logger.error(f"Competitor filter test failed: {e}", exc_info=True)
        raise

async def test_api_endpoint():
    """Test the API endpoint directly."""
    
    import httpx
    import json
    
    print("\n🌐 Testing Competitor Analysis API Endpoint")
    print("=" * 50)
    
    # API configuration
    API_BASE_URL = "http://localhost:8000"
    ENDPOINT = "/api/v1/dashboard/charts/competitor-analysis/reviews"
    
    # Test request
    test_request = {
        "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
        "category_id": 12499,
        "product_id": "B0033PSGEQ",
        "limit": 5,
        "offset": 0,
        "sort_by": "review_id",
        "sort_order": "desc",
        "sentiment_filter": "positive",
        "rating_filter": "high",
        "filters": {},
        "selected_asins": None,
        "date_range": None
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{API_BASE_URL}{ENDPOINT}",
                json=test_request,
                headers={"Content-Type": "application/json"}
            )
            
            print(f"📡 API Response Status: {response.status_code}")
            
            # ===== API ASSERTIONS =====
            assert response.status_code == 200, f"API should return 200, got {response.status_code}"
            
            result = response.json()
            
            # Check response structure
            assert "status" in result, "API response should have 'status' field"
            assert "data" in result, "API response should have 'data' field"
            assert result["status"] == "success", f"API status should be 'success', got {result['status']}"
            
            data = result["data"]
            assert "reviews" in data, "API data should have 'reviews' field"
            assert "total_reviews" in data, "API data should have 'total_reviews' field"
            assert "project_id" in data, "API data should have 'project_id' field"
            assert "category_id" in data, "API data should have 'category_id' field"
            assert "product_id" in data, "API data should have 'product_id' field"
            
            # Check data types
            assert isinstance(data["reviews"], list), "Reviews should be a list"
            assert isinstance(data["total_reviews"], int), "Total reviews should be an integer"
            assert isinstance(data["project_id"], str), "Project ID should be a string"
            assert isinstance(data["category_id"], int), "Category ID should be an integer"
            assert isinstance(data["product_id"], str), "Product ID should be a string"
            
            print("✅ API call successful!")
            print(f"📊 Total reviews: {data.get('total_reviews', 0)}")
            print(f"📄 Reviews returned: {len(data.get('reviews', []))}")
            
            # Show response structure
            print("\n📋 Response structure:")
            print(json.dumps(result, indent=2)[:500] + "...")
            
    except Exception as e:
        print(f"❌ API test error: {str(e)}")
        logger.error(f"API test failed: {e}", exc_info=True)
        raise

def test_model_validation():
    """Test Pydantic model validation for the new filters."""
    
    print("\n🔍 Testing Model Validation")
    print("=" * 40)
    
    try:
        from dashboard.charts.competitorAnalysis.models import ReviewRetrievalRequest
        
        # Test valid filter values
        valid_request = ReviewRetrievalRequest(
            project_id="test-project",
            category_id=123,
            product_id="B123456789",
            sentiment_filter="positive",
            rating_filter="high"
        )
        assert valid_request.sentiment_filter == "positive"
        assert valid_request.rating_filter == "high"
        print("✅ Valid filter values accepted")
        
        # Test None values (should be allowed)
        none_request = ReviewRetrievalRequest(
            project_id="test-project",
            category_id=123,
            product_id="B123456789",
            sentiment_filter=None,
            rating_filter=None
        )
        assert none_request.sentiment_filter is None
        assert none_request.rating_filter is None
        print("✅ None values accepted")
        
        # Test invalid sentiment filter (should raise error)
        try:
            invalid_sentiment = ReviewRetrievalRequest(
                project_id="test-project",
                category_id=123,
                product_id="B123456789",
                sentiment_filter="invalid"
            )
            assert False, "Should have raised validation error for invalid sentiment"
        except Exception:
            print("✅ Invalid sentiment filter correctly rejected")
        
        # Test invalid rating filter (should raise error)
        try:
            invalid_rating = ReviewRetrievalRequest(
                project_id="test-project",
                category_id=123,
                product_id="B123456789",
                rating_filter="invalid"
            )
            assert False, "Should have raised validation error for invalid rating"
        except Exception:
            print("✅ Invalid rating filter correctly rejected")
        
        print("🎉 All model validation tests passed!")
        
    except Exception as e:
        print(f"❌ Model validation test error: {str(e)}")
        logger.error(f"Model validation test failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    print("🚀 Starting Competitor Review Filter Tests")
    print("Note: Make sure the backend server is running and you have valid project/category/product IDs")
    
    # Run tests
    asyncio.run(test_competitor_review_filters())
    asyncio.run(test_api_endpoint())
    test_model_validation() 