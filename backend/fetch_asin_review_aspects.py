#!/usr/bin/env python3
"""
Script to fetch review aspects data for specific ASINs and save each ASIN to a separate file.

Output Schema for each ASIN:
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
from pathlib import Path

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
BATCH_SIZE = 1000

# Test ASINs from rerun_reviews_cli.py
TEST_ASINS = [
    "B00NG0ELL0",  # Leviton DSL06
    "B0BVKZLT3B",  # Leviton D215S
    "B0BVKYKKRK",  # Leviton D26HD
    "B0BSHKS26L",  # Lutron Caseta Diva
    "B085D8M2MR",  # Lutron Diva
    "B01EZV35QU",  # TP Link Switch
]

def capitalize_words(text: str) -> str:
    """Capitalize the first letter of each word in the text."""
    if not text:
        return text
    return ' '.join(word.capitalize() for word in str(text).split())

def get_asin_review_aspects_data(supabase: Client, project_id: str, asin: str) -> Dict[str, Any]:
    """
    Get review aspects data for a specific ASIN.
    
    Args:
        supabase: Supabase client
        project_id: Project ID
        asin: Specific ASIN to analyze
    
    Returns:
        Dictionary with review aspects data for the ASIN
    """
    logger.info(f"Fetching review aspects data for ASIN: {asin}")
    
    # Step 1: Get aspects for this specific ASIN
    logger.info("Step 1: Getting aspects for ASIN...")
    
    # Get all aspects for this ASIN using pagination
    all_aspects = []
    page_size = 1000
    offset = 0
    
    while True:
        aspects_response = supabase.table('review_analysis_aspects').select(
            'aspect_pk,product_id,aspect_type,detail_text,parent_group_name,category_pk'
        ).eq('project_id', project_id).eq('product_id', asin).range(offset, offset + page_size - 1).execute()
        
        batch_aspects = aspects_response.data
        if not batch_aspects:
            break
            
        all_aspects.extend(batch_aspects)
        offset += page_size
        
        # If we got fewer than page_size results, we've reached the end
        if len(batch_aspects) < page_size:
            break
    
    aspects_data = all_aspects
    logger.info(f"Found {len(aspects_data)} aspects for ASIN {asin}")
    
    if not aspects_data:
        logger.warning(f"No aspects found for ASIN {asin}")
        return {}
    
    # Step 2: Get categories for the aspects found
    logger.info("Step 2: Getting categories for aspects...")
    category_pks = list(set(aspect['category_pk'] for aspect in aspects_data))
    
    categories_response = supabase.table('review_analysis_aspect_categories').select(
        'category_pk,name,definition,aspect_type'
    ).eq('project_id', project_id).eq('stage', 'final').in_('category_pk', category_pks).execute()
    
    categories_data = {cat['category_pk']: cat for cat in categories_response.data}
    logger.info(f"Found {len(categories_data)} categories for ASIN {asin}")
    
    # Step 3: Get aspect occurrences for this ASIN's aspects
    logger.info("Step 3: Getting aspect occurrences...")
    
    aspect_pks = [aspect['aspect_pk'] for aspect in aspects_data]
    
    # Get occurrences with pagination
    all_occurrences = []
    page_size = 1000
    offset = 0
    
    while True:
        occurrences_response = supabase.table('review_analysis_aspect_occurrences').select(
            'aspect_pk,sentiment,review_id'
        ).in_('aspect_pk', aspect_pks).range(offset, offset + page_size - 1).execute()
        
        batch_occurrences = occurrences_response.data
        if not batch_occurrences:
            break
            
        all_occurrences.extend(batch_occurrences)
        offset += page_size
        
        # If we got fewer than page_size results, we've reached the end
        if len(batch_occurrences) < page_size:
            break
    
    occurrences_data = all_occurrences
    logger.info(f"Found {len(occurrences_data)} occurrences for ASIN {asin}")
    
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
    
    # Step 4: Fetch review content for this ASIN
    logger.info("Step 4: Fetching review content...")
    
    # Get all unique review IDs from occurrences
    review_ids = set()
    for aspect_pk, aspect_occurrences in occurrences_by_aspect.items():
        for sentiment in ['positive', 'negative']:
            if aspect_occurrences[sentiment]['count'] > 0:
                review_ids.update(aspect_occurrences[sentiment]['review_ids'])
    
    logger.info(f"Found {len(review_ids)} unique review IDs to fetch")
    
    # Fetch review content in batches
    review_content_map = {}
    review_ids_list = list(review_ids)
    
    # Process reviews in batches
    for i in range(0, len(review_ids_list), BATCH_SIZE):
        batch_review_ids = review_ids_list[i:i + BATCH_SIZE]
        try:
            reviews_response = supabase.table('product_reviews').select(
                'review_id,review_title,review_text,product_id'
            ).eq('product_id', asin).in_('review_id', batch_review_ids).execute()
            
            for review in reviews_response.data:
                review_id = review['review_id']
                review_title = review.get('review_title', '')
                review_text = review.get('review_text', '')
                review_content = f"{review_title} - {review_text}".strip()
                review_key = f"{asin}#{review_id}"
                review_content_map[review_key] = review_content
        except Exception as e:
            logger.warning(f"Error fetching reviews batch {i//BATCH_SIZE + 1}: {e}")
            continue
    
    logger.info(f"Found review content for {len(review_content_map)} reviews")
    
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
        
        # Get aspects for this category and ASIN
        category_aspects = [aspect for aspect in aspects_data if aspect['category_pk'] == category_pk]
        
        logger.info(f"Processing category {category_name} with {len(category_aspects)} aspects")
        
        for aspect in category_aspects:
            aspect_pk = aspect['aspect_pk']
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
            
            # Get occurrences for this aspect
            aspect_occurrences = occurrences_by_aspect.get(aspect_pk, {})
            
            # Process positive and negative sentiments
            for sentiment in ['positive', 'negative']:
                sentiment_data = aspect_occurrences.get(sentiment, {'count': 0, 'review_ids': []})
                count = sentiment_data['count']
                review_ids = sentiment_data['review_ids']
                
                if count > 0:
                    # Add to category totals
                    result[category_key]['num_mentions'] += count
                    result[category_key]['num_reviews'].update(review_ids)
                    
                    # Initialize sentiment structure if not exists
                    sentiment_key = '+' if sentiment == 'positive' else '-'
                    if sentiment_key not in result[category_key]:
                        result[category_key][sentiment_key] = {'count': 0, 'reviews': {}}
                    
                    result[category_key][sentiment_key]['count'] += count
                    
                    # Add review content
                    for review_id in review_ids:
                        review_key = f"{asin}#{review_id}"
                        if review_key in review_content_map:
                            review_content = review_content_map[review_key]
                            
                            # Initialize review entry if not exists
                            if review_key not in result[category_key][sentiment_key]['reviews']:
                                result[category_key][sentiment_key]['reviews'][review_key] = {
                                    'review': review_content,
                                    'aspects': []
                                }
                            
                            # Add aspect to the review
                            result[category_key][sentiment_key]['reviews'][review_key]['aspects'].append(aspect_description)
    
    # Step 6: Calculate final statistics
    logger.info("Step 6: Calculating final statistics...")
    
    # Convert sets to counts and calculate ratios
    for category_key, category_data in result.items():
        category_data["num_reviews"] = len(category_data["num_reviews"])
        if category_data["num_mentions"] > 0:
            positive_mentions = category_data.get('+', {}).get('count', 0)
            category_data["positive_ratio"] = positive_mentions / category_data["num_mentions"]
    
    return result

def print_summary_stats(result: Dict[str, Any], asin: str) -> None:
    """Print summary statistics for the results."""
    if not result:
        print(f"No data found for ASIN {asin}.")
        return
    
    total_categories = len(result)
    total_mentions = sum(category_data["num_mentions"] for category_data in result.values())
    total_reviews = sum(category_data["num_reviews"] for category_data in result.values())
    avg_positive_ratio = sum(category_data["positive_ratio"] for category_data in result.values()) / total_categories if total_categories > 0 else 0
    
    print(f"\n📊 SUMMARY STATISTICS for ASIN {asin}:")
    print(f"   • Total Categories: {total_categories}")
    print(f"   • Total Mentions: {total_mentions}")
    print(f"   • Total Reviews: {total_reviews}")
    print(f"   • Average Positive Ratio: {avg_positive_ratio:.3f}")

def save_asin_data(asin: str, data: Dict[str, Any], output_dir: str = "asin_review_data") -> str:
    """Save ASIN data to a JSON file."""
    # Create output directory if it doesn't exist
    Path(output_dir).mkdir(exist_ok=True)
    
    # Create filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{output_dir}/{asin}_review_aspects_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    return filename

def main():
    """Main function to run the script."""
    parser = argparse.ArgumentParser(description='Fetch review aspects data for specific ASINs')
    parser.add_argument('--project-id', default=DEFAULT_PROJECT_ID, help='Project ID to analyze')
    parser.add_argument('--asins', type=str, help='Comma-separated list of ASINs (default: all test ASINs)')
    parser.add_argument('--output-dir', default='asin_review_data', help='Output directory for JSON files')
    
    args = parser.parse_args()
    
    # Determine ASINs to process
    if args.asins:
        asins = [asin.strip() for asin in args.asins.split(',')]
        logger.info(f"Processing custom ASINs: {asins}")
    else:
        asins = TEST_ASINS
        logger.info(f"Processing all test ASINs: {asins}")
    
    # Initialize Supabase client
    supabase = get_supabase_client()
    
    total_processed = 0
    total_saved = 0
    
    for asin in asins:
        try:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing ASIN: {asin}")
            logger.info(f"{'='*60}")
            
            # Get the data for this ASIN
            result = get_asin_review_aspects_data(
                supabase=supabase,
                project_id=args.project_id,
                asin=asin
            )
            
            if not result:
                logger.warning(f"No data found for ASIN {asin}")
                continue
            
            # Print summary
            print_summary_stats(result, asin)
            
            # Save to file
            filename = save_asin_data(asin, result, args.output_dir)
            logger.info(f"💾 Data saved to: {filename}")
            
            total_processed += 1
            total_saved += 1
            
        except Exception as e:
            logger.error(f"Error processing ASIN {asin}: {e}")
            continue
    
    logger.info(f"\n{'='*60}")
    logger.info(f"PROCESSING COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total ASINs processed: {total_processed}")
    logger.info(f"Total files saved: {total_saved}")
    logger.info(f"Output directory: {args.output_dir}")

if __name__ == "__main__":
    main() 