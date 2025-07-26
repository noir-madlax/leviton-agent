"""Review Analysis Chart Service for Dashboard module.

This service handles review analysis data retrieval with efficient database queries.
"""

import logging
from typing import Dict, List, Any, Optional

from ..reviewCore import ReviewAnalysisBaseService, ReviewProcessingUtils
from ..reviewCore.constants import ReviewAnalysisConfig

logger = logging.getLogger(__name__)


class ReviewAnalysisChartService(ReviewAnalysisBaseService):
    """Service for review analysis data retrieval.
    
    Provides efficient access to review analysis data for all filtered products
    under a project, including top categories and reviews by category.
    """

    def __init__(self, project_id: str, filters: Optional[Dict[str, Any]] = None, date_range: Optional[Dict[str, str]] = None):
        """Initialize ReviewAnalysisChartService.
        
        Args:
            project_id: Project ID for filtering
            filters: Optional filters (categories, brands, segments, extend_fields)
            date_range: Optional date range (not used for review analysis)
        """
        super().__init__(project_id)
        
        # Set filters if provided
        if filters:
            from core.models.filters import ProjectFilters
            project_filters = ProjectFilters.from_dict(filters)
            self.set_project_filters(project_filters)
        
        logger.info(f"ReviewAnalysisChartService initialized for project {project_id}")

    def get_data(self) -> List[Dict[str, Any]]:
        """Get data - required by BaseDashboardService but not used for review analysis.
        
        Returns:
            Empty list since review analysis uses specific methods
        """
        return []

    async def get_top_categories(self, additional_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Get top aspect categories with comprehensive statistics.
        
        Args:
            additional_conditions: Additional filtering and sorting conditions
            
        Returns:
            Dict containing top categories data with statistics
        """
        try:
            logger.info(f"Getting top categories for project {self.project_id}")
            
            # Get filtered ASINs based on project filters
            filtered_asins = self._get_filtered_asins()
            if not filtered_asins:
                return self._get_empty_top_categories_response()
            
            # Extract aspect type filter
            aspect_type = additional_conditions.get('aspect_type', 'phy_perf')
            db_aspect_types = ReviewAnalysisConfig.ASPECT_TYPE_MAP.get(aspect_type, [aspect_type])
            
            # Get category statistics with filtering and sorting
            categories_data = await self.review_data_service.get_aspect_categories_with_metrics(
                project_id=self.project_id,
                asins=filtered_asins,
                aspect_types=db_aspect_types,
                options=additional_conditions
            )
            
            if not categories_data:
                return self._get_empty_top_categories_response()
            
            # Calculate summary statistics
            summary_stats = ReviewProcessingUtils.aggregate_category_metrics(categories_data)
            
            # Format response
            categories = []
            for cat_data in categories_data:
                category = {
                    'category_id': cat_data['category_pk'],
                    'category_name': cat_data['category_name'],
                    'definition': cat_data['definition'],
                    'aspect_type': cat_data['aspect_type'],
                    'total_mentions': cat_data['mentions'],
                    'positive_mentions': cat_data['positive_mentions'],
                    'negative_mentions': cat_data['negative_mentions'],
                    'neutral_mentions': cat_data['neutral_mentions'],
                    'unique_reviews': cat_data['reviews'],
                    'positive_ratio': cat_data['positive_ratio']
                }
                categories.append(category)
            
            result = {
                'categories': categories,
                'total_categories': len(categories),
                'summary_stats': summary_stats
            }
            
            logger.info(f"Top categories service returned data for {len(categories)} categories")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_top_categories: {e}", exc_info=True)
            return self._get_empty_top_categories_response()

    async def get_reviews_by_category(
        self, 
        category_id: int,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "review_id",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get reviews for a specific category with product information.
        
        Args:
            category_id: Category ID to filter by
            limit: Number of reviews to return (default: 100)
            offset: Offset for pagination (default: 0)
            sort_by: Sort field (review_id, date, rating, sentiment)
            sort_order: Sort direction (asc, desc)
            
        Returns:
            Dict containing reviews with product information and pagination
        """
        try:
            logger.info(f"Getting reviews for project {self.project_id}, category {category_id}")
            
            # Get filtered ASINs based on project filters
            filtered_asins = self._get_filtered_asins()
            if not filtered_asins:
                return self._get_empty_reviews_response(category_id)
            
            # Get category information first
            category_info = await self._get_category_info(category_id)
            
            # Get all review data for this category
            all_reviews_data = await self.review_data_service.get_reviews_by_category(
                project_id=self.project_id,
                category_id=category_id,
                asins=filtered_asins,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            if not all_reviews_data:
                return self._get_empty_reviews_response(category_id, category_info)
            
            # Deduplicate reviews and aggregate aspects
            deduplicated_reviews = self._deduplicate_and_aggregate_reviews(all_reviews_data)
            
            # Apply pagination
            total_reviews = len(deduplicated_reviews)
            paginated_reviews = deduplicated_reviews[offset:offset + limit]
            
            # Convert to response format
            reviews = []
            for review_data in paginated_reviews:
                # Convert aspects
                aspects = []
                for aspect_data in review_data['aspects']:
                    aspect = {
                        'aspect_description': aspect_data['aspect_description'],
                        'sentiment': aspect_data['sentiment'],
                        'aspect_type': aspect_data['aspect_type']
                    }
                    aspects.append(aspect)
                
                # Create review with product information
                review = {
                    'review_id': review_data['review_id'],
                    'review_title': review_data.get('review_title'),
                    'review_text': review_data['review_text'],
                    'rating': review_data.get('rating'),
                    'verified': review_data.get('verified'),
                    'review_date': review_data.get('review_date'),
                    'aspects': aspects,
                    # Product information (required for review analysis)
                    'product_id': review_data['product_id'],
                    'product_title': review_data.get('product_title'),
                    'product_brand': review_data.get('product_brand'),
                    'product_url': review_data.get('product_url')
                }
                reviews.append(review)
            
            # Convert category info
            category_info_response = None
            if category_info:
                category_info_response = {
                    'category_pk': category_info['category_pk'],
                    'name': category_info['name'],
                    'definition': category_info['definition'],
                    'aspect_type': category_info['aspect_type'],
                    'stage': category_info['stage']
                }
            
            # Create pagination info
            pagination = {
                'limit': limit,
                'offset': offset,
                'has_more': offset + limit < total_reviews
            }
            
            response = {
                'reviews': reviews,
                'total_reviews': total_reviews,
                'project_id': self.project_id,
                'category_id': category_id,
                'category_info': category_info_response,
                'pagination': pagination
            }
            
            logger.info(f"Review retrieval service returned {len(reviews)} reviews out of {total_reviews} total")
            return response
            
        except Exception as e:
            logger.error(f"Error in get_reviews_by_category: {e}", exc_info=True)
            return self._get_empty_reviews_response(category_id)

    def _get_empty_top_categories_response(self) -> Dict[str, Any]:
        """Return empty top categories response."""
        return {
            'categories': [],
            'total_categories': 0,
            'summary_stats': {
                'total_categories': 0,
                'total_mentions': 0,
                'total_reviews': 0,
                'total_positive_mentions': 0,
                'total_negative_mentions': 0,
                'overall_positive_ratio': 0.0
            }
        }

    def _get_empty_reviews_response(self, category_id: int, category_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Return empty reviews response."""
        category_info_response = None
        if category_info:
            category_info_response = {
                'category_pk': category_info['category_pk'],
                'name': category_info['name'],
                'definition': category_info['definition'],
                'aspect_type': category_info['aspect_type'],
                'stage': category_info['stage']
            }
        
        return {
            'reviews': [],
            'total_reviews': 0,
            'project_id': self.project_id,
            'category_id': category_id,
            'category_info': category_info_response,
            'pagination': {
                'limit': 100,
                'offset': 0,
                'has_more': False
            }
        } 