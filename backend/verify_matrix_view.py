#!/usr/bin/env python3
"""
Script to verify the review_aspect_data_view materialized view and produce sample JSON outputs.

This script will:
1. Check if the view exists and has data
2. Show basic statistics about the view
3. Generate sample JSON outputs for test ASINs
4. Verify data quality and completeness
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

# Test ASINs from the competitor analysis
TEST_ASINS = [
    "B00NG0ELL0",  # Leviton DSL06
    "B0BVKZLT3B",  # Leviton D215S
    "B0BVKYKKRK",  # Leviton D26HD
    "B0BSHKS26L",  # Lutron Caseta Diva
    "B085D8M2MR",  # Lutron Diva
    "B01EZV35QU",  # TP Link Switch
]

def check_view_exists(supabase: Client) -> bool:
    """Check if the review_aspect_data_view view exists."""
    try:
        # Try to query the view with a simple count
        result = supabase.table('review_aspect_data_view').select('*', count='exact').limit(1).execute()
        logger.info("✅ review_aspect_data_view view exists and is accessible")
        return True
    except Exception as e:
        logger.error(f"❌ review_aspect_data_view view does not exist or is not accessible: {e}")
        return False

def get_view_statistics(supabase: Client) -> Dict[str, Any]:
    """Get basic statistics about the materialized view."""
    logger.info("📊 Getting view statistics...")
    
    stats = {}
    
    try:
        # Total records
        total_result = supabase.table('review_aspect_data_view').select('*', count='exact').execute()
        stats['total_records'] = total_result.count
        
        # Unique categories
        categories_result = supabase.table('review_aspect_data_view').select('category_name, aspect_type').execute()
        unique_categories = set()
        aspect_type_counts = defaultdict(int)
        
        for record in categories_result.data:
            unique_categories.add(record['category_name'])
            aspect_type_counts[record['aspect_type']] += 1
        
        stats['unique_categories'] = len(unique_categories)
        stats['aspect_type_distribution'] = dict(aspect_type_counts)
        
        # Unique products
        products_result = supabase.table('review_aspect_data_view').select('product_id').execute()
        unique_products = set(record['product_id'] for record in products_result.data)
        stats['unique_products'] = len(unique_products)
        
        # Sentiment distribution
        sentiment_result = supabase.table('review_aspect_data_view').select('sentiment_label').execute()
        sentiment_counts = defaultdict(int)
        for record in sentiment_result.data:
            sentiment_counts[record['sentiment_label']] += 1
        stats['sentiment_distribution'] = dict(sentiment_counts)
        
        # Sample categories
        sample_categories = list(unique_categories)[:10]
        stats['sample_categories'] = sample_categories
        
        logger.info(f"✅ View statistics retrieved successfully")
        return stats
        
    except Exception as e:
        logger.error(f"❌ Error getting view statistics: {e}")
        return {}

def get_test_asin_data(supabase: Client, asin: str) -> Dict[str, Any]:
    """Get data for a specific test ASIN from the view."""
    logger.info(f"🔍 Getting data for ASIN: {asin}")
    
    try:
        # Get all records for this ASIN
        result = supabase.table('review_aspect_data_view').select('*').eq('product_id', asin).execute()
        
        if not result.data:
            logger.warning(f"No data found for ASIN {asin}")
            return {}
        
        # Group by category
        category_data = defaultdict(lambda: {
            'num_mentions': 0,
            'num_reviews': set(),
            'positive_ratio': 0.0,
            'positive': {'count': 0, 'reviews': {}},
            'negative': {'count': 0, 'reviews': {}}
        })
        
        for record in result.data:
            category_name = record['category_name']
            sentiment = record['sentiment_label']
            review_id = record['review_id']
            review_content = record['full_review_content']
            aspect_description = record['aspect_description']
            
            # Add to category totals
            category_data[category_name]['num_mentions'] += 1
            category_data[category_name]['num_reviews'].add(review_id)
            
            # Add to sentiment counts
            if sentiment in ['positive', 'negative']:
                category_data[category_name][sentiment]['count'] += 1
                
                # Add review content
                review_key = f"{asin}#{review_id}"
                if review_key not in category_data[category_name][sentiment]['reviews']:
                    category_data[category_name][sentiment]['reviews'][review_key] = {
                        'review': review_content,
                        'aspects': []
                    }
                
                category_data[category_name][sentiment]['reviews'][review_key]['aspects'].append(aspect_description)
        
        # Calculate final statistics
        final_data = {}
        for category_name, data in category_data.items():
            # Convert sets to counts
            data['num_reviews'] = len(data['num_reviews'])
            
            # Calculate positive ratio
            if data['num_mentions'] > 0:
                positive_count = data['positive']['count']
                data['positive_ratio'] = positive_count / data['num_mentions']
            
            final_data[category_name] = data
        
        logger.info(f"✅ Retrieved data for ASIN {asin}: {len(final_data)} categories")
        return final_data
        
    except Exception as e:
        logger.error(f"❌ Error getting data for ASIN {asin}: {e}")
        return {}

def get_matrix_sample_data(supabase: Client, test_asins: List[str]) -> Dict[str, Any]:
    """Get sample matrix data for the test ASINs."""
    logger.info("📋 Getting sample matrix data...")
    
    try:
        # Get data for all test ASINs
        result = supabase.table('review_aspect_data_view').select('*').in_('product_id', test_asins).execute()
        
        if not result.data:
            logger.warning("No data found for test ASINs")
            return {}
        
        # Group by category and product
        matrix_data = defaultdict(lambda: defaultdict(lambda: {
            'mentions': 0,
            'positive_count': 0,
            'negative_count': 0,
            'reviews': []
        }))
        
        for record in result.data:
            category_name = record['category_name']
            product_id = record['product_id']
            sentiment = record['sentiment_label']
            review_content = record['full_review_content']
            aspect_description = record['aspect_description']
            
            # Add to matrix data
            matrix_data[category_name][product_id]['mentions'] += 1
            
            if sentiment == 'positive':
                matrix_data[category_name][product_id]['positive_count'] += 1
            elif sentiment == 'negative':
                matrix_data[category_name][product_id]['negative_count'] += 1
            
            # Add sample review (limit to 3 per category-product combination)
            if len(matrix_data[category_name][product_id]['reviews']) < 3:
                matrix_data[category_name][product_id]['reviews'].append({
                    'sentiment': sentiment,
                    'content': review_content[:200] + '...' if len(review_content) > 200 else review_content,
                    'aspect': aspect_description
                })
        
        # Convert to final format
        final_matrix = {}
        for category_name, products in matrix_data.items():
            final_matrix[category_name] = {}
            for product_id, data in products.items():
                final_matrix[category_name][product_id] = {
                    'mentions': data['mentions'],
                    'positive_count': data['positive_count'],
                    'negative_count': data['negative_count'],
                    'satisfaction_rate': (data['positive_count'] / data['mentions'] * 100) if data['mentions'] > 0 else 0,
                    'sample_reviews': data['reviews']
                }
        
        logger.info(f"✅ Retrieved matrix data: {len(final_matrix)} categories")
        return final_matrix
        
    except Exception as e:
        logger.error(f"❌ Error getting matrix data: {e}")
        return {}

def save_verification_results(stats: Dict[str, Any], asin_data: Dict[str, Dict[str, Any]], 
                            matrix_data: Dict[str, Any], output_dir: str = "matrix_view_verification"):
    """Save verification results to JSON files."""
    # Create output directory
    Path(output_dir).mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save view statistics
    stats_file = f"{output_dir}/view_statistics_{timestamp}.json"
    with open(stats_file, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    logger.info(f"💾 View statistics saved to: {stats_file}")
    
    # Save ASIN data
    for asin, data in asin_data.items():
        if data:  # Only save if data exists
            asin_file = f"{output_dir}/{asin}_matrix_data_{timestamp}.json"
            with open(asin_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"💾 ASIN {asin} data saved to: {asin_file}")
    
    # Save matrix sample data
    if matrix_data:
        matrix_file = f"{output_dir}/matrix_sample_data_{timestamp}.json"
        with open(matrix_file, 'w', encoding='utf-8') as f:
            json.dump(matrix_data, f, indent=2, ensure_ascii=False)
        logger.info(f"💾 Matrix sample data saved to: {matrix_file}")

def print_verification_summary(stats: Dict[str, Any], asin_data: Dict[str, Dict[str, Any]], 
                             matrix_data: Dict[str, Any]):
    """Print a summary of the verification results."""
    print("\n" + "="*80)
    print("📊 MATRIX VIEW VERIFICATION SUMMARY")
    print("="*80)
    
    if stats:
        print(f"\n📈 View Statistics:")
        print(f"   • Total Records: {stats.get('total_records', 0):,}")
        print(f"   • Unique Categories: {stats.get('unique_categories', 0)}")
        print(f"   • Unique Products: {stats.get('unique_products', 0)}")
        print(f"   • Aspect Type Distribution: {stats.get('aspect_type_distribution', {})}")
        print(f"   • Sentiment Distribution: {stats.get('sentiment_distribution', {})}")
        
        if 'sample_categories' in stats:
            print(f"   • Sample Categories: {', '.join(stats['sample_categories'][:5])}")
    
    print(f"\n🔍 Test ASIN Data:")
    for asin in TEST_ASINS:
        data = asin_data.get(asin, {})
        if data:
            total_mentions = sum(cat_data['num_mentions'] for cat_data in data.values())
            total_reviews = sum(cat_data['num_reviews'] for cat_data in data.values())
            print(f"   • {asin}: {len(data)} categories, {total_mentions} mentions, {total_reviews} reviews")
        else:
            print(f"   • {asin}: No data found")
    
    if matrix_data:
        print(f"\n📋 Matrix Sample Data:")
        print(f"   • Categories: {len(matrix_data)}")
        for category_name, products in list(matrix_data.items())[:3]:  # Show first 3 categories
            total_mentions = sum(data['mentions'] for data in products.values())
            print(f"   • {category_name}: {len(products)} products, {total_mentions} total mentions")
    
    print("\n" + "="*80)

def main():
    """Main function to run the verification script."""
    parser = argparse.ArgumentParser(description='Verify review_aspect_data_view materialized view')
    parser.add_argument('--output-dir', default='matrix_view_verification', 
                       help='Output directory for JSON files')
    parser.add_argument('--asins', type=str, help='Comma-separated list of ASINs to test')
    
    args = parser.parse_args()
    
    # Determine ASINs to test
    if args.asins:
        test_asins = [asin.strip() for asin in args.asins.split(',')]
        logger.info(f"Testing custom ASINs: {test_asins}")
    else:
        test_asins = TEST_ASINS
        logger.info(f"Testing default ASINs: {test_asins}")
    
    # Initialize Supabase client
    supabase = get_supabase_client()
    
    logger.info(f"\n{'='*60}")
    logger.info(f"MATRIX VIEW VERIFICATION")
    logger.info(f"{'='*60}")
    
    # Step 1: Check if view exists
    if not check_view_exists(supabase):
        logger.error("View verification failed - view does not exist")
        return
    
    # Step 2: Get view statistics
    stats = get_view_statistics(supabase)
    
    # Step 3: Get data for each test ASIN
    asin_data = {}
    for asin in test_asins:
        asin_data[asin] = get_test_asin_data(supabase, asin)
    
    # Step 4: Get matrix sample data
    matrix_data = get_matrix_sample_data(supabase, test_asins)
    
    # Step 5: Save results
    save_verification_results(stats, asin_data, matrix_data, args.output_dir)
    
    # Step 6: Print summary
    print_verification_summary(stats, asin_data, matrix_data)
    
    logger.info(f"\n✅ Verification completed successfully!")
    logger.info(f"📁 Results saved to: {args.output_dir}")

if __name__ == "__main__":
    main() 