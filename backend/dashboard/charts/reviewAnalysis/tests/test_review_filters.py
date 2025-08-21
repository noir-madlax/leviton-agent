#!/usr/bin/env python3
"""Test script for Review Analysis Filters (Sentiment and Rating)."""

import asyncio
import json
import sys
import os
from typing import Dict, Any
from collections import defaultdict, Counter

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../../../../'))

from dashboard.charts.reviewAnalysis.service import ReviewAnalysisChartService
from dashboard.charts.reviewAnalysis.models import (
    ReviewsByCategoryRequest, ReviewsByCategoryResponse
)


def analyze_review_statistics(reviews: list) -> Dict[str, Any]:
    """Analyze review statistics for ratings and sentiments."""
    
    if not reviews:
        return {
            'total_reviews': 0,
            'rating_stats': {},
            'sentiment_stats': {},
            'combined_stats': {}
        }
    
    # Rating statistics
    ratings = [review.get('rating') for review in reviews if review.get('rating') is not None]
    rating_counter = Counter(ratings)
    
    # Sentiment statistics
    all_sentiments = []
    for review in reviews:
        aspects = review.get('aspects', [])
        for aspect in aspects:
            sentiment = aspect.get('sentiment')
            if sentiment:
                all_sentiments.append(sentiment)
    
    sentiment_counter = Counter(all_sentiments)
    
    # Combined statistics (rating + sentiment)
    combined_stats = defaultdict(lambda: defaultdict(int))
    for review in reviews:
        rating = review.get('rating')
        if rating is not None:
            aspects = review.get('aspects', [])
            for aspect in aspects:
                sentiment = aspect.get('sentiment')
                if sentiment:
                    combined_stats[rating][sentiment] += 1
    
    return {
        'total_reviews': len(reviews),
        'rating_stats': {
            'distribution': dict(rating_counter),
            'high_ratings_4_5': sum(1 for r in ratings if r >= 4),
            'mid_ratings_3': sum(1 for r in ratings if r == 3),
            'low_ratings_1_2': sum(1 for r in ratings if r <= 2),
            'avg_rating': sum(ratings) / len(ratings) if ratings else 0
        },
        'sentiment_stats': {
            'distribution': dict(sentiment_counter),
            'positive_count': sentiment_counter.get('+', 0),
            'negative_count': sentiment_counter.get('-', 0),
            'neutral_count': sentiment_counter.get('0', 0)
        },
        'combined_stats': dict(combined_stats)
    }


async def test_sentiment_and_rating_filters():
    """Test the new sentiment and rating filters."""
    print("=" * 80)
    print("TESTING SENTIMENT AND RATING FILTERS")
    print("=" * 80)
    
    project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
    
    # First, get some category IDs to test with
    print("🔍 Getting category IDs for testing...")
    
    try:
        service = ReviewAnalysisChartService(
            project_id=project_id,
            filters={}
        )
        
        # Get top categories to find category IDs
        categories_result = await service.get_top_categories({
            "aspect_type": "phy_perf",
            "sort_by": "mentions",
            "sort_direction": "desc",
            "max_categories": 5,
            "min_mentions": 1  # Lower threshold to get more categories
        })
        
        assert categories_result['categories'], "No categories found to test with"
        
        # Test with the first category
        test_category = categories_result['categories'][0]
        category_id = test_category['category_id']
        
        print(f"✅ Using category: {test_category['category_name']} (ID: {category_id})")
        
        # Get baseline statistics first
        print("\n📊 BASELINE STATISTICS (All Reviews)")
        print("-" * 50)
        
        baseline_result = await service.get_reviews_by_category(
            category_id=category_id,
            limit=1000,  # Get more reviews for better statistics
            offset=0,
            sort_by="review_id",
            sort_order="desc"
        )
        
        baseline_reviews = baseline_result.get('reviews', [])
        baseline_stats = analyze_review_statistics(baseline_reviews)
        
        # Assert baseline data exists
        assert baseline_stats['total_reviews'] > 0, "No baseline reviews found"
        assert baseline_result['total_reviews'] == baseline_stats['total_reviews'], "Review count mismatch"
        
        print(f"📈 Total Reviews: {baseline_stats['total_reviews']}")
        
        # Rating statistics
        rating_stats = baseline_stats['rating_stats']
        print(f"⭐ Rating Distribution:")
        print(f"   - High (4-5 stars): {rating_stats['high_ratings_4_5']}")
        print(f"   - Mid (3 stars): {rating_stats['mid_ratings_3']}")
        print(f"   - Low (1-2 stars): {rating_stats['low_ratings_1_2']}")
        print(f"   - Average Rating: {rating_stats['avg_rating']:.2f}")
        print(f"   - Detailed: {rating_stats['distribution']}")
        
        # Sentiment statistics
        sentiment_stats = baseline_stats['sentiment_stats']
        print(f"😊 Sentiment Distribution:")
        print(f"   - Positive (+): {sentiment_stats['positive_count']}")
        print(f"   - Negative (-): {sentiment_stats['negative_count']}")
        print(f"   - Neutral (0): {sentiment_stats['neutral_count']}")
        print(f"   - Detailed: {sentiment_stats['distribution']}")
        
        # Combined statistics
        print(f"🔗 Rating + Sentiment Combinations:")
        for rating, sentiments in baseline_stats['combined_stats'].items():
            print(f"   - Rating {rating}: {dict(sentiments)}")
        
        # Test filter combinations
        print("\n" + "=" * 70)
        print("🧪 FILTER TESTING")
        print("=" * 70)
        
        test_cases = [
            {
                "name": "No filters (all reviews)",
                "filters": {},
                "expected_total": baseline_stats['total_reviews'],
                "expected_high_ratings": rating_stats['high_ratings_4_5'],
                "expected_positive_sentiments": sentiment_stats['positive_count']
            },
            {
                "name": "Negative sentiment only",
                "filters": {"sentiment_filter": "negative"},
                "expected_min_negative": 0,  # May be 0 if no negative aspects in this category
                "expected_all_negative": True
            },
            {
                "name": "Mid rating only (3 stars)",
                "filters": {"rating_filter": "mid"},
                "expected_rating": 3,
                "expected_count": rating_stats['mid_ratings_3']
            },
            {
                "name": "Positive sentiment + High rating",
                "filters": {"sentiment_filter": "positive", "rating_filter": "high"},
                "expected_rating_range": (4, 5),
                "expected_all_positive": True
            },
            {
                "name": "Negative sentiment + Low rating",
                "filters": {"sentiment_filter": "negative", "rating_filter": "low"},
                "expected_rating_range": (1, 2),
                "expected_all_negative": True
            }
        ]
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"\n{i}. {test_case['name']}")
            
            try:
                # Call the service with filters
                result = await service.get_reviews_by_category(
                    category_id=category_id,
                    limit=1000,  # Get more reviews for better statistics
                    offset=0,
                    sort_by="review_id",
                    sort_order="desc",
                    sentiment_filter=test_case["filters"].get("sentiment_filter"),
                    rating_filter=test_case["filters"].get("rating_filter")
                )
                
                # Analyze results
                total_reviews = result.get('total_reviews', 0)
                reviews = result.get('reviews', [])
                
                print(f"   ✅ Success: Found {total_reviews} total reviews, returned {len(reviews)} reviews")
                
                # Assert basic response structure
                assert isinstance(result, dict), "Result should be a dictionary"
                assert 'total_reviews' in result, "Result should contain total_reviews"
                assert 'reviews' in result, "Result should contain reviews"
                assert 'pagination' in result, "Result should contain pagination"
                assert total_reviews == len(reviews), "Total reviews should match returned reviews count"
                
                # Show filtered statistics
                if reviews:
                    filtered_stats = analyze_review_statistics(reviews)
                    
                    print(f"   📊 Filtered Statistics:")
                    
                    # Rating statistics for filtered results
                    rating_stats = filtered_stats['rating_stats']
                    print(f"      ⭐ Ratings: High={rating_stats['high_ratings_4_5']}, Mid={rating_stats['mid_ratings_3']}, Low={rating_stats['low_ratings_1_2']}")
                    print(f"      📊 Rating Distribution: {rating_stats['distribution']}")
                    
                    # Sentiment statistics for filtered results
                    sentiment_stats = filtered_stats['sentiment_stats']
                    print(f"      😊 Sentiments: +={sentiment_stats['positive_count']}, -={sentiment_stats['negative_count']}, 0={sentiment_stats['neutral_count']}")
                    print(f"      📊 Sentiment Distribution: {sentiment_stats['distribution']}")
                    
                    # Assert specific test case expectations
                    if "expected_total" in test_case:
                        assert total_reviews == test_case["expected_total"], f"Expected {test_case['expected_total']} reviews, got {total_reviews}"
                    
                    if "expected_count" in test_case:
                        assert total_reviews == test_case["expected_count"], f"Expected {test_case['expected_count']} reviews, got {total_reviews}"
                    
                    if "expected_rating_range" in test_case:
                        min_rating, max_rating = test_case["expected_rating_range"]
                        for review in reviews:
                            assert min_rating <= review.get('rating', 0) <= max_rating, f"Rating {review.get('rating')} not in range {min_rating}-{max_rating}"
                    
                    if "expected_rating" in test_case:
                        for review in reviews:
                            assert review.get('rating') == test_case["expected_rating"], f"Expected rating {test_case['expected_rating']}, got {review.get('rating')}"
                    
                    if "expected_all_positive" in test_case and test_case["expected_all_positive"]:
                        for review in reviews:
                            aspects = review.get('aspects', [])
                            for aspect in aspects:
                                assert aspect.get('sentiment') == '+', f"Expected positive sentiment, got {aspect.get('sentiment')}"
                    
                    if "expected_all_negative" in test_case and test_case["expected_all_negative"]:
                        for review in reviews:
                            aspects = review.get('aspects', [])
                            for aspect in aspects:
                                assert aspect.get('sentiment') == '-', f"Expected negative sentiment, got {aspect.get('sentiment')}"
                    
                    if "expected_min_positive" in test_case:
                        positive_count = sentiment_stats['positive_count']
                        assert positive_count >= test_case["expected_min_positive"], f"Expected at least {test_case['expected_min_positive']} positive sentiments, got {positive_count}"
                    
                    if "expected_min_negative" in test_case:
                        negative_count = sentiment_stats['negative_count']
                        assert negative_count >= test_case["expected_min_negative"], f"Expected at least {test_case['expected_min_negative']} negative sentiments, got {negative_count}"
                    
                    # Show sample review details
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
                        
                        # Assert aspect structure
                        for aspect in aspects:
                            assert 'aspect_description' in aspect, "Aspect should have description"
                            assert 'sentiment' in aspect, "Aspect should have sentiment"
                            assert aspect['sentiment'] in ['+', '-', '0'], f"Invalid sentiment: {aspect['sentiment']}"
                    
                    print(f"   ✅ All assertions passed for {test_case['name']}")
                else:
                    print(f"   📝 No reviews returned for this filter combination")
                    # Assert that if no reviews returned, it's expected for some test cases
                    if "expected_count" in test_case and test_case["expected_count"] == 0:
                        print(f"   ✅ Expected no reviews for {test_case['name']}")
                
            except Exception as e:
                print(f"   ❌ Error: {str(e)}")
                import traceback
                traceback.print_exc()
                raise  # Re-raise to fail the test
        
        print("\n" + "=" * 70)
        print("🎉 Filter testing completed!")
        
    except Exception as e:
        print(f"❌ Error in filter testing: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to fail the test


async def test_filter_models():
    """Test the filter models and validation."""
    print("\n" + "=" * 80)
    print("TESTING FILTER MODELS")
    print("=" * 80)
    
    try:
        # Test valid filter combinations
        valid_test_cases = [
            {
                "name": "No filters",
                "data": {
                    "project_id": "test-project",
                    "category_id": 1,
                    "limit": 10,
                    "offset": 0,
                    "sort_by": "review_id",
                    "sort_order": "desc"
                }
            },
            {
                "name": "Sentiment filter only",
                "data": {
                    "project_id": "test-project",
                    "category_id": 1,
                    "limit": 10,
                    "offset": 0,
                    "sort_by": "review_id",
                    "sort_order": "desc",
                    "sentiment_filter": "positive"
                }
            },
            {
                "name": "Rating filter only",
                "data": {
                    "project_id": "test-project",
                    "category_id": 1,
                    "limit": 10,
                    "offset": 0,
                    "sort_by": "review_id",
                    "sort_order": "desc",
                    "rating_filter": "high"
                }
            },
            {
                "name": "Both filters",
                "data": {
                    "project_id": "test-project",
                    "category_id": 1,
                    "limit": 10,
                    "offset": 0,
                    "sort_by": "review_id",
                    "sort_order": "desc",
                    "sentiment_filter": "negative",
                    "rating_filter": "low"
                }
            }
        ]
        
        for test_case in valid_test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print("-" * 60)
            
            try:
                # Create request model
                request = ReviewsByCategoryRequest(**test_case['data'])
                
                # Assert model properties
                assert request.category_id == test_case['data']['category_id'], "Category ID should match"
                assert request.limit == test_case['data']['limit'], "Limit should match"
                assert request.sort_by == test_case['data']['sort_by'], "Sort by should match"
                assert request.sort_order == test_case['data']['sort_order'], "Sort order should match"
                
                # Assert optional filters
                if 'sentiment_filter' in test_case['data']:
                    assert request.sentiment_filter == test_case['data']['sentiment_filter'], "Sentiment filter should match"
                else:
                    assert request.sentiment_filter is None, "Sentiment filter should be None when not provided"
                
                if 'rating_filter' in test_case['data']:
                    assert request.rating_filter == test_case['data']['rating_filter'], "Rating filter should match"
                else:
                    assert request.rating_filter is None, "Rating filter should be None when not provided"
                
                print(f"✅ Success! Model created with:")
                print(f"   - Category ID: {request.category_id}")
                print(f"   - Sentiment Filter: {request.sentiment_filter}")
                print(f"   - Rating Filter: {request.rating_filter}")
                print(f"   - Limit: {request.limit}")
                print(f"   - Sort By: {request.sort_by}")
                print(f"   - Sort Order: {request.sort_order}")
                
            except Exception as e:
                print(f"❌ Error: {e}")
                raise  # Re-raise to fail the test
        
        # Test invalid filter values
        print(f"\n🧪 Testing Invalid Filter Values")
        print("-" * 60)
        
        invalid_test_cases = [
            {
                "name": "Invalid sentiment filter",
                "data": {
                    "project_id": "test-project",
                    "category_id": 1,
                    "sentiment_filter": "invalid_sentiment"
                },
                "expected_error": "Input should be 'positive' or 'negative'"
            },
            {
                "name": "Invalid rating filter",
                "data": {
                    "project_id": "test-project",
                    "category_id": 1,
                    "rating_filter": "invalid_rating"
                },
                "expected_error": "Input should be 'high', 'mid' or 'low'"
            }
        ]
        
        for test_case in invalid_test_cases:
            print(f"\n🧪 Testing: {test_case['name']}")
            print("-" * 60)
            
            try:
                # This should raise a validation error
                request = ReviewsByCategoryRequest(**test_case['data'])
                assert False, f"Expected validation error but model was created successfully"
                
            except Exception as e:
                error_message = str(e)
                assert test_case['expected_error'] in error_message, f"Expected error containing '{test_case['expected_error']}', got: {error_message}"
                print(f"✅ Expected validation error: {e}")
        
    except Exception as e:
        print(f"❌ Error in model testing: {e}")
        import traceback
        traceback.print_exc()
        raise  # Re-raise to fail the test


async def main():
    """Run all tests."""
    print("🚀 Starting Review Filter Tests")
    print("Note: Make sure you have valid project/category IDs")
    
    try:
        # Run tests
        await test_sentiment_and_rating_filters()
        await test_filter_models()
        
        print("\n" + "=" * 80)
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main()) 