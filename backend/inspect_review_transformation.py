#!/usr/bin/env python3
"""
Script to manually inspect what reviews will be transformed from amazon_reviews to product_reviews
along with their corresponding aspects and aspect details.
"""

import json
import logging
from typing import List, Dict, Any, Set
from collections import defaultdict

from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_asins_with_aspects_but_no_product_reviews() -> List[str]:
    """Get ASINs that have aspects but are missing from product_reviews."""
    client = get_supabase_client()
    
    # Get ASINs with aspects
    aspects_result = client.table('review_analysis_aspects').select('product_id').execute()
    aspect_asins = list(set([r['product_id'] for r in aspects_result.data]))
    
    # Get ASINs with product_reviews
    reviews_result = client.table('product_reviews').select('product_id').execute()
    review_asins = list(set([r['product_id'] for r in reviews_result.data]))
    
    # Find ASINs with aspects but no product_reviews
    missing_asins = [asin for asin in aspect_asins if asin not in review_asins]
    
    logger.info(f"Found {len(missing_asins)} ASINs with aspects but missing from product_reviews")
    return missing_asins

def inspect_review_transformation_for_asin(asin: str) -> Dict[str, Any]:
    """Inspect what will be transformed for a specific ASIN."""
    client = get_supabase_client()
    
    logger.info(f"🔍 Inspecting transformation for {asin}")
    
    # Get amazon_reviews for this ASIN
    amazon_reviews = client.table('amazon_reviews').select(
        'review_id,review_title,review_text,rating,verified,review_date'
    ).eq('asin', asin).execute()
    
    # Get aspects for this ASIN
    aspects = client.table('review_analysis_aspects').select(
        'aspect_pk,category_pk,detail_text'
    ).eq('product_id', asin).execute()
    
    # Get aspect occurrences
    aspect_pks = [aspect['aspect_pk'] for aspect in aspects.data]
    occurrences = []
    if aspect_pks:
        occurrences = client.table('review_analysis_aspect_occurrences').select(
            'aspect_pk,review_id,sentiment'
        ).in_('aspect_pk', aspect_pks).execute().data
    
    # Get categories
    category_pks = list(set([aspect['category_pk'] for aspect in aspects.data if aspect['category_pk'] is not None]))
    categories = []
    if category_pks:
        categories = client.table('review_analysis_aspect_categories').select(
            'category_pk,name,stage'
        ).in_('category_pk', category_pks).execute().data
    
    # Create category mapping
    category_map = {cat['category_pk']: cat for cat in categories}
    
    # Create aspect mapping
    aspect_map = {aspect['aspect_pk']: aspect for aspect in aspects.data}
    
    # Group occurrences by review_id
    review_occurrences = defaultdict(list)
    for occurrence in occurrences:
        review_occurrences[occurrence['review_id']].append(occurrence)
    
    # Create transformation preview
    transformation_preview = {
        'asin': asin,
        'amazon_reviews_count': len(amazon_reviews.data),
        'aspects_count': len(aspects.data),
        'occurrences_count': len(occurrences),
        'categories_count': len(categories),
        'reviews_to_transform': [],
        'aspect_details': []
    }
    
    # Show sample reviews that will be transformed
    for i, review in enumerate(amazon_reviews.data[:3]):  # Show first 3 reviews
        review_id = review['review_id']
        review_occs = review_occurrences.get(review_id, [])
        
        review_preview = {
            'amazon_review_id': review_id,
            'review_title': review.get('review_title', ''),
            'review_text_preview': review.get('review_text', '')[:200] + '...' if len(review.get('review_text', '')) > 200 else review.get('review_text', ''),
            'rating': review.get('rating'),
            'verified_purchase': review.get('verified'),
            'review_date': review.get('review_date'),
            'aspect_occurrences_count': len(review_occs),
            'aspect_occurrences': []
        }
        
        # Show aspect occurrences for this review
        for occ in review_occs[:5]:  # Show first 5 occurrences
            aspect = aspect_map.get(occ['aspect_pk'])
            category = category_map.get(aspect['category_pk']) if aspect and aspect['category_pk'] else None
            
            occ_preview = {
                'aspect_pk': occ['aspect_pk'],
                'aspect_text': aspect['detail_text'] if aspect else 'Unknown',
                'category_name': category['name'] if category else 'Unknown',
                'category_stage': category['stage'] if category else 'Unknown',
                'sentiment': occ['sentiment'],
                'position': 'N/A'  # start_pos and end_pos columns don't exist in the table
            }
            review_preview['aspect_occurrences'].append(occ_preview)
        
        transformation_preview['reviews_to_transform'].append(review_preview)
    
    # Show aspect details in JSON format (similar to fetch_top_review_aspects.py)
    for aspect in aspects.data[:5]:  # Show first 5 aspects
        aspect_occs = [occ for occ in occurrences if occ['aspect_pk'] == aspect['aspect_pk']]
        category = category_map.get(aspect['category_pk'])
        
        aspect_detail = {
            'aspect_pk': aspect['aspect_pk'],
            'aspect_text': aspect['detail_text'],
            'category_name': category['name'] if category else 'Unknown',
            'category_stage': category['stage'] if category else 'Unknown',
            'occurrences_count': len(aspect_occs),
            'sentiment_breakdown': {
                'positive': len([occ for occ in aspect_occs if occ['sentiment'] == '+']),
                'negative': len([occ for occ in aspect_occs if occ['sentiment'] == '-']),
                'neutral': len([occ for occ in aspect_occs if occ['sentiment'] == '0'])
            },
            'sample_occurrences': [
                {
                    'review_id': occ['review_id'],
                    'sentiment': occ['sentiment'],
                    'position': 'N/A'  # start_pos and end_pos columns don't exist in the table
                }
                for occ in aspect_occs[:3]  # Show first 3 occurrences
            ]
        }
        transformation_preview['aspect_details'].append(aspect_detail)
    
    return transformation_preview

def show_transformation_preview(asins: List[str], max_asins: int = 5):
    """Show transformation preview for multiple ASINs."""
    logger.info("🎯 Review Transformation Preview")
    logger.info("=" * 80)
    
    for i, asin in enumerate(asins[:max_asins]):
        logger.info(f"📦 ASIN {i+1}/{min(len(asins), max_asins)}: {asin}")
        logger.info("-" * 60)
        
        try:
            preview = inspect_review_transformation_for_asin(asin)
            
            logger.info(f"📊 Summary:")
            logger.info(f"  Amazon reviews: {preview['amazon_reviews_count']}")
            logger.info(f"  Aspects: {preview['aspects_count']}")
            logger.info(f"  Occurrences: {preview['occurrences_count']}")
            logger.info(f"  Categories: {preview['categories_count']}")
            
            logger.info(f"📝 Sample Reviews to Transform:")
            for j, review in enumerate(preview['reviews_to_transform']):
                logger.info(f"  Review {j+1}:")
                logger.info(f"    Amazon Review ID: {review['amazon_review_id']}")
                logger.info(f"    Title: {review['review_title']}")
                logger.info(f"    Text: {review['review_text_preview']}")
                logger.info(f"    Rating: {review['rating']}")
                logger.info(f"    Verified: {review['verified_purchase']}")
                logger.info(f"    Date: {review['review_date']}")
                logger.info(f"    Aspect Occurrences: {review['aspect_occurrences_count']}")
                
                if review['aspect_occurrences']:
                    logger.info(f"    Sample Aspects:")
                    for occ in review['aspect_occurrences']:
                        logger.info(f"      - {occ['aspect_text']} ({occ['category_name']}, {occ['sentiment']})")
            
            logger.info(f"🔍 Sample Aspect Details (JSON format):")
            for aspect in preview['aspect_details']:
                logger.info(f"  Aspect: {aspect['aspect_text']}")
                logger.info(f"    Category: {aspect['category_name']} (stage: {aspect['category_stage']})")
                logger.info(f"    Sentiment: {aspect['sentiment_breakdown']}")
                logger.info(f"    Sample occurrences: {aspect['sample_occurrences']}")
            
            logger.info("")
            
        except Exception as e:
            logger.error(f"Error inspecting {asin}: {e}")
            logger.info("")
    
    logger.info("=" * 80)
    logger.info(f"📋 Preview completed for {min(len(asins), max_asins)} ASINs")
    logger.info(f"Total ASINs with aspects but no product_reviews: {len(asins)}")

def main():
    """Main function."""
    logger.info("🔍 Manual Review Transformation Inspection")
    logger.info("=" * 80)
    
    # Get ASINs that need transformation
    missing_asins = get_asins_with_aspects_but_no_product_reviews()
    
    if not missing_asins:
        logger.info("✅ No ASINs found that need transformation")
        return
    
    # Show preview
    show_transformation_preview(missing_asins, max_asins=5)
    
    logger.info("💡 Next Steps:")
    logger.info("1. Review the transformation preview above")
    logger.info("2. If satisfied, run the transformation script:")
    logger.info("   python fix_missing_product_reviews.py")
    logger.info("3. After transformation, refresh the materialized view:")
    logger.info("   python refresh_matrix_view.py")

if __name__ == "__main__":
    main() 