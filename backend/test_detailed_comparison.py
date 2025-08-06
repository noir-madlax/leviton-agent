#!/usr/bin/env python3
"""Detailed comparison to understand the exact difference between tooltip and clicked view."""

import asyncio
import logging
from collections import defaultdict

from dashboard.charts.reviewCore.data_service import ReviewDataService
from core.database.connection import get_supabase_client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test parameters
PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"
CATEGORY_ID = 12515

async def test_detailed_comparison():
    """Detailed comparison to understand the exact difference."""
    
    supabase = get_supabase_client()
    data_service = ReviewDataService(supabase)
    
    try:
        # Get project ASINs
        project_result = supabase.table('projects').select('selected_product_asins').eq('id', PROJECT_ID).execute()
        project_asins = project_result.data[0]['selected_product_asins']
        
        logger.info(f"🔍 Detailed comparison for category {CATEGORY_ID}")
        
        # Get raw data to understand the base counts
        query = supabase.table('review_aspect_data_view').select(
            'category_pk, category_name, category_definition, aspect_type, sentiment, review_id, product_id'
        ).eq('project_id', PROJECT_ID).eq('category_pk', CATEGORY_ID).in_('product_id', project_asins).in_('aspect_type', ['phy', 'perf'])
        
        result = query.execute()
        logger.info(f"📊 Raw data: {len(result.data)} records")
        
        # Check what aspect types are actually in the data
        aspect_types_in_data = set()
        for record in result.data:
            aspect_types_in_data.add(record['aspect_type'])
        logger.info(f"📊 Aspect types in data: {aspect_types_in_data}")
        
        # Get ALL data for this category (without aspect type filter)
        all_data_query = supabase.table('review_aspect_data_view').select(
            'category_pk, category_name, category_definition, aspect_type, sentiment, review_id, product_id'
        ).eq('project_id', PROJECT_ID).eq('category_pk', CATEGORY_ID).in_('product_id', project_asins)
        
        all_data_result = all_data_query.execute()
        logger.info(f"📊 All data (no aspect filter): {len(all_data_result.data)} records")
        
        all_aspect_types = set()
        for record in all_data_result.data:
            all_aspect_types.add(record['aspect_type'])
        logger.info(f"📊 All aspect types in data: {all_aspect_types}")
        
        # Analyze the raw data
        review_sentiments = defaultdict(set)
        for record in result.data:
            review_key = (record['product_id'], record['review_id'])
            sentiment = record['sentiment']
            review_sentiments[review_key].add(sentiment)
        
        logger.info(f"📊 Unique reviews: {len(review_sentiments)}")
        
        # Categorize reviews by their sentiment patterns
        positive_only = set()
        negative_only = set()
        mixed_sentiment = set()
        neutral_only = set()
        
        for review_key, sentiments in review_sentiments.items():
            if '+' in sentiments and '-' in sentiments:
                mixed_sentiment.add(review_key)
            elif '+' in sentiments:
                positive_only.add(review_key)
            elif '-' in sentiments:
                negative_only.add(review_key)
            else:
                neutral_only.add(review_key)
        
        logger.info("📊 Review categorization:")
        logger.info(f"   - Positive only: {len(positive_only)}")
        logger.info(f"   - Negative only: {len(negative_only)}")
        logger.info(f"   - Mixed sentiment: {len(mixed_sentiment)}")
        logger.info(f"   - Neutral only: {len(neutral_only)}")
        logger.info(f"   - Total: {len(positive_only) + len(negative_only) + len(mixed_sentiment) + len(neutral_only)}")
        
        # 🔍 NEW: Detailed analysis of what the tooltip is actually doing
        logger.info("\n🔍 NEW: Detailed tooltip analysis")
        
        # Simulate the exact tooltip logic step by step
        tooltip_reviews = set()
        tooltip_positive = set()
        tooltip_negative = set()
        tooltip_neutral = set()
        
        for record in result.data:
            review_key = (record['product_id'], record['review_id'])
            sentiment = record['sentiment']
            
            # Add to all_reviews (this is what gets counted as total_reviews)
            tooltip_reviews.add(review_key)
            
            # Add to sentiment-specific sets
            if sentiment == '+':
                tooltip_positive.add(review_key)
            elif sentiment == '-':
                tooltip_negative.add(review_key)
            else:
                tooltip_neutral.add(review_key)
        
        logger.info("📊 Tooltip simulation results:")
        logger.info(f"   - All reviews (total_reviews): {len(tooltip_reviews)}")
        logger.info(f"   - Positive reviews: {len(tooltip_positive)}")
        logger.info(f"   - Negative reviews: {len(tooltip_negative)}")
        logger.info(f"   - Neutral reviews: {len(tooltip_neutral)}")
        
        # Check for any reviews that might be filtered out
        all_review_keys = set()
        for record in result.data:
            review_key = (record['product_id'], record['review_id'])
            all_review_keys.add(review_key)
        
        logger.info(f"📊 All review keys from raw data: {len(all_review_keys)}")
        logger.info(f"📊 Tooltip review keys: {len(tooltip_reviews)}")
        
        if len(all_review_keys) != len(tooltip_reviews):
            missing_reviews = all_review_keys - tooltip_reviews
            logger.warning(f"⚠️  Missing reviews in tooltip: {len(missing_reviews)}")
            logger.info(f"   - Missing review keys: {list(missing_reviews)[:5]}...")  # Show first 5
        
        # 🔍 NEW: Direct examination of the actual method
        logger.info("\n🔍 NEW: Direct examination of actual get_category_statistics")
        
        # Get the raw data that the actual method processes
        actual_query = supabase.table('review_aspect_data_view').select(
            'category_pk, category_name, category_definition, aspect_type, sentiment, review_id, product_id'
        ).eq('project_id', PROJECT_ID).in_('product_id', project_asins).in_('aspect_type', ['phy', 'perf'])
        
        actual_result = actual_query.execute()
        logger.info(f"📊 Actual method raw data: {len(actual_result.data)} records")
        
        # Process this data exactly like the actual method does
        actual_category_metrics = {}
        for item in actual_result.data:
            category_pk = item['category_pk']
            if category_pk not in actual_category_metrics:
                actual_category_metrics[category_pk] = {
                    'category_pk': category_pk,
                    'category_name': item['category_name'],
                    'definition': item['category_definition'],
                    'aspect_type': item['aspect_type'],
                    'total_mentions': 0,
                    'positive_mentions': 0,
                    'negative_mentions': 0,
                    'neutral_mentions': 0,
                    'positive_reviews': set(),
                    'negative_reviews': set(),
                    'neutral_reviews': set(),
                    'all_reviews': set()
                }
            
            actual_category_metrics[category_pk]['total_mentions'] += 1
            review_key = (item.get('product_id', 'unknown'), item['review_id'])
            actual_category_metrics[category_pk]['all_reviews'].add(review_key)
            
            sentiment = item['sentiment']
            if sentiment == '+':
                actual_category_metrics[category_pk]['positive_mentions'] += 1
                actual_category_metrics[category_pk]['positive_reviews'].add(review_key)
            elif sentiment == '-':
                actual_category_metrics[category_pk]['negative_mentions'] += 1
                actual_category_metrics[category_pk]['negative_reviews'].add(review_key)
            else:
                actual_category_metrics[category_pk]['neutral_mentions'] += 1
                actual_category_metrics[category_pk]['neutral_reviews'].add(review_key)
        
        # Check our specific category
        if CATEGORY_ID in actual_category_metrics:
            cat_data = actual_category_metrics[CATEGORY_ID]
            logger.info(f"📊 Actual method results for category {CATEGORY_ID}:")
            logger.info(f"   - Raw positive_reviews set: {len(cat_data['positive_reviews'])}")
            logger.info(f"   - Raw negative_reviews set: {len(cat_data['negative_reviews'])}")
            logger.info(f"   - Raw neutral_reviews set: {len(cat_data['neutral_reviews'])}")
            logger.info(f"   - Raw all_reviews set: {len(cat_data['all_reviews'])}")
            
            # Check if there are any reviews that are missing
            missing_from_actual = tooltip_reviews - cat_data['all_reviews']
            extra_in_actual = cat_data['all_reviews'] - tooltip_reviews
            
            if missing_from_actual:
                logger.warning(f"⚠️  Reviews missing from actual method: {len(missing_from_actual)}")
                logger.info(f"   - Missing review keys: {list(missing_from_actual)[:5]}...")
            
            if extra_in_actual:
                logger.warning(f"⚠️  Extra reviews in actual method: {len(extra_in_actual)}")
                logger.info(f"   - Extra review keys: {list(extra_in_actual)[:5]}...")
        else:
            logger.error(f"❌ Category {CATEGORY_ID} not found in actual method results")
        
        # Test the actual methods
        logger.info("\n🔍 Testing actual methods")
        
        # Get category statistics (tooltip data)
        category_stats = await data_service.get_category_statistics(
            project_id=PROJECT_ID,
            asins=project_asins,
            aspect_types=['phy_perf']
        )
        
        tooltip_category = None
        for cat in category_stats:
            if cat['category_pk'] == CATEGORY_ID:
                tooltip_category = cat
                break
        
        if tooltip_category:
            logger.info("📊 Tooltip results:")
            logger.info(f"   - Total Reviews: {tooltip_category['total_reviews']}")
            logger.info(f"   - Positive Reviews: {tooltip_category['positive_reviews']}")
            logger.info(f"   - Negative Reviews: {tooltip_category['negative_reviews']}")
            logger.info(f"   - Neutral Reviews: {tooltip_category['neutral_reviews']}")
            
            # 🔍 DEBUG: Check the raw data that went into the calculation
            logger.info("🔍 DEBUG: Raw data analysis for tooltip:")
            logger.info(f"   - Raw positive_reviews set size: {len(tooltip_category.get('_debug_positive_reviews', set()))}")
            logger.info(f"   - Raw negative_reviews set size: {len(tooltip_category.get('_debug_negative_reviews', set()))}")
            logger.info(f"   - Raw neutral_reviews set size: {len(tooltip_category.get('_debug_neutral_reviews', set()))}")
            logger.info(f"   - Raw all_reviews set size: {len(tooltip_category.get('_debug_all_reviews', set()))}")
        
        # Get reviews by category (clicked view data)
        clicked_result = await data_service.get_reviews_by_category(
            project_id=PROJECT_ID,
            category_id=CATEGORY_ID,
            asins=project_asins,
            aspect_types=['phy_perf']
        )
        
        logger.info("📊 Clicked view results:")
        logger.info(f"   - Total Reviews: {clicked_result['total_count']}")
        logger.info(f"   - Reviews Returned: {len(clicked_result['reviews'])}")
        
        # Analyze the clicked view reviews
        clicked_sentiments = defaultdict(set)
        for review in clicked_result['reviews']:
            review_key = (review['product_id'], review['review_id'])
            for aspect in review.get('aspects', []):
                sentiment = aspect.get('sentiment')
                if sentiment:
                    clicked_sentiments[review_key].add(sentiment)
        
        clicked_positive_only = set()
        clicked_negative_only = set()
        clicked_mixed_sentiment = set()
        clicked_neutral_only = set()
        
        for review_key, sentiments in clicked_sentiments.items():
            if '+' in sentiments and '-' in sentiments:
                clicked_mixed_sentiment.add(review_key)
            elif '+' in sentiments:
                clicked_positive_only.add(review_key)
            elif '-' in sentiments:
                clicked_negative_only.add(review_key)
            else:
                clicked_neutral_only.add(review_key)
        
        logger.info("📊 Clicked view categorization:")
        logger.info(f"   - Positive only: {len(clicked_positive_only)}")
        logger.info(f"   - Negative only: {len(clicked_negative_only)}")
        logger.info(f"   - Mixed sentiment: {len(clicked_mixed_sentiment)}")
        logger.info(f"   - Neutral only: {len(clicked_neutral_only)}")
        logger.info(f"   - Total: {len(clicked_positive_only) + len(clicked_negative_only) + len(clicked_mixed_sentiment) + len(clicked_neutral_only)}")
        
        # Compare the differences
        logger.info("\n🔍 Comparison analysis:")
        
        if tooltip_category:
            tooltip_total = tooltip_category['total_reviews']
            clicked_total = clicked_result['total_count']
            
            logger.info("📊 Total counts:")
            logger.info(f"   - Tooltip: {tooltip_total}")
            logger.info(f"   - Clicked: {clicked_total}")
            logger.info(f"   - Difference: {clicked_total - tooltip_total}")
            
            # Expected based on business logic
            expected_tooltip = len(positive_only) + len(negative_only) + len(neutral_only)
            logger.info(f"📊 Expected tooltip (excluding mixed): {expected_tooltip}")
            
            if expected_tooltip == tooltip_total:
                logger.info("✅ Tooltip count matches expected business logic")
            else:
                logger.warning("⚠️  Tooltip count doesn't match expected business logic")
                logger.info(f"   - Expected: {expected_tooltip}")
                logger.info(f"   - Actual: {tooltip_total}")
                logger.info(f"   - Difference: {tooltip_total - expected_tooltip}")
        
        # 🔍 NEW: Detailed business logic analysis
        logger.info("\n🔍 Detailed business logic analysis:")
        
        # Simulate the exact business logic from get_category_statistics
        positive_reviews_set = positive_only | mixed_sentiment  # All reviews with positive sentiment
        negative_reviews_set = negative_only | mixed_sentiment  # All reviews with negative sentiment
        neutral_reviews_set = neutral_only
        
        # Apply business logic: if review has both positive and negative, only count in negative
        positive_only_reviews = positive_reviews_set - negative_reviews_set
        negative_reviews = negative_reviews_set  # This includes mixed sentiment reviews
        neutral_only_reviews = neutral_reviews_set - (positive_reviews_set | negative_reviews_set)
        
        simulated_total = len(positive_only_reviews) + len(negative_reviews) + len(neutral_only_reviews)
        
        logger.info("📊 Simulated business logic:")
        logger.info(f"   - Positive only reviews: {len(positive_only_reviews)}")
        logger.info(f"   - Negative reviews (including mixed): {len(negative_reviews)}")
        logger.info(f"   - Neutral only reviews: {len(neutral_only_reviews)}")
        logger.info(f"   - Simulated total: {simulated_total}")
        
        if tooltip_category:
            logger.info("📊 Comparison with actual tooltip:")
            logger.info(f"   - Simulated positive: {len(positive_only_reviews)} vs Actual: {tooltip_category['positive_reviews']}")
            logger.info(f"   - Simulated negative: {len(negative_reviews)} vs Actual: {tooltip_category['negative_reviews']}")
            logger.info(f"   - Simulated neutral: {len(neutral_only_reviews)} vs Actual: {tooltip_category['neutral_reviews']}")
            logger.info(f"   - Simulated total: {simulated_total} vs Actual: {tooltip_category['total_reviews']}")
        
    except Exception as e:
        logger.error(f"❌ Error during comparison: {e}", exc_info=True)

async def test_use_aspect_type():
    """Test the use aspect type for Use Case Sentiment Analysis."""
    
    supabase = get_supabase_client()
    data_service = ReviewDataService(supabase)
    
    try:
        # Get project ASINs
        project_result = supabase.table('projects').select('selected_product_asins').eq('id', PROJECT_ID).execute()
        project_asins = project_result.data[0]['selected_product_asins']
        
        logger.info("\n🔍 Testing USE aspect type for Use Case Sentiment Analysis")
        
        # Get raw data for use aspect type
        use_query = supabase.table('review_aspect_data_view').select(
            'category_pk, category_name, category_definition, aspect_type, sentiment, review_id, product_id'
        ).eq('project_id', PROJECT_ID).in_('product_id', project_asins).in_('aspect_type', ['use'])
        
        use_result = use_query.execute()
        logger.info(f"📊 USE aspect type raw data: {len(use_result.data)} records")
        
        # Get unique categories for use aspect type
        use_categories = set()
        for record in use_result.data:
            use_categories.add(record['category_pk'])
        logger.info(f"📊 USE aspect type categories: {len(use_categories)}")
        logger.info(f"📊 USE category IDs: {list(use_categories)[:10]}...")  # Show first 10
        
        if not use_categories:
            logger.warning("⚠️  No USE aspect type categories found")
            return
        
        # Pick a category to test
        test_category_id = list(use_categories)[0]
        logger.info(f"📊 Testing category: {test_category_id}")
        
        # Get category statistics for use aspect type (tooltip data)
        use_category_stats = await data_service.get_category_statistics(
            project_id=PROJECT_ID,
            asins=project_asins,
            aspect_types=['use']
        )
        
        use_tooltip_category = None
        for cat in use_category_stats:
            if cat['category_pk'] == test_category_id:
                use_tooltip_category = cat
                break
        
        if use_tooltip_category:
            logger.info(f"📊 USE Tooltip results for category {test_category_id}:")
            logger.info(f"   - Category Name: {use_tooltip_category['category_name']}")
            logger.info(f"   - Total Reviews: {use_tooltip_category['total_reviews']}")
            logger.info(f"   - Positive Reviews: {use_tooltip_category['positive_reviews']}")
            logger.info(f"   - Negative Reviews: {use_tooltip_category['negative_reviews']}")
            logger.info(f"   - Neutral Reviews: {use_tooltip_category['neutral_reviews']}")
            logger.info(f"   - Total Mentions: {use_tooltip_category['total_mentions']}")
            logger.info(f"   - Positive Mentions: {use_tooltip_category['positive_mentions']}")
            logger.info(f"   - Negative Mentions: {use_tooltip_category['negative_mentions']}")
            logger.info(f"   - Neutral Mentions: {use_tooltip_category['neutral_mentions']}")
        
        # Get reviews by category for use aspect type (clicked view data)
        use_clicked_result = await data_service.get_reviews_by_category(
            project_id=PROJECT_ID,
            category_id=test_category_id,
            asins=project_asins,
            aspect_types=['use']
        )
        
        logger.info(f"📊 USE Clicked view results for category {test_category_id}:")
        logger.info(f"   - Total Reviews: {use_clicked_result['total_count']}")
        logger.info(f"   - Reviews Returned: {len(use_clicked_result['reviews'])}")
        
        # Compare tooltip vs clicked view for use aspect type
        if use_tooltip_category:
            use_tooltip_total = use_tooltip_category['total_reviews']
            use_clicked_total = use_clicked_result['total_count']
            
            logger.info("📊 USE Comparison:")
            logger.info(f"   - Tooltip: {use_tooltip_total}")
            logger.info(f"   - Clicked: {use_clicked_total}")
            logger.info(f"   - Difference: {use_clicked_total - use_tooltip_total}")
            
            if use_tooltip_total == use_clicked_total:
                logger.info("✅ USE aspect type: Tooltip and clicked view match")
            else:
                logger.warning("⚠️  USE aspect type: Tooltip and clicked view don't match")
        
        # Test the ReviewAnalysisChartService for use aspect type
        logger.info("\n🔍 Testing ReviewAnalysisChartService for USE aspect type")
        
        from dashboard.charts.reviewAnalysis.service import ReviewAnalysisChartService
        
        service = ReviewAnalysisChartService(
            project_id=PROJECT_ID,
            filters={},
            selected_asins=project_asins
        )
        
        use_top_categories = await service.get_top_categories({
            'aspect_type': 'use',
            'sort_by': 'total_reviews',
            'sort_direction': 'desc',
            'max_categories': 5,
            'min_mentions': 1
        })
        
        logger.info("📊 USE Top Categories from ReviewAnalysisChartService:")
        logger.info(f"   - Total Categories: {use_top_categories['total_categories']}")
        
        for i, cat in enumerate(use_top_categories['categories'][:3]):  # Show first 3
            logger.info(f"   {i+1}. {cat['category_name']}:")
            logger.info(f"      - Total Reviews: {cat['total_reviews']}")
            logger.info(f"      - Positive: {cat['positive_reviews']}, Negative: {cat['negative_reviews']}")
            logger.info(f"      - Total Mentions: {cat['total_mentions']}")
        
        # Verify that the ReviewAnalysisChartService uses the same business logic
        if use_top_categories['categories']:
            first_cat = use_top_categories['categories'][0]
            logger.info("📊 Business Logic Verification for USE aspect type:")
            logger.info(f"   - Category: {first_cat['category_name']}")
            logger.info(f"   - Total Reviews: {first_cat['total_reviews']}")
            logger.info(f"   - Positive + Negative: {first_cat['positive_reviews'] + first_cat['negative_reviews']}")
            
            # Check if total_reviews equals positive + negative (business logic)
            if first_cat['total_reviews'] == first_cat['positive_reviews'] + first_cat['negative_reviews']:
                logger.info("✅ USE aspect type: Business logic applied correctly")
            else:
                logger.warning("⚠️  USE aspect type: Business logic not applied correctly")
        
    except Exception as e:
        logger.error(f"❌ Error during USE aspect type test: {e}", exc_info=True)

async def test_review_analysis_api():
    """Test the ReviewAnalysisChartService API endpoint directly."""
    
    import requests
    
    logger.info("\n🔍 Testing ReviewAnalysisChartService API endpoint directly")
    
    # Test parameters
    project_id = PROJECT_ID
    aspect_type = 'use'  # Use aspect type for "Use Case Sentiment Analysis"
    
    # Get project ASINs
    supabase = get_supabase_client()
    project_result = supabase.table('projects').select('selected_product_asins').eq('id', project_id).execute()
    project_asins = project_result.data[0]['selected_product_asins']
    
    # Prepare request body
    request_body = {
        "project_id": project_id,
        "filters": {},
        "options": {
            "aspect_type": aspect_type,
            "sort_by": "positive_reviews",
            "sort_direction": "desc",
            "max_categories": 15,
            "min_mentions": 3,
            "min_positive_mentions": 1
        }
    }
    
    try:
        # Make API call
        API_BASE_URL = 'http://localhost:8000'
        response = requests.post(
            f"{API_BASE_URL}/api/v1/dashboard/charts/review-analysis/top-categories",
            headers={'Content-Type': 'application/json'},
            json=request_body
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("✅ API call successful")
            logger.info(f"📊 Response status: {result.get('status')}")
            logger.info(f"📊 Total categories: {result.get('data', {}).get('total_categories', 0)}")
            
            categories = result.get('data', {}).get('categories', [])
            logger.info(f"📊 Categories returned: {len(categories)}")
            
            # Check first few categories for business logic consistency
            for i, cat in enumerate(categories[:5]):
                logger.info(f"📊 Category {i+1}: {cat['category_name']}")
                logger.info(f"   - Total Reviews: {cat['total_reviews']}")
                logger.info(f"   - Positive Reviews: {cat['positive_reviews']}")
                logger.info(f"   - Negative Reviews: {cat['negative_reviews']}")
                logger.info(f"   - Positive + Negative: {cat['positive_reviews'] + cat['negative_reviews']}")
                
                # Check if business logic is applied correctly
                if cat['total_reviews'] == cat['positive_reviews'] + cat['negative_reviews']:
                    logger.info("   ✅ Business logic applied correctly")
                else:
                    logger.warning("   ⚠️  Business logic NOT applied correctly")
                    logger.info(f"   - Expected: {cat['positive_reviews'] + cat['negative_reviews']}")
                    logger.info(f"   - Actual: {cat['total_reviews']}")
                    logger.info(f"   - Difference: {cat['total_reviews'] - (cat['positive_reviews'] + cat['negative_reviews'])}")
        else:
            logger.error(f"❌ API call failed with status {response.status_code}")
            logger.error(f"Response: {response.text}")
            
    except Exception as e:
        logger.error(f"❌ Error testing API: {e}", exc_info=True)

async def main():
    """Run all tests."""
    await test_detailed_comparison()
    await test_use_aspect_type()
    await test_review_analysis_api()

if __name__ == "__main__":
    asyncio.run(main()) 