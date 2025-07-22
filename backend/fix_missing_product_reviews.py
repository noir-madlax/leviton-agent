#!/usr/bin/env python3
"""
Script to fix missing product_reviews for ASINs that have aspects but are missing from product_reviews.
This ensures data consistency between amazon_reviews, product_reviews, and review_analysis_aspect_occurrences.
"""

import json
import logging
import sys
import os
from typing import List, Dict, Any, Set, Tuple
from datetime import datetime
from collections import defaultdict

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

try:
    from backend.core.database.connection import get_supabase_client
    from backend.data_transformation.models import TransformationConfig
    from backend.data_transformation.services.review_transformation_service import ReviewTransformationService
except ImportError as e:
    print(f"Import error: {e}")
    print("Please ensure you're running this script from the backend directory")
    sys.exit(1)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MAX_ASIN_SAMPLES = 3
BATCH_SIZE = 100
SKIP_EXISTING_DEFAULT = True
VALIDATE_CALCULATIONS_DEFAULT = False  # Disable validation to avoid issues

def get_asins_with_aspects_but_missing_reviews() -> List[str]:
    """Get ASINs that have aspects but are missing from product_reviews."""
    try:
        client = get_supabase_client()
        
        # Get ASINs with aspects
        aspects_result = client.table('review_analysis_aspects').select('product_id').execute()
        aspect_asins = list(set([r['product_id'] for r in aspects_result.data]))
        
        # Get ASINs in product_reviews
        reviews_result = client.table('product_reviews').select('product_id').execute()
        review_asins = list(set([r['product_id'] for r in reviews_result.data]))
        
        # Find missing ASINs
        missing_asins = [asin for asin in aspect_asins if asin not in review_asins]
        
        logger.info(f"Found {len(aspect_asins)} ASINs with aspects")
        logger.info(f"Found {len(review_asins)} ASINs in product_reviews")
        logger.info(f"Found {len(missing_asins)} ASINs missing from product_reviews")
        
        return missing_asins
        
    except Exception as e:
        logger.error(f"Error getting missing ASINs: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []

def check_amazon_reviews_availability(missing_asins: List[str]) -> Dict[str, int]:
    """Check which missing ASINs have reviews in amazon_reviews."""
    try:
        client = get_supabase_client()
        
        available_asins = {}
        for asin in missing_asins:
            result = client.table('amazon_reviews').select('asin').eq('asin', asin).execute()
            count = len(result.data)
            if count > 0:
                available_asins[asin] = count
        
        logger.info(f"Found {len(available_asins)} missing ASINs with reviews in amazon_reviews")
        for asin, count in available_asins.items():
            logger.info(f"  {asin}: {count} reviews")
        
        return available_asins
        
    except Exception as e:
        logger.error(f"Error checking amazon_reviews availability: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}

def get_review_id_mapping_examples(available_asins: Dict[str, int]) -> Dict[str, List[Dict[str, Any]]]:
    """Get examples of review_id mappings and aspect occurrences for validation."""
    try:
        client = get_supabase_client()
        
        examples = {}
        
        for asin, review_count in list(available_asins.items())[:MAX_ASIN_SAMPLES]:  # Check first 3 ASINs
            logger.info(f"🔍 Analyzing {asin} for review_id mapping examples...")
            
            # Get sample reviews from amazon_reviews
            amazon_reviews = client.table('amazon_reviews').select(
                'asin,review_id,review_title,review_text,rating'
            ).eq('asin', asin).limit(5).execute()
            
            # Get aspects for this ASIN
            aspects = client.table('review_analysis_aspects').select(
                'aspect_pk,product_id,detail_text,parent_group_name,category_pk'
            ).eq('product_id', asin).limit(10).execute()
            
            # Get occurrences for these aspects (only select existing columns)
            aspect_pks = [aspect['aspect_pk'] for aspect in aspects.data]
            occurrences = []
            if aspect_pks:
                occurrences = client.table('review_analysis_aspect_occurrences').select(
                    'aspect_pk,review_id,sentiment'
                ).in_('aspect_pk', aspect_pks[:5]).execute().data
            
            # Build example mapping
            example_data = {
                'amazon_reviews': amazon_reviews.data,
                'aspects': aspects.data,
                'occurrences': occurrences,
                'mapping_analysis': []
            }
            
            # Analyze review_id mapping
            for review in amazon_reviews.data[:3]:
                amazon_review_id = review['review_id']
                
                # Apply the same transformation logic as ReviewTransformationService
                if str(amazon_review_id).isdigit():
                    product_review_id = int(amazon_review_id)
                else:
                    product_review_id = hash(amazon_review_id) % 2147483647
                
                # Check if this review_id appears in occurrences
                matching_occurrences = [
                    occ for occ in occurrences 
                    if occ['review_id'] == product_review_id
                ]
                
                example_data['mapping_analysis'].append({
                    'amazon_review_id': amazon_review_id,
                    'product_review_id': product_review_id,
                    'review_title': review.get('review_title', ''),
                    'review_text': review.get('review_text', '')[:100] + '...' if review.get('review_text') else '',
                    'matching_occurrences': len(matching_occurrences),
                    'occurrence_details': matching_occurrences[:3]  # Show first 3
                })
            
            examples[asin] = example_data
        
        return examples
        
    except Exception as e:
        logger.error(f"Error getting review_id mapping examples: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}

def print_transformation_preview(examples: Dict[str, List[Dict[str, Any]]]):
    """Print a preview of what will be transformed."""
    logger.info("=" * 80)
    logger.info("📋 TRANSFORMATION PREVIEW")
    logger.info("=" * 80)
    
    for asin, data in examples.items():
        logger.info(f"\n📦 ASIN: {asin}")
        logger.info("-" * 40)
        
        logger.info("Amazon Reviews to be transformed:")
        for review in data['amazon_reviews'][:3]:
            amazon_review_id = review['review_id']
            if str(amazon_review_id).isdigit():
                product_review_id = int(amazon_review_id)
            else:
                product_review_id = hash(amazon_review_id) % 2147483647
            
            logger.info(f"  Review ID: {amazon_review_id} → {product_review_id}")
            logger.info(f"  Title: {review.get('review_title', 'N/A')}")
            logger.info(f"  Text: {review.get('review_text', 'N/A')[:100]}...")
            logger.info("")
        
        logger.info("Aspect Analysis Data (existing):")
        for aspect in data['aspects'][:3]:
            logger.info(f"  Aspect PK: {aspect['aspect_pk']}")
            logger.info(f"  Detail: {aspect['detail_text']}")
            logger.info(f"  Parent Group: {aspect.get('parent_group_name', 'N/A')}")
            logger.info("")
        
        logger.info("Review ID Mapping Analysis:")
        for mapping in data['mapping_analysis']:
            logger.info(f"  Amazon Review ID: {mapping['amazon_review_id']}")
            logger.info(f"  Product Review ID: {mapping['product_review_id']}")
            logger.info(f"  Matching Occurrences: {mapping['matching_occurrences']}")
            if mapping['occurrence_details']:
                logger.info(f"  Sample Occurrences:")
                for occ in mapping['occurrence_details']:
                    logger.info(f"    - Aspect PK: {occ['aspect_pk']}, Sentiment: {occ['sentiment']}")
            logger.info("")

def create_targeted_transformation_service(available_asins: List[str]) -> ReviewTransformationService:
    """Create a transformation service that targets specific ASINs."""
    
    class TargetedReviewTransformationService(ReviewTransformationService):
        def __init__(self, config: TransformationConfig, target_asins: List[str]):
            super().__init__(config)
            self.target_asins = target_asins
        
        def _get_source_data(self, limit=None):
            """Override to only get data for target ASINs."""
            try:
                query = self.supabase.table('amazon_reviews').select('*')
                
                # Apply filters for quality data
                query = query.neq('asin', None)
                query = query.neq('review_id', None)
                
                # Filter to target ASINs
                query = query.in_('asin', self.target_asins)
                
                # Apply limit
                if limit:
                    query = query.limit(limit)
                
                # Order by scrape_date for consistent processing
                query = query.order('scrape_date', desc=True)
                
                result = query.execute()
                return result.data or []
                
            except Exception as e:
                logger.error(f"Failed to get review source data: {e}")
                logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return []
        
        def _validate_review_data(self, data: Dict[str, Any]) -> bool:
            """Override validation to be less strict for missing reviews fix."""
            try:
                # Check required fields
                if not data.get('review_id') or not data.get('product_id'):
                    logger.warning(f"Missing required fields: review_id={data.get('review_id')}, product_id={data.get('product_id')}")
                    return False
                
                # Validate review_id is integer
                if not isinstance(data.get('review_id'), int):
                    logger.warning(f"Invalid review_id type: {type(data.get('review_id'))}")
                    return False
                
                # Skip product validation for missing reviews fix
                # The goal is to add missing reviews, not validate existing products
                if self.config.validate_calculations:
                    logger.info(f"Skipping product validation for {data['product_id']} (missing reviews fix)")
                
                return True
                
            except Exception as e:
                logger.error(f"Error validating review data: {e}")
                logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return False
    
    config = TransformationConfig(
        skip_existing=SKIP_EXISTING_DEFAULT,
        validate_calculations=VALIDATE_CALCULATIONS_DEFAULT,
        dry_run=False,
        batch_size=BATCH_SIZE
    )
    
    return TargetedReviewTransformationService(config, available_asins)

def run_targeted_transformation(available_asins: List[str]) -> Dict[str, Any]:
    """Run transformation for specific ASINs."""
    logger.info(f"🔄 Starting targeted transformation for {len(available_asins)} ASINs...")
    
    try:
        service = create_targeted_transformation_service(available_asins)
        result = service.transform_batch(limit=None)
        
        logger.info("=" * 60)
        logger.info("📊 TRANSFORMATION RESULTS")
        logger.info("=" * 60)
        logger.info(f"✅ Success: {result.success}")
        logger.info(f"📝 Processed: {result.processed_count}")
        logger.info(f"⏭️ Skipped: {result.skipped_count}")
        logger.info(f"❌ Errors: {result.error_count}")
        logger.info(f"⏱️ Duration: {result.duration_seconds:.2f} seconds")
        
        if result.summary:
            logger.info("📈 Summary:")
            for key, value in result.summary.items():
                logger.info(f"  {key}: {value}")
        
        return {
            "success": result.success,
            "processed_count": result.processed_count,
            "skipped_count": result.skipped_count,
            "error_count": result.error_count,
            "duration_seconds": result.duration_seconds,
            "summary": result.summary
        }
        
    except Exception as e:
        logger.error(f"Error running targeted transformation: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "processed_count": 0,
            "skipped_count": 0,
            "error_count": 1,
            "duration_seconds": 0,
            "summary": {"error": str(e)}
        }

def verify_transformation_success(available_asins: List[str]) -> Dict[str, bool]:
    """Verify that transformation was successful."""
    try:
        client = get_supabase_client()
        
        verification_results = {}
        
        for asin in available_asins:
            # Check if ASIN now exists in product_reviews
            result = client.table('product_reviews').select('product_id').eq('product_id', asin).execute()
            has_reviews = len(result.data) > 0
            
            # Check if aspects can now be joined with reviews
            aspects_result = client.table('review_analysis_aspects').select('aspect_pk').eq('product_id', asin).limit(5).execute()
            aspect_pks = [aspect['aspect_pk'] for aspect in aspects_result.data]
            
            can_join = False
            if aspect_pks:
                # Try to join aspects with occurrences and reviews
                occurrences_result = client.table('review_analysis_aspect_occurrences').select(
                    'aspect_pk,review_id'
                ).in_('aspect_pk', aspect_pks[:5]).execute()
                
                if occurrences_result.data:
                    review_ids = [occ['review_id'] for occ in occurrences_result.data]
                    reviews_result = client.table('product_reviews').select(
                        'review_id'
                    ).eq('product_id', asin).in_('review_id', review_ids[:5]).execute()
                    
                    can_join = len(reviews_result.data) > 0
            
            verification_results[asin] = {
                'has_reviews': has_reviews,
                'can_join_with_aspects': can_join
            }
        
        return verification_results
        
    except Exception as e:
        logger.error(f"Error verifying transformation success: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return {}

def main():
    """Main function to fix missing product_reviews."""
    logger.info("🎯 Fix Missing Product Reviews")
    logger.info("=" * 80)
    
    try:
        # Step 1: Identify missing ASINs
        logger.info("📊 Step 1: Identifying missing ASINs...")
        missing_asins = get_asins_with_aspects_but_missing_reviews()
        
        if not missing_asins:
            logger.info("✅ No missing ASINs found. All ASINs with aspects have reviews in product_reviews.")
            return
        
        # Step 2: Check amazon_reviews availability
        logger.info("📊 Step 2: Checking amazon_reviews availability...")
        available_asins = check_amazon_reviews_availability(missing_asins)
        
        if not available_asins:
            logger.warning("⚠️ No missing ASINs have reviews in amazon_reviews. Cannot proceed with transformation.")
            return
        
        # Step 3: Get transformation preview
        logger.info("📊 Step 3: Generating transformation preview...")
        examples = get_review_id_mapping_examples(available_asins)
        print_transformation_preview(examples)
        
        # Step 4: Ask for confirmation
        logger.info("=" * 80)
        logger.info("⚠️  TRANSFORMATION READY")
        logger.info("=" * 80)
        logger.info(f"This will transform {len(available_asins)} ASINs from amazon_reviews to product_reviews.")
        logger.info("The transformation ensures review_id compatibility with review_analysis_aspect_occurrences.")
        logger.info("")
        
        # For now, proceed automatically (you can add user confirmation here)
        logger.info("🔄 Proceeding with transformation...")
        
        # Step 5: Run transformation
        logger.info("📊 Step 4: Running transformation...")
        result = run_targeted_transformation(list(available_asins.keys()))
        
        # Step 6: Verify results
        logger.info("📊 Step 5: Verifying transformation...")
        verification = verify_transformation_success(list(available_asins.keys()))
        
        logger.info("=" * 80)
        logger.info("📋 VERIFICATION RESULTS")
        logger.info("=" * 80)
        
        success_count = 0
        for asin, status in verification.items():
            logger.info(f"📦 {asin}:")
            logger.info(f"   Has reviews: {'✅' if status['has_reviews'] else '❌'}")
            logger.info(f"   Can join with aspects: {'✅' if status['can_join_with_aspects'] else '❌'}")
            if status['has_reviews'] and status['can_join_with_aspects']:
                success_count += 1
            logger.info("")
        
        logger.info("=" * 80)
        logger.info(f"🎉 Transformation completed!")
        logger.info(f"   Successfully fixed: {success_count}/{len(verification)} ASINs")
        logger.info(f"   Processed: {result['processed_count']} reviews")
        logger.info(f"   Skipped: {result['skipped_count']} reviews")
        logger.info(f"   Errors: {result['error_count']} reviews")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error in main function: {e}")
        logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        sys.exit(1)

if __name__ == "__main__":
    main() 