#!/usr/bin/env python3
"""
Script to fetch top customer insights (delights, pain points, use cases) from review analysis data.

Output Schema:
{
    "CategoryName#aspect_type#category_pk": {
        "num_mentions": <int>,           # Total mentions across all sentiments
        "num_reviews": <int>,            # Unique review count
        "positive_ratio": <float>,       # Ratio of positive mentions to total mentions
        "+": {                           # Positive sentiment data
            "count": <int>,              # Number of positive mentions
            "reviews": {
                "product_id#review_id": {
                    "review": "title - content",
                    "aspects": ["aspect_id#parent_group_name: detail_text", ...]
                }
            }
        },
        "-": {                           # Negative sentiment data
            "count": <int>,              # Number of negative mentions
            "reviews": {
                "product_id#review_id": {
                    "review": "title - content", 
                    "aspects": ["aspect_id#parent_group_name: detail_text", ...]
                }
            }
        }
    }
}

Note: For 'use' aspect_type, aspects are formatted as "aspect_id#detail_text" (no parent_group_name).
"""

import json
import logging
import argparse
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

from supabase import create_client, Client
from core.database.connection import get_supabase_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DEFAULT_PROJECT_ID = "d2c02b80-4c82-44cc-8093-56708a7883f7"
BATCH_SIZE = 100
MAX_CATEGORIES = 10

# Analysis types
ANALYSIS_TYPES = {
    'delights': {'sentiment': '+', 'description': 'Top Customer Delights', 'aspect_types': ['phy', 'perf']},
    'pain_points': {'sentiment': '-', 'description': 'Top Customer Pain Points', 'aspect_types': ['phy', 'perf']},
    'use_cases': {'sentiment': 'both', 'description': 'Most Mentioned Use Cases', 'aspect_types': ['use']}
}

def capitalize_words(text: str) -> str:
    """Capitalize the first letter of each word in the text."""
    if not text:
        return text
    return ' '.join(word.capitalize() for word in str(text).split())

def safe_int_conversion(value: str) -> Optional[int]:
    """Safely convert string to integer, returning None if conversion fails."""
    try:
        if value and value.isdigit():
            return int(value)
    except (ValueError, OverflowError):
        pass
    return None

def get_top_insights_data(supabase: Client, project_id: str, analysis_type: str = 'delights', 
                         asin: str = None, max_categories: int = 10) -> Dict[str, Any]:
    """
    Get top insights data (delights, pain points, or use cases) for a project.
    
    Args:
        supabase: Supabase client
        project_id: Project ID
        analysis_type: 'delights', 'pain_points', or 'use_cases'
        asin: Specific ASIN to filter by
        max_categories: Maximum number of categories to return
    
    Returns:
        Dictionary with top insights data
    """
    logger.info(f"Fetching Top Customer {analysis_type.title()} for project: {project_id}")
    
    # Get aspect types for this analysis type
    analysis_config = ANALYSIS_TYPES[analysis_type]
    aspect_types = analysis_config['aspect_types']
    
    # Step 1: Get categories
    logger.info("Step 1: Getting categories...")
    categories_query = supabase.table('review_analysis_aspect_categories').select(
        'category_pk,name,definition,aspect_type'
    ).eq('project_id', project_id).eq('stage', 'final').neq('name', 'OUT_OF_SCOPE')
    
    categories_query = categories_query.in_('aspect_type', aspect_types)
    
    categories_response = categories_query.execute()
    categories_data = {cat['category_pk']: cat for cat in categories_response.data}
    logger.info(f"Found {len(categories_data)} categories")
    
    if not categories_data:
        return {}
    
    # Step 2: Get aspects for categories with product_id
    logger.info("Step 2: Getting aspects for categories...")
    category_pks = list(categories_data.keys())
    
    # Get all aspects using pagination
    all_aspects = []
    page_size = 1000
    offset = 0
    
    while True:
        aspects_response = supabase.table('review_analysis_aspects').select(
            'aspect_pk,product_id,aspect_type,detail_text,parent_group_name,category_pk'
        ).eq('project_id', project_id).in_('category_pk', category_pks).range(offset, offset + page_size - 1).execute()
        
        batch_aspects = aspects_response.data
        if not batch_aspects:
            break
            
        all_aspects.extend(batch_aspects)
        offset += page_size
        
        # If we got fewer than page_size results, we've reached the end
        if len(batch_aspects) < page_size:
            break
    
    aspects_data = all_aspects
    
    aspects_by_category = {}
    for aspect in aspects_data:
        category_pk = aspect['category_pk']
        if category_pk not in aspects_by_category:
            aspects_by_category[category_pk] = []
        aspects_by_category[category_pk].append(aspect)
    
    logger.info(f"Found {len(aspects_data)} aspects across {len(aspects_by_category)} categories")
    
    # Debug: Check if specific aspect_pks with occurrences are in the fetched data
    known_aspects_with_occurrences = [32002, 33080, 34194, 33604, 32486]
    found_aspects = [aspect['aspect_pk'] for aspect in aspects_data if aspect['aspect_pk'] in known_aspects_with_occurrences]
    logger.info(f"Found {len(found_aspects)} known aspects with occurrences in fetched data: {found_aspects}")
    
    # Step 3: Fetch aspect occurrences with proper project filtering
    logger.info("Step 3: Fetching aspect occurrences...")
    
    # Query occurrences with pagination to get all occurrences
    all_occurrences = []
    page_size = 1000
    offset = 0
    
    while True:
        occurrences_response = supabase.table('review_analysis_aspect_occurrences').select(
            'aspect_pk,sentiment,review_id'
        ).range(offset, offset + page_size - 1).execute()
        
        batch_occurrences = occurrences_response.data
        if not batch_occurrences:
            break
            
        all_occurrences.extend(batch_occurrences)
        offset += page_size
        
        # If we got fewer than page_size results, we've reached the end
        if len(batch_occurrences) < page_size:
            break
    
    logger.info(f"Total occurrences in database: {len(all_occurrences)}")
    logger.info(f"Sample occurrences: {all_occurrences[:5]}")
    
    # Filter occurrences to only include those from aspects in our project
    project_aspect_pks = {aspect['aspect_pk'] for aspect in aspects_data}
    occurrences_data = [
        occurrence for occurrence in all_occurrences 
        if int(occurrence['aspect_pk']) in project_aspect_pks
    ]
    
    logger.info(f"Found {len(occurrences_data)} occurrences for project aspects")
    logger.info(f"Sample filtered occurrences: {occurrences_data[:5]}")
    
    # Group occurrences by aspect_pk
    occurrences_by_aspect = {}
    for occurrence in occurrences_data:
        aspect_pk = occurrence['aspect_pk']
        if aspect_pk not in occurrences_by_aspect:
            occurrences_by_aspect[aspect_pk] = {'positive': {'count': 0, 'review_ids': []}, 'negative': {'count': 0, 'review_ids': []}}
        
        sentiment = occurrence['sentiment']
        if sentiment == '+':
            occurrences_by_aspect[aspect_pk]['positive']['count'] += 1
            occurrences_by_aspect[aspect_pk]['positive']['review_ids'].append(occurrence['review_id'])
        elif sentiment == '-':
            occurrences_by_aspect[aspect_pk]['negative']['count'] += 1
            occurrences_by_aspect[aspect_pk]['negative']['review_ids'].append(occurrence['review_id'])
    
    logger.info(f"Found occurrence data for {len(occurrences_by_aspect)} aspects")
    
    # Step 4: Fetch review content
    logger.info("Step 4: Fetching review content...")
    
    # Get all unique review keys (product_id, review_id) from occurrences
    review_keys = set()
    for aspect_pk, aspect_occurrences in occurrences_by_aspect.items():
        for sentiment in ['positive', 'negative']:
            if aspect_occurrences[sentiment]['count'] > 0:
                for review_id in aspect_occurrences[sentiment]['review_ids']:
                    # Find the product_id for this aspect
                    for aspect in aspects_data:
                        if aspect['aspect_pk'] == aspect_pk:
                            review_keys.add((aspect['product_id'], review_id))
                            break
    
    logger.info(f"Found {len(review_keys)} unique review keys to fetch")
    logger.info(f"Sample review keys: {list(review_keys)[:5]}")
    
    # Debug: Show some aspect_pks in occurrences
    sample_aspect_pks = list(occurrences_by_aspect.keys())[:10]
    logger.info(f"Sample aspect_pks in occurrences: {sample_aspect_pks}")
    
    # Debug: Show some aspect_pks from aspects_data
    sample_aspects = [aspect['aspect_pk'] for aspect in aspects_data[:10]]
    logger.info(f"Sample aspect_pks from aspects: {sample_aspects}")
    
    # Debug: Check if any aspects from aspects_data are in occurrences_by_aspect
    aspects_in_occurrences = [aspect['aspect_pk'] for aspect in aspects_data if aspect['aspect_pk'] in occurrences_by_aspect]
    logger.info(f"Found {len(aspects_in_occurrences)} aspects that have occurrences data")
    if aspects_in_occurrences:
        logger.info(f"Sample aspects with occurrences: {aspects_in_occurrences[:5]}")
    else:
        logger.warning("NO ASPECTS FOUND IN OCCURRENCES DATA!")
        logger.info(f"Total aspects in aspects_data: {len(aspects_data)}")
        logger.info(f"Total aspects in occurrences_by_aspect: {len(occurrences_by_aspect)}")
    
    # Fetch review content in batches
    review_content_map = {}
    review_keys_list = list(review_keys)
    
    # Process each review key individually to avoid complex OR queries
    for product_id, review_id in review_keys_list:
        try:
            reviews_response = supabase.table('product_reviews').select(
                'review_id,review_title,review_text,product_id'
            ).eq('product_id', product_id).eq('review_id', review_id).execute()
            
            if reviews_response.data:
                for review in reviews_response.data:
                    review_id = review['review_id']
                    product_id = review['product_id']
                    review_title = review.get('review_title', '')
                    review_text = review.get('review_text', '')
                    review_content = f"{review_title} - {review_text}".strip()
                    review_key = f"{product_id}#{review_id}"
                    review_content_map[review_key] = review_content
        except Exception as e:
            logger.warning(f"Error fetching review {product_id}#{review_id}: {e}")
            continue
    
    logger.info(f"Found review content for {len(review_content_map)} reviews")
    logger.info(f"Sample review keys in review_content_map: {list(review_content_map.keys())[:5]}")
    
    # Step 5: Build the final result structure
    logger.info("Step 5: Building final result structure...")
    
    result = {}
    
    for category_pk, category_info in categories_data.items():
        category_name = capitalize_words(category_info['name'])
        aspect_type = category_info['aspect_type']
        
        # Create category key
        category_key = f"{category_name}#{aspect_type}#{category_pk}"
        result[category_key] = {
            "num_mentions": 0,
            "num_reviews": set(),
            "positive_ratio": 0.0
        }
        
        # Get aspects for this category
        category_aspects = aspects_by_category.get(category_pk, [])
        
        logger.info(f"Processing category {category_name} with {len(category_aspects)} aspects")
        
        for aspect in category_aspects:
            aspect_pk = aspect['aspect_pk']
            product_id = aspect['product_id']
            original_aspect = capitalize_words(aspect['detail_text'])
            parent_group_name = aspect.get('parent_group_name', '')
            detail_text = aspect.get('detail_text', '')
            
            # Check if this aspect has occurrences
            if aspect_pk not in occurrences_by_aspect:
                logger.debug(f"Aspect {aspect_pk} ({detail_text}) has no occurrences")
                continue
                
            logger.info(f"Processing aspect {aspect_pk} ({detail_text}) with occurrences")
            
            # Format aspect description based on aspect_type
            if aspect_type == 'use':
                aspect_description = f"{aspect_pk}#{detail_text}"
            else:
                aspect_description = f"{aspect_pk}#{parent_group_name}: {detail_text}"
            
            logger.debug(f"Processing aspect {aspect_pk} for product {product_id}")
            
            # Get occurrences for this aspect
            aspect_occurrences = occurrences_by_aspect.get(aspect_pk, {})
            
            logger.debug(f"Aspect {aspect_pk} occurrences: {aspect_occurrences}")
            
            # Process positive and negative sentiments
            for sentiment in ['positive', 'negative']:
                sentiment_data = aspect_occurrences.get(sentiment, {'count': 0, 'review_ids': []})
                count = sentiment_data['count']
                review_ids = sentiment_data['review_ids']
                
                logger.debug(f"Aspect {aspect_pk} {sentiment}: count={count}, review_ids={review_ids}")
                
                if count > 0:
                    # Add to category totals
                    result[category_key]['num_mentions'] += count
                    result[category_key]['num_reviews'].update(review_ids)
                    
                    # Initialize sentiment structure if not exists
                    if sentiment not in result[category_key]:
                        result[category_key][sentiment] = {'count': 0, 'reviews': {}}
                    
                    result[category_key][sentiment]['count'] += count
                    
                    # Add review content
                    for review_id in review_ids:
                        review_key = f"{product_id}#{review_id}"
                        if review_key in review_content_map:
                            review_content = review_content_map[review_key]
                            result[category_key][sentiment]['reviews'][review_key] = {
                                'review': review_content,
                                'aspects': [aspect_description]
                            }
                            logger.debug(f"Added review {review_key} to aspect {aspect_pk}")
                        else:
                            logger.debug(f"Review {review_key} not found in review_content_map")
                            logger.debug(f"Available review keys: {list(review_content_map.keys())[:5]}")
    
    # Step 6: Calculate final statistics and filter
    logger.info("Step 6: Calculating final statistics and filtering...")
    
    # Convert sets to counts and calculate ratios
    for category_key, category_data in result.items():
        category_data["num_reviews"] = len(category_data["num_reviews"])
        if category_data["num_mentions"] > 0:
            positive_mentions = sum(
                aspect_data.get('+', {}).get('count', 0) 
                for aspect_name, aspect_data in category_data.items() 
                if aspect_name not in ["num_mentions", "num_reviews", "positive_ratio"]
            )
            category_data["positive_ratio"] = positive_mentions / category_data["num_mentions"]
    
    # Filter based on analysis type
    if analysis_type == 'delights':
        # Sort by positive mentions, then by total mentions
        sorted_categories = sorted(
            result.items(),
            key=lambda x: (
                sum(aspect_data.get('+', {}).get('count', 0) 
                    for aspect_name, aspect_data in x[1].items() 
                    if aspect_name not in ["num_mentions", "num_reviews", "positive_ratio"]),
                x[1]["num_mentions"]
            ),
            reverse=True
        )
    elif analysis_type == 'pain_points':
        # Sort by negative mentions, then by total mentions
        sorted_categories = sorted(
            result.items(),
            key=lambda x: (
                sum(aspect_data.get('-', {}).get('count', 0) 
                    for aspect_name, aspect_data in x[1].items() 
                    if aspect_name not in ["num_mentions", "num_reviews", "positive_ratio"]),
                x[1]["num_mentions"]
            ),
            reverse=True
        )
    else:  # use_cases
        # Sort by total mentions
        sorted_categories = sorted(
            result.items(),
            key=lambda x: x[1]["num_mentions"],
            reverse=True
        )
    
    # Limit to top categories
    result = dict(sorted_categories[:max_categories])
    
    return result

def print_summary_stats(result: Dict[str, Any], analysis_type: str) -> None:
    """Print summary statistics for the results."""
    if not result:
        print("No data found for this project.")
        return
    
    analysis_config = ANALYSIS_TYPES[analysis_type]
    
    total_categories = len(result)
    total_aspects = sum(len([k for k, v in aspects_data.items() if isinstance(v, dict)]) for aspects_data in result.values())
    total_mentions = sum(category_data["num_mentions"] for category_data in result.values())
    total_reviews = sum(category_data["num_reviews"] for category_data in result.values())
    avg_positive_ratio = sum(category_data["positive_ratio"] for category_data in result.values()) / total_categories if total_categories > 0 else 0
    
    print(f"\n📊 SUMMARY STATISTICS ({analysis_config['description']}):")
    print(f"   • Total Categories: {total_categories}")
    print(f"   • Total Aspects: {total_aspects}")
    print(f"   • Total Mentions: {total_mentions}")
    print(f"   • Total Reviews: {total_reviews}")
    print(f"   • Average Positive Ratio: {avg_positive_ratio:.3f}")

def print_detailed_results(result: Dict[str, Any]) -> None:
    """Print detailed results in a formatted manner."""
    print("\n" + "=" * 80)
    print("📋 DETAILED RESULTS:")
    print("=" * 80)
    print(json.dumps(result, indent=2, ensure_ascii=False))

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Fetch top customer insights from review analysis data')
    parser.add_argument('--project-id', required=True, help='Project ID to analyze')
    parser.add_argument('--analysis-type', choices=['delights', 'pain_points', 'use_cases'], 
                       default='delights', help='Type of analysis to perform')

    parser.add_argument('--asin', help='Filter by specific ASIN')
    parser.add_argument('--max-categories', type=int, default=10, 
                       help='Maximum number of categories to return')
    
    args = parser.parse_args()
    
    # Initialize Supabase client
    supabase = get_supabase_client()
    
    try:
        # Get the data
        result = get_top_insights_data(
            supabase=supabase,
            project_id=args.project_id,
            analysis_type=args.analysis_type,
            asin=args.asin,
            max_categories=args.max_categories
        )
        
        if not result:
            print(f"No data found for project {args.project_id}")
            return
        
        # Print summary
        print_summary_stats(result, args.analysis_type)
        
        # Print detailed results
        print_detailed_results(result)
        
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{args.analysis_type}_{args.project_id}_{timestamp}.json"
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        print(f"\n💾 Results saved to: {filename}")
        
    except Exception as e:
        logger.error(f"Error in main: {e}")
        raise

if __name__ == "__main__":
    main() 