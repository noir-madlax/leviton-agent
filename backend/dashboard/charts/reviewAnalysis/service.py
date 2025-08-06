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

    def __init__(self, project_id: str, filters: Optional[Dict[str, Any]] = None, 
                 selected_asins: Optional[List[str]] = None, date_range: Optional[Dict[str, str]] = None):
        """Initialize ReviewAnalysisChartService with cache isolation.
        
        Args:
            project_id: Project ID for filtering
            filters: Optional filters (categories, brands, segments, extend_fields)
            selected_asins: Optional list of ASINs to analyze (takes precedence over filters)
            date_range: Optional date range (not used for review analysis)
        """
        super().__init__(project_id)
        
        # Store selected_asins for later use
        self.selected_asins = selected_asins
        self.original_filters = filters.copy() if filters else None
        
        # Cache management with isolation
        self._asin_cache: Dict[str, List[str]] = {}  # cache_key -> asins
        self._current_cache_key: Optional[str] = None
        
        # Set filters if provided and no selected_asins
        if filters and not selected_asins:
            self._apply_filters(filters)
        
        logger.info(f"ReviewAnalysisChartService initialized for project {project_id}")

    def _create_cache_key(self, project_id: str, filters: Optional[Dict[str, Any]], 
                         selected_asins: Optional[List[str]]) -> str:
        """Create a unique cache key for the given parameters.
        
        Args:
            project_id: Project ID
            filters: Filter dictionary
            selected_asins: Selected ASINs list
            
        Returns:
            Unique cache key string
        """
        import hashlib
        import json
        
        # Create a deterministic cache key
        cache_data = {
            'project_id': project_id,
            'filters': self._normalize_filters(filters) if filters else None,
            'selected_asins': sorted(selected_asins) if selected_asins else None
        }
        
        # Create hash from sorted JSON representation
        cache_str = json.dumps(cache_data, sort_keys=True, default=str)
        cache_key = hashlib.sha256(cache_str.encode()).hexdigest()[:16]  # Short hash
        
        logger.debug(f"Created cache key {cache_key} for project {project_id}")
        return cache_key
    
    def _normalize_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize filters for consistent cache key generation.
        
        Args:
            filters: Raw filters dictionary
            
        Returns:
            Normalized filters dictionary
        """
        if not filters:
            return {}
        
        normalized = {}
        for key, value in filters.items():
            if isinstance(value, list):
                # Sort lists for consistent ordering
                normalized[key] = sorted(value)
            elif isinstance(value, dict):
                # Recursively normalize nested dictionaries
                normalized[key] = self._normalize_filters(value)
            else:
                normalized[key] = value
        
        return normalized

    def _apply_filters(self, filters: Dict[str, Any]):
        """Apply filters and update current cache key.
        
        Args:
            filters: Filters to apply
        """
        from core.models.filters import ProjectFilters
        
        # Handle both dict and FiltersModel objects
        if hasattr(filters, 'dict'):
            filters_dict = filters.dict()
        else:
            filters_dict = filters
            
        project_filters = ProjectFilters.from_dict(filters_dict)
        self.set_project_filters(project_filters)
        
        # Update current cache key
        self._current_cache_key = self._create_cache_key(
            self.project_id, 
            filters_dict, 
            self.selected_asins
        )
        
        logger.info(f"Applied filters, cache key: {self._current_cache_key}")

    def _get_asins_to_analyze(self) -> List[str]:
        """Get ASINs to analyze based on selected_asins or filters, with isolated caching.
        
        Returns:
            List of ASINs to analyze
        """
        if self.selected_asins:
            logger.info(f"Using selected_asins: {len(self.selected_asins)} ASINs")
            return self.selected_asins
        
        # Ensure we have a cache key for filter-based ASINs
        if self._current_cache_key is None:
            self._current_cache_key = self._create_cache_key(
                self.project_id, 
                self.original_filters, 
                self.selected_asins
            )
        
        # Check cache first
        if self._current_cache_key in self._asin_cache:
            cached_asins = self._asin_cache[self._current_cache_key]
            logger.info(f"Using cached ASINs for key {self._current_cache_key}: {len(cached_asins)} ASINs")
            return cached_asins
        
        # Compute ASINs and cache them
        logger.info(f"Computing ASINs for cache key {self._current_cache_key}")
        filtered_asins = self._get_filtered_asins()
        
        # Store in cache
        self._asin_cache[self._current_cache_key] = filtered_asins
        logger.info(f"Cached {len(filtered_asins)} ASINs for key {self._current_cache_key}")
        
        return filtered_asins

    def clear_cache(self):
        """Clear all cached ASINs.
        
        Useful for testing or when data changes require cache invalidation.
        """
        cache_count = len(self._asin_cache)
        self._asin_cache.clear()
        logger.info(f"Cleared {cache_count} cached ASIN entries")

    def clear_cache_for_key(self, cache_key: str):
        """Clear cached ASINs for a specific cache key.
        
        Args:
            cache_key: Cache key to invalidate
        """
        if cache_key in self._asin_cache:
            del self._asin_cache[cache_key]
            logger.info(f"Cleared cache for key {cache_key}")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the current cache state.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            'current_cache_key': self._current_cache_key,
            'cached_entries': len(self._asin_cache),
            'cache_keys': list(self._asin_cache.keys()),
            'cache_sizes': {k: len(v) for k, v in self._asin_cache.items()}
        }

    def update_filters(self, filters: Dict[str, Any]):
        """Update filters and ensure proper cache isolation.
        
        Args:
            filters: New filters to apply
        """
        logger.info("Updating filters and recalculating cache key")
        self.original_filters = filters.copy() if filters else None
        self._apply_filters(filters)

    def get_data(self) -> List[Dict[str, Any]]:
        """Get data - required by BaseDashboardService but not used for review analysis.
        
        Returns:
            Empty list since review analysis uses specific methods
        """
        return []

    async def get_top_categories(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Get top aspect categories with comprehensive statistics.
        
        Args:
            options: Options for filtering and selecting aspect categories
            
        Returns:
            Dict containing top categories data with statistics
        """
        try:
            logger.info(f"Getting top categories for project {self.project_id}")
            
            # Get filtered ASINs based on project filters
            filtered_asins = self._get_asins_to_analyze()
            if not filtered_asins:
                return self._get_empty_top_categories_response()
            
            # Extract aspect type filter
            aspect_type = options.get('aspect_type', 'phy_perf')
            db_aspect_types = ReviewAnalysisConfig.ASPECT_TYPE_MAP.get(aspect_type, [aspect_type])
            
            # Get category statistics with filtering and sorting
            categories_data = await self.review_data_service.get_aspect_categories_with_metrics(
                project_id=self.project_id,
                asins=filtered_asins,
                aspect_types=db_aspect_types,
                options=options
            )
            
            if not categories_data or not categories_data.get('categories'):
                return self._get_empty_top_categories_response()
            
            # Extract categories and aggregated cause summary
            categories_list = categories_data['categories']
            aggregated_cause_summary = categories_data.get('aggregated_cause_summary', [])
            
            # Calculate summary statistics
            summary_stats = ReviewProcessingUtils.aggregate_category_metrics(categories_list)
            
            # Format response
            categories = []
            for cat_data in categories_list:
                category = {
                    'category_id': cat_data['category_pk'],
                    'category_name': cat_data['category_name'],
                    'definition': cat_data['definition'],
                    'aspect_type': cat_data['aspect_type'],
                    'total_mentions': cat_data['total_mentions'],
                    'positive_mentions': cat_data['positive_mentions'],
                    'negative_mentions': cat_data['negative_mentions'],
                    'total_reviews': cat_data['total_reviews'],
                    'positive_reviews': cat_data['positive_reviews'],
                    'negative_reviews': cat_data['negative_reviews'],
                    'positive_ratio': cat_data['positive_ratio'],
                    'cause_data': cat_data.get('cause_data', [])  # Add embedded cause data
                }
                categories.append(category)
            
            result = {
                'categories': categories,
                'total_categories': len(categories),
                'summary_stats': summary_stats,
                'aggregated_cause_summary': aggregated_cause_summary  # Add aggregated cause summary
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
        sort_order: str = "desc",
        sentiment_filter: Optional[str] = None,
        rating_filter: Optional[str] = None,
        aspect_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get reviews for a specific category with optional aspect type filtering.
        
        Args:
            category_id: Category ID to get reviews for
            limit: Number of reviews to return
            offset: Number of reviews to skip
            sort_by: Sort field (review_id, date, rating, sentiment)
            sort_order: Sort direction (asc, desc)
            sentiment_filter: Optional sentiment filter (positive, negative)
            rating_filter: Optional rating filter (high, mid, low)
            aspect_types: Optional list of aspect types to filter by (e.g., ['phy', 'perf', 'use'])
                         If None, returns all aspect types for the category
        """
        try:
            logger.info(f"Getting reviews for project {self.project_id}, category {category_id}")
            
            # Get filtered ASINs based on project filters
            filtered_asins = self._get_asins_to_analyze()
            if not filtered_asins:
                return self._get_empty_reviews_response(category_id)
            
            # Get all review data for this category using centralized service
            # Use aspect_types parameter directly - no need for chart_type logic
            result = await self.review_data_service.get_reviews_by_category(
                project_id=self.project_id,
                category_id=category_id,
                asins=filtered_asins,
                sort_by=sort_by,
                sort_order=sort_order,
                aspect_types=aspect_types,
                sentiment_filter=sentiment_filter,
                rating_filter=rating_filter
            )
            
            # Get category information from centralized service
            category_info = result.get('category_info')
            
            if not result or not result.get('reviews'):
                return self._get_empty_reviews_response(category_id, category_info)
            
            # Use the already deduplicated reviews from the centralized service
            deduplicated_reviews = result['reviews']
            
            # Apply pagination
            total_reviews = len(deduplicated_reviews)
            paginated_reviews = deduplicated_reviews[offset:offset + limit]
            
            # Convert to response format (centralized service already provides the correct structure)
            reviews = []
            for review_data in paginated_reviews:
                # Create review with product information (centralized service already has correct structure)
                review = {
                    'review_id': review_data['review_id'],
                    'review_title': review_data.get('review_title'),
                    'review_text': review_data['review_text'],
                    'rating': review_data.get('rating'),
                    'verified': review_data.get('verified'),
                    'review_date': review_data.get('review_date'),
                    'aspects': review_data['aspects'],  # Already in correct format from centralized service
                    # Product information (required for review analysis)
                    'product_id': review_data['product_id'],
                    'product_title': review_data.get('title'),  # Centralized service uses 'title'
                    'product_brand': review_data.get('brand'),  # Centralized service uses 'brand'
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