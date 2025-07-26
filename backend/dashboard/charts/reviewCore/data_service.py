"""Shared data service for review analysis database operations."""

import logging
from typing import List, Dict, Any, Optional
from collections import defaultdict
from supabase import Client

from .constants import ReviewAnalysisConfig
from .utils import ReviewProcessingUtils

logger = logging.getLogger(__name__)


class ReviewDataService:
    """Shared service for review data operations."""
    
    def __init__(self, supabase_client: Client):
        self.supabase = supabase_client
    
    async def get_reviews_by_category(
        self, 
        project_id: str, 
        category_id: int, 
        asins: List[str],
        sort_by: str = "review_id",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get reviews for a category with sorting.
        
        Args:
            project_id: Project ID for filtering
            category_id: Category ID to filter by
            asins: List of ASINs to filter by
            sort_by: Sort field
            sort_order: Sort direction
            
        Returns:
            List of review data dictionaries
        """
        try:
            # Build the base query
            query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                'review_id, review_title, review_text, rating, verified, review_date, '
                'sentiment, sentiment_label, aspect_description, category_name, '
                'category_definition, aspect_type, parent_group_name, detail_text, '
                'product_id, title, brand, product_url'
            ).eq('project_id', project_id).eq('category_pk', category_id).in_('product_id', asins)
            
            # Apply sorting
            if sort_by == 'date':
                query = query.order('review_date', desc=(sort_order == 'desc'))
            elif sort_by == 'rating':
                query = query.order('rating', desc=(sort_order == 'desc'))
            elif sort_by == 'sentiment':
                query = query.order('sentiment', desc=(sort_order == 'desc'))
            else:
                # Default sort by review_id
                query = query.order('review_id', desc=(sort_order == 'desc'))
            
            # Get all data (no pagination at this level since we need to deduplicate)
            result = query.execute()
            
            if not result.data:
                logger.info(f"No reviews found for project {project_id}, category {category_id}")
                return []
            
            logger.info(f"Retrieved {len(result.data)} review occurrences from database")
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting reviews by category: {e}", exc_info=True)
            return []
    
    async def get_category_statistics(
        self, 
        project_id: str, 
        asins: List[str],
        aspect_types: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Get category statistics with mentions, sentiments, etc.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            aspect_types: Optional list of aspect types to filter by
            
        Returns:
            List of category statistics dictionaries
        """
        try:
            # Build the base query
            query = self.supabase.table(ReviewAnalysisConfig.REVIEW_ASPECT_DATA_VIEW).select(
                'category_pk, category_name, category_definition, aspect_type, sentiment, review_id'
            ).eq('project_id', project_id).in_('product_id', asins)
            
            # Apply aspect type filter if provided
            if aspect_types:
                query = query.in_('aspect_type', aspect_types)
            
            result = query.execute()
            
            if not result.data:
                logger.info(f"No category data found for project {project_id}")
                return []
            
            # Calculate metrics per category
            category_metrics = {}
            for item in result.data:
                category_pk = item['category_pk']
                if category_pk not in category_metrics:
                    category_metrics[category_pk] = {
                        'category_pk': category_pk,
                        'category_name': item['category_name'],
                        'definition': item['category_definition'],
                        'aspect_type': item['aspect_type'],
                        'mentions': 0,
                        'reviews': set(),
                        'positive_mentions': 0,
                        'negative_mentions': 0,
                        'neutral_mentions': 0
                    }
                
                category_metrics[category_pk]['mentions'] += 1
                category_metrics[category_pk]['reviews'].add(item['review_id'])
                
                # Count sentiment
                sentiment = item['sentiment']
                if sentiment == '+':
                    category_metrics[category_pk]['positive_mentions'] += 1
                elif sentiment == '-':
                    category_metrics[category_pk]['negative_mentions'] += 1
                else:
                    category_metrics[category_pk]['neutral_mentions'] += 1
            
            # Convert to list and add review counts
            categories = []
            for cat_data in category_metrics.values():
                cat_data['reviews'] = len(cat_data['reviews'])
                cat_data['positive_ratio'] = cat_data['positive_mentions'] / max(cat_data['mentions'], 1)
                categories.append(cat_data)
            
            logger.info(f"Retrieved statistics for {len(categories)} categories")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}", exc_info=True)
            return []
    
    async def get_aspect_categories_with_metrics(
        self,
        project_id: str,
        asins: List[str],
        aspect_types: List[str],
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get aspect categories with filtering and sorting options.
        
        Args:
            project_id: Project ID for filtering
            asins: List of ASINs to filter by
            aspect_types: List of aspect types to filter by
            options: Options for sorting and filtering
            
        Returns:
            List of aspect categories with metrics
        """
        try:
            # Get category statistics
            categories = await self.get_category_statistics(project_id, asins, aspect_types)
            
            if not categories:
                return []
            
            # Apply filters
            categories = self._apply_category_filters(categories, options)
            
            # Apply sorting
            categories = self._apply_category_sorting(categories, options)
            
            # Apply limit
            max_categories = options.get('max_categories', ReviewAnalysisConfig.DEFAULT_TOP_CATEGORIES)
            categories = categories[:max_categories]
            
            logger.info(f"Retrieved {len(categories)} aspect categories after filtering and sorting")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting aspect categories with metrics: {e}", exc_info=True)
            return []
    
    def _apply_category_filters(self, categories: List[Dict[str, Any]], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply category filters based on options.
        
        Args:
            categories: List of category data
            options: Filter options
            
        Returns:
            Filtered list of categories
        """
        filtered_categories = categories
        
        # Filter by minimum mentions
        min_mentions = options.get('min_mentions')
        if min_mentions is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['mentions'] >= min_mentions]
        
        # Filter by minimum reviews
        min_reviews = options.get('min_reviews')
        if min_reviews is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['reviews'] >= min_reviews]
        
        # Filter by minimum positive mentions
        min_positive = options.get('min_positive_mentions')
        if min_positive is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['positive_mentions'] >= min_positive]
        
        # Filter by minimum negative mentions
        min_negative = options.get('min_negative_mentions')
        if min_negative is not None:
            filtered_categories = [cat for cat in filtered_categories if cat['negative_mentions'] >= min_negative]
        
        return filtered_categories
    
    def _apply_category_sorting(self, categories: List[Dict[str, Any]], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply category sorting based on options.
        
        Args:
            categories: List of category data
            options: Sort options
            
        Returns:
            Sorted list of categories
        """
        sort_by = options.get('sort_by', 'mentions')
        sort_direction = options.get('sort_direction', 'desc')
        
        reverse = sort_direction == 'desc'
        
        if sort_by == 'mentions':
            categories.sort(key=lambda x: x['mentions'], reverse=reverse)
        elif sort_by == 'reviews':
            categories.sort(key=lambda x: x['reviews'], reverse=reverse)
        elif sort_by == 'positive_mentions':
            categories.sort(key=lambda x: x['positive_mentions'], reverse=reverse)
        elif sort_by == 'negative_mentions':
            categories.sort(key=lambda x: x['negative_mentions'], reverse=reverse)
        elif sort_by == 'positive_ratio':
            categories.sort(key=lambda x: x['positive_ratio'], reverse=reverse)
        
        return categories 