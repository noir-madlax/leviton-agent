"""Base service for review analysis functionality."""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict

from dashboard.services.base_service import BaseDashboardService
from core.database.connection import get_supabase_client
from .data_service import ReviewDataService
from .utils import ReviewProcessingUtils
from .constants import ReviewAnalysisConfig

logger = logging.getLogger(__name__)


class ReviewAnalysisBaseService(BaseDashboardService):
    """Base service for review analysis functionality.
    
    Provides shared methods for review deduplication, aspect aggregation,
    and common database operations used by both competitor analysis and
    review analysis modules.
    """

    def __init__(self, project_id: str):
        """Initialize ReviewAnalysisBaseService.
        
        Args:
            project_id: Project ID for filtering
        """
        super().__init__(project_id)
        self.review_data_service = ReviewDataService(self.supabase)
        
        logger.info(f"ReviewAnalysisBaseService initialized for project {project_id}")

    def _deduplicate_and_aggregate_reviews(self, reviews_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Deduplicate reviews and aggregate aspects for each review.
        
        First groups by product_id, then within each product group, deduplicates by review_id.
        This ensures that reviews from different products are handled separately.
        
        Args:
            reviews_data: Raw review data from database
            
        Returns:
            List of deduplicated reviews with aggregated aspects
        """
        # First group by product_id
        product_groups = defaultdict(list)
        for review in reviews_data:
            product_id = review.get('product_id', 'unknown')
            product_groups[product_id].append(review)
        
        deduplicated_reviews = []
        
        # Process each product group
        for product_id, product_reviews in product_groups.items():
            # Within each product, group by review_id to deduplicate
            review_groups = defaultdict(list)
            for review in product_reviews:
                review_id = review['review_id']
                review_groups[review_id].append(review)
            
            # Process each unique review within this product
            for review_id, review_occurrences in review_groups.items():
                # Use the first occurrence for basic review info
                base_review = review_occurrences[0]
                
                # Aggregate aspects from all occurrences
                aspects = []
                for occurrence in review_occurrences:
                    # Format aspect description based on parent_group_name and detail_text
                    parent_group = occurrence.get('parent_group_name', '')
                    detail_text = occurrence.get('detail_text', '')
                    
                    aspect_description = ReviewProcessingUtils.format_aspect_description(parent_group, detail_text)
                    
                    aspect = {
                        'aspect_description': aspect_description,
                        'sentiment': occurrence['sentiment'],
                        'aspect_type': occurrence['aspect_type']
                    }
                    aspects.append(aspect)
                
                # Transform rating from string to integer if needed
                rating = ReviewProcessingUtils.transform_rating(base_review.get('rating'))
                
                # Create deduplicated review with aggregated aspects
                deduplicated_review = {
                    'review_id': review_id,
                    'review_title': base_review.get('review_title'),
                    'review_text': base_review['review_text'],
                    'rating': rating,
                    'verified': base_review.get('verified'),
                    'review_date': base_review.get('review_date'),
                    'aspects': aspects,  # All aspects mentioned in this review
                    'category_name': base_review['category_name'],
                    'category_definition': base_review.get('category_definition'),
                    'aspect_type': base_review['aspect_type']
                }
                
                # Add product information if available (for review analysis)
                if 'product_id' in base_review:
                    deduplicated_review['product_id'] = base_review['product_id']
                    deduplicated_review['product_title'] = base_review.get('title')
                    deduplicated_review['product_brand'] = base_review.get('brand')
                    deduplicated_review['product_url'] = base_review.get('product_url')
                
                deduplicated_reviews.append(deduplicated_review)
        
        logger.info(f"Deduplicated {len(reviews_data)} review occurrences into {len(deduplicated_reviews)} unique reviews across {len(product_groups)} products")
        return deduplicated_reviews

    async def _get_category_info(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Get category information for the specified category ID.
        
        Args:
            category_id: Category ID to get info for
            
        Returns:
            Category information dict or None if not found
        """
        try:
            result = self.supabase.table(ReviewAnalysisConfig.ASPECT_CATEGORIES_TABLE).select(
                'category_pk, name, definition, aspect_type, stage'
            ).eq('category_pk', category_id).eq('project_id', self.project_id).execute()
            
            if result.data:
                category_data = result.data[0]
                return {
                    'category_pk': category_data['category_pk'],
                    'name': category_data['name'],
                    'definition': category_data['definition'],
                    'aspect_type': category_data['aspect_type'],
                    'stage': category_data['stage']
                }
            
            logger.warning(f"Category {category_id} not found for project {self.project_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error getting category info: {e}", exc_info=True)
            return None

    def _apply_review_sorting(self, query, sort_by: str, sort_order: str):
        """Apply review sorting to a query.
        
        Args:
            query: Supabase query object
            sort_by: Sort field
            sort_order: Sort direction
            
        Returns:
            Query with sorting applied
        """
        if sort_by == 'date':
            query = query.order('review_date', desc=(sort_order == 'desc'))
        elif sort_by == 'rating':
            query = query.order('rating', desc=(sort_order == 'desc'))
        elif sort_by == 'sentiment':
            query = query.order('sentiment', desc=(sort_order == 'desc'))
        else:
            # Default sort by review_id
            query = query.order('review_id', desc=(sort_order == 'desc'))
        
        return query

    def _get_filtered_asins(self) -> List[str]:
        """Get filtered ASINs based on project filters.
        
        Returns:
            List of filtered ASINs
        """
        try:
            # Build query to get platform_id field
            query = self._get_base_product_table().select('platform_id')
            
            # Apply all filters (ASIN + category + brand + segments + extend_fields)
            query = self._apply_combined_filters(query)
            
            result = query.execute()
            
            filtered_asins = [item['platform_id'] for item in result.data] if result.data else []
            logger.info(f"Filtered ASINs: {len(filtered_asins)} products match all filters")
            
            return filtered_asins
            
        except Exception as e:
            logger.error(f"Error getting filtered ASINs: {e}", exc_info=True)
            return []

    def _get_empty_response(self) -> Dict[str, Any]:
        """Return empty response data.
        
        Returns:
            Empty response structure
        """
        return {
            "data": [],
            "total_count": 0,
            "summary": {}
        } 