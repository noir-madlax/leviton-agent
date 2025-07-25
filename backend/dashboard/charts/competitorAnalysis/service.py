"""Competitor Analysis Chart Service for Dashboard module.

This service handles competitor analysis data retrieval with efficient database queries.
"""

import logging
from typing import Dict, List, Any, Optional

from dashboard.services.base_service import BaseDashboardService, FilterConfig, FilterService
from core.models.filters import ProjectFilters
from core.database.connection import get_supabase_client
from ..base_models import FiltersModel, DateRangeModel


logger = logging.getLogger(__name__)


class CompetitorAnalysisChartService(BaseDashboardService):
    """Service for competitor analysis data retrieval.
    
    Provides efficient access to competitor product information and review metrics
    from product_wide_table and review_aspect_data_view.
    
    Note: This service uses selected_asins from the request instead of project filters
    since competitor analysis is specifically about analyzing provided ASINs.
    """

    def __init__(self, project_id: str, filters: Optional[FiltersModel] = None,
                 date_range: Optional[DateRangeModel] = None):
        """Initialize CompetitorAnalysisChartService.
        
        Args:
            project_id: Project ID (used for review data filtering)
            filters: Optional filters (not used for competitor analysis)
            date_range: Optional date range (not used for competitor analysis)
        """
        # Initialize base service but override project ASIN validation for competitor analysis
        self.project_id = project_id
        self.supabase = get_supabase_client()
        self.filters = FilterConfig()
        self.category_filters = None
        
        # For competitor analysis, we don't need project ASIN filtering
        # since we use selected_asins from the request
        try:
            self.project_asins = self._get_project_asins()
        except Exception:
            # If project doesn't exist or has no ASINs, use empty list
            # This allows competitor analysis to work with any project_id
            self.project_asins = []
        
        self.filter_service = FilterService(self.supabase, self.project_asins)
        self.project_filters = ProjectFilters.empty()
        
        logger.info(f"CompetitorAnalysisChartService initialized for project {project_id}")

    def get_data(self) -> List[Dict[str, Any]]:
        """Get data - required by BaseDashboardService but not used for competitor analysis.
        
        Returns:
            Empty list since competitor analysis uses specific methods
        """
        return []

    async def get_competitor_summary(self, selected_asins: List[str]) -> Dict[str, Any]:
        """Get comprehensive competitor summary for selected ASINs.
        
        Args:
            selected_asins: List of ASINs to analyze
            
        Returns:
            Dict containing competitor summary data
        """
        try:
            logger.info(f"Getting competitor summary for project {self.project_id}, {len(selected_asins)} ASINs")
            
            # Get product data from product_wide_table
            product_data = await self._get_product_summary_data(selected_asins)
            
            # Get unique review counts from review_aspect_data_view
            review_counts = await self._get_unique_review_counts(selected_asins)
            
            # Get additional metrics from review_aspect_data_view
            additional_metrics = await self._get_additional_metrics(selected_asins)
            
            # Combine the data
            products = []
            for asin in selected_asins:
                product_info = product_data.get(asin, {})
                review_count = review_counts.get(asin, 0)
                metrics = additional_metrics.get(asin, {})
                
                products.append({
                    'asin': asin,
                    'product_title': product_info.get('title', 'Unknown Product'),
                    'rating': product_info.get('rating'),
                    'brand': product_info.get('brand'),
                    'product_url': product_info.get('product_url'),
                    'list_price': product_info.get('list_price_usd') if product_info.get('list_price_usd') is not None else None,
                    'unique_reviews_count': review_count,
                    'additional_metrics': metrics
                })
            
            result = {
                'products': products,
                'total_products': len(products),
                'selected_asins': selected_asins
            }
            
            logger.info(f"Competitor summary service returned data for {len(products)} products")
            return result
            
        except Exception as e:
            logger.error(f"Error in CompetitorAnalysisChartService: {e}", exc_info=True)
            return {
                'products': [],
                'total_products': 0,
                'selected_asins': selected_asins
            }

    async def _get_product_summary_data(self, selected_asins: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get product summary data from product_wide_table.
        
        Args:
            selected_asins: List of ASINs to get data for
            
        Returns:
            Dict mapping ASIN to product data
        """
        try:
            result = self.supabase.table('product_wide_table').select(
                'platform_id, title, rating, brand, product_url, list_price_usd, price_usd, reviews_count, category'
            ).in_('platform_id', selected_asins).execute()
            
            if not result.data:
                logger.warning("No product data found for selected ASINs")
                return {}
            
            # Convert to dict with ASIN as key
            product_data = {}
            for item in result.data:
                asin = item['platform_id']
                product_data[asin] = item
            
            logger.info(f"Retrieved product data for {len(product_data)} ASINs")
            return product_data
            
        except Exception as e:
            logger.error(f"Error getting product summary data: {e}", exc_info=True)
            return {}

    async def _get_unique_review_counts(self, selected_asins: List[str]) -> Dict[str, int]:
        """Get unique review counts from review_aspect_data_view.
        
        Args:
            selected_asins: List of ASINs to get review counts for
            
        Returns:
            Dict mapping ASIN to unique review count
        """
        try:
            result = self.supabase.table('review_aspect_data_view').select(
                'product_id, review_id'
            ).eq('project_id', self.project_id).in_('product_id', selected_asins).execute()
            
            if not result.data:
                logger.warning("No review data found for selected ASINs")
                return {}
            
            # Count unique reviews per ASIN
            review_counts = {}
            for item in result.data:
                asin = item['product_id']
                if asin not in review_counts:
                    review_counts[asin] = set()
                review_counts[asin].add(item['review_id'])
            
            # Convert sets to counts
            review_count_dict = {asin: len(reviews) for asin, reviews in review_counts.items()}
            
            logger.info(f"Retrieved review counts for {len(review_count_dict)} ASINs")
            return review_count_dict
            
        except Exception as e:
            logger.error(f"Error getting unique review counts: {e}", exc_info=True)
            return {}

    async def _get_additional_metrics(self, selected_asins: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get additional metrics from review_aspect_data_view.
        
        Args:
            selected_asins: List of ASINs to get metrics for
            
        Returns:
            Dict mapping ASIN to additional metrics
        """
        try:
            result = self.supabase.table('review_aspect_data_view').select(
                'product_id, sentiment, category_name'
            ).eq('project_id', self.project_id).in_('product_id', selected_asins).execute()
            
            if not result.data:
                logger.warning("No review data found for additional metrics")
                return {}
            
            # Calculate metrics per ASIN
            metrics = {}
            for item in result.data:
                asin = item['product_id']
                if asin not in metrics:
                    metrics[asin] = {
                        'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                        'category_counts': {}
                    }
                
                # Count sentiment
                sentiment = item['sentiment']
                if sentiment == '+':
                    metrics[asin]['sentiment_distribution']['positive'] += 1
                elif sentiment == '-':
                    metrics[asin]['sentiment_distribution']['negative'] += 1
                else:
                    metrics[asin]['sentiment_distribution']['neutral'] += 1
                
                # Count categories
                category = item['category_name']
                if category:
                    if category not in metrics[asin]['category_counts']:
                        metrics[asin]['category_counts'][category] = 0
                    metrics[asin]['category_counts'][category] += 1
            
            logger.info(f"Retrieved additional metrics for {len(metrics)} ASINs")
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting additional metrics: {e}", exc_info=True)
            return {}

    async def get_matrix_view_data(
        self, 
        selected_asins: List[str], 
        aspect_type: str, 
        options: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get competitor matrix view data with flexible options.
        
        Args:
            selected_asins: List of ASINs to analyze
            aspect_type: Aspect type filter ('phy_perf' or 'use')
            options: Matrix view options for sorting and filtering
            
        Returns:
            Dict containing matrix view data
        """
        try:
            logger.info(f"Getting matrix view data for project {self.project_id}, {len(selected_asins)} ASINs, aspect_type: {aspect_type}")
            
            # Map aspect_type to database values
            aspect_type_map = {
                'phy_perf': ['phy', 'perf'],  # phy_perf maps to both phy and perf
                'use': ['use']
            }
            db_aspect_types = aspect_type_map.get(aspect_type, [aspect_type])
            
            # Get aspect categories with options
            categories = await self._get_aspect_categories_with_options(
                selected_asins, db_aspect_types, options
            )
            
            if not categories:
                logger.warning("No aspect categories found for matrix view")
                return {
                    'aspect_categories': [],
                    'product_aspect_data': [],
                    'selected_asins': selected_asins,
                    'aspect_type': aspect_type,
                    'total_categories': 0
                }
            
            # Get category information
            category_pks = [cat['category_pk'] for cat in categories]
            category_info = await self._get_category_info(category_pks)
            
            # Get product aspect data
            product_aspect_data = await self._get_product_aspect_data(
                selected_asins, category_pks
            )
            
            # Format response
            aspect_categories = []
            for cat in categories:
                cat_info = category_info.get(cat['category_pk'], {})
                aspect_categories.append({
                    'category_id': cat['category_pk'],
                    'category_name': cat['category_name'],
                    'definition': cat_info.get('definition', '')
                })
            
            result = {
                'aspect_categories': aspect_categories,
                'product_aspect_data': product_aspect_data,
                'selected_asins': selected_asins,
                'aspect_type': aspect_type,
                'total_categories': len(aspect_categories)
            }
            
            logger.info(f"Matrix view service returned data for {len(aspect_categories)} categories")
            return result
            
        except Exception as e:
            logger.error(f"Error in get_matrix_view_data: {e}", exc_info=True)
            return {
                'aspect_categories': [],
                'product_aspect_data': [],
                'selected_asins': selected_asins,
                'aspect_type': aspect_type,
                'total_categories': 0
            }

    async def _get_aspect_categories_with_options(
        self, 
        selected_asins: List[str], 
        aspect_types: List[str], 
        options: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Get aspect categories with sorting and filtering options.
        
        Args:
            selected_asins: List of ASINs to analyze
            aspect_types: List of aspect types to filter by
            options: Options for sorting and filtering
            
        Returns:
            List of aspect categories with metrics
        """
        try:
            # Get all aspect categories for the selected ASINs and aspect types
            result = self.supabase.table('review_aspect_data_view').select(
                'category_pk, category_name, aspect_type, sentiment, review_id'
            ).eq('project_id', self.project_id).in_('product_id', selected_asins).in_('aspect_type', aspect_types).execute()
            
            if not result.data:
                logger.warning("No aspect data found for selected ASINs and aspect types")
                return []
            
            # Calculate metrics per category
            category_metrics = {}
            for item in result.data:
                category_pk = item['category_pk']
                if category_pk not in category_metrics:
                    category_metrics[category_pk] = {
                        'category_pk': category_pk,
                        'category_name': item['category_name'],
                        'mentions': 0,
                        'reviews': set(),
                        'sentiment_counts': {'positive': 0, 'negative': 0, 'neutral': 0}
                    }
                
                category_metrics[category_pk]['mentions'] += 1
                category_metrics[category_pk]['reviews'].add(item['review_id'])
                
                # Count sentiment
                sentiment = item['sentiment']
                if sentiment == '+':
                    category_metrics[category_pk]['sentiment_counts']['positive'] += 1
                elif sentiment == '-':
                    category_metrics[category_pk]['sentiment_counts']['negative'] += 1
                else:
                    category_metrics[category_pk]['sentiment_counts']['neutral'] += 1
            
            # Convert to list and add review counts
            categories = []
            for cat_data in category_metrics.values():
                cat_data['reviews'] = len(cat_data['reviews'])
                categories.append(cat_data)
            
            # Apply filters
            categories = self._apply_category_filters(categories, options)
            
            # Apply sorting
            categories = self._apply_category_sorting(categories, options)
            
            # Apply limit
            max_categories = options.get('max_categories', 10)
            categories = categories[:max_categories]
            
            logger.info(f"Retrieved {len(categories)} aspect categories after filtering and sorting")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting aspect categories with options: {e}", exc_info=True)
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
        
        # Filter by include categories
        include_categories = options.get('include_categories')
        if include_categories:
            filtered_categories = [cat for cat in filtered_categories if cat['category_name'] in include_categories]
        
        # Filter by exclude categories
        exclude_categories = options.get('exclude_categories')
        if exclude_categories:
            filtered_categories = [cat for cat in filtered_categories if cat['category_name'] not in exclude_categories]
        
        # Filter by sentiment
        sentiment_filter = options.get('sentiment_filter')
        if sentiment_filter:
            if sentiment_filter == 'positive_only':
                filtered_categories = [cat for cat in filtered_categories if cat['sentiment_counts']['positive'] > 0 and cat['sentiment_counts']['negative'] == 0]
            elif sentiment_filter == 'negative_only':
                filtered_categories = [cat for cat in filtered_categories if cat['sentiment_counts']['negative'] > 0 and cat['sentiment_counts']['positive'] == 0]
            elif sentiment_filter == 'mixed_only':
                filtered_categories = [cat for cat in filtered_categories if cat['sentiment_counts']['positive'] > 0 and cat['sentiment_counts']['negative'] > 0]
        
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
        elif sort_by == 'sentiment':
            # Sort by positive sentiment ratio
            categories.sort(key=lambda x: x['sentiment_counts']['positive'] / max(x['mentions'], 1), reverse=reverse)
        
        return categories

    async def _get_category_info(self, category_pks: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get category information for given category PKs.
        
        Args:
            category_pks: List of category PKs
            
        Returns:
            Dict mapping category PK to category info
        """
        try:
            if not category_pks:
                return {}
            
            result = self.supabase.table('review_analysis_aspect_categories').select(
                'category_pk, definition'
            ).in_('category_pk', category_pks).execute()
            
            category_info = {}
            for item in result.data:
                category_info[item['category_pk']] = item
            
            return category_info
            
        except Exception as e:
            logger.error(f"Error getting category info: {e}", exc_info=True)
            return {}

    async def _get_product_aspect_data(
        self, 
        selected_asins: List[str], 
        category_pks: List[int]
    ) -> List[Dict[str, Any]]:
        """Get product aspect data for matrix view.
        
        Args:
            selected_asins: List of ASINs to analyze
            category_pks: List of category PKs to include
            
        Returns:
            List of product aspect data
        """
        try:
            if not category_pks:
                return []
            
            result = self.supabase.table('review_aspect_data_view').select(
                'product_id, category_pk, sentiment, review_id'
            ).eq('project_id', self.project_id).in_('product_id', selected_asins).in_('category_pk', category_pks).execute()
            
            if not result.data:
                return []
            
            # Group by product and category
            product_aspect_data = {}
            for item in result.data:
                asin = item['product_id']
                category_pk = item['category_pk']
                
                if asin not in product_aspect_data:
                    product_aspect_data[asin] = {}
                
                if category_pk not in product_aspect_data[asin]:
                    product_aspect_data[asin][category_pk] = {
                        'mentions': 0,
                        'reviews': set(),
                        'sentiment_counts': {'positive': 0, 'negative': 0, 'neutral': 0}
                    }
                
                product_aspect_data[asin][category_pk]['mentions'] += 1
                product_aspect_data[asin][category_pk]['reviews'].add(item['review_id'])
                
                # Count sentiment
                sentiment = item['sentiment']
                if sentiment == '+':
                    product_aspect_data[asin][category_pk]['sentiment_counts']['positive'] += 1
                elif sentiment == '-':
                    product_aspect_data[asin][category_pk]['sentiment_counts']['negative'] += 1
                else:
                    product_aspect_data[asin][category_pk]['sentiment_counts']['neutral'] += 1
            
            # Convert to response format
            response_data = []
            for asin, categories in product_aspect_data.items():
                aspect_data = []
                for category_pk, metrics in categories.items():
                    metrics['reviews'] = len(metrics['reviews'])
                    aspect_data.append({
                        'category_pk': category_pk,
                        **metrics
                    })
                
                response_data.append({
                    'asin': asin,
                    'aspect_data': aspect_data
                })
            
            return response_data
            
        except Exception as e:
            logger.error(f"Error getting product aspect data: {e}", exc_info=True)
            return [] 