"""Competitor Analysis Chart Service for Dashboard module.

This service handles competitor analysis data retrieval with efficient database queries.
"""

import logging
from typing import Dict, List, Any, Optional
from collections import defaultdict

from dashboard.services.base_service import BaseDashboardService, FilterConfig, FilterService
from core.models.filters import ProjectFilters
from core.database.connection import get_supabase_client
from ..base_models import FiltersModel, DateRangeModel
from ..reviewCore import ReviewAnalysisBaseService


logger = logging.getLogger(__name__)


class CompetitorAnalysisChartService(ReviewAnalysisBaseService):
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
        super().__init__(project_id)
        
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
            
            # Get all data from review_aspect_data_view in a single query
            all_data = await self._get_all_competitor_data(selected_asins)
            
            # Process the data to create the response
            products = []
            for asin in selected_asins:
                asin_data = all_data.get(asin, {})
                
                # Transform rating from string to float if needed
                rating = asin_data.get('rating')
                if isinstance(rating, str) and 'out of' in rating:
                    # Extract numeric rating from "5.0 out of 5 stars" format
                    try:
                        rating = float(rating.split(' out of')[0])
                    except (ValueError, IndexError):
                        rating = None
                
                products.append({
                    'asin': asin,
                    'product_title': asin_data.get('title', 'Unknown Product'),
                    'rating': rating,
                    'brand': asin_data.get('brand'),
                    'product_url': asin_data.get('product_url'),
                    'list_price': asin_data.get('list_price_usd') if asin_data.get('list_price_usd') is not None else None,
                    'unique_reviews_count': asin_data.get('unique_reviews_count', 0),
                    'additional_metrics': {
                        'sentiment_distribution': asin_data.get('sentiment_distribution', {'positive': 0, 'negative': 0, 'neutral': 0}),
                        'category_counts': asin_data.get('category_counts', {})
                    }
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

    async def get_reviews_by_category_product(
        self, 
        category_id: int, 
        product_id: str,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "review_id",
        sort_order: str = "desc"
    ) -> Dict[str, Any]:
        """Get reviews for a specific category and product with deduplication and aspect aggregation.
        
        Args:
            category_id: Category ID to filter by
            product_id: Product ID (ASIN) to filter by
            limit: Number of reviews to return (default: 100)
            offset: Offset for pagination (default: 0)
            sort_by: Sort field (review_id, date, rating, sentiment)
            sort_order: Sort direction (asc, desc)
            
        Returns:
            Dict containing deduplicated reviews with aggregated aspects
        """
        try:
            logger.info(f"Getting reviews for project {self.project_id}, category {category_id}, product {product_id}")
            
            # Get category information first
            category_info = await self._get_category_info(category_id)
            
            # Get all review data for this category and product
            all_reviews_data = await self._get_all_reviews_data(category_id, product_id, sort_by, sort_order)
            
            # Deduplicate reviews and aggregate aspects
            deduplicated_reviews = self._deduplicate_and_aggregate_reviews(all_reviews_data)
            
            # Apply pagination
            total_reviews = len(deduplicated_reviews)
            paginated_reviews = deduplicated_reviews[offset:offset + limit]
            
            # Convert to response format
            reviews = []
            for review_data in paginated_reviews:
                review = {
                    'review_id': review_data['review_id'],
                    'review_title': review_data.get('review_title'),
                    'review_text': review_data['review_text'],
                    'rating': review_data.get('rating'),
                    'verified': review_data.get('verified'),
                    'review_date': review_data.get('review_date'),
                    'aspects': review_data['aspects'],  # Aggregated aspects with sentiments
                    'category_name': review_data['category_name'],
                    'category_definition': review_data.get('category_definition'),
                    'aspect_type': review_data['aspect_type']
                }
                reviews.append(review)
            
            response = {
                'reviews': reviews,
                'total_reviews': total_reviews,
                'project_id': self.project_id,
                'category_id': category_id,
                'product_id': product_id,
                'category_info': category_info,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'has_more': offset + limit < total_reviews
                }
            }
            
            logger.info(f"Review retrieval service returned {len(reviews)} reviews out of {total_reviews} total")
            return response
            
        except Exception as e:
            logger.error(f"Error in get_reviews_by_category_product: {e}", exc_info=True)
            return {
                'reviews': [],
                'total_reviews': 0,
                'project_id': self.project_id,
                'category_id': category_id,
                'product_id': product_id,
                'category_info': None,
                'pagination': {
                    'limit': limit,
                    'offset': offset,
                    'has_more': False
                }
            }



    async def _get_all_reviews_data(
        self, 
        category_id: int, 
        product_id: str,
        sort_by: str = "review_id",
        sort_order: str = "desc"
    ) -> List[Dict[str, Any]]:
        """Get all review data for a category and product with sorting.
        
        Args:
            category_id: Category ID to filter by
            product_id: Product ID to filter by
            sort_by: Sort field
            sort_order: Sort direction
            
        Returns:
            List of review data dictionaries
        """
        try:
            # Build the base query
            query = self.supabase.table('review_aspect_data_view').select(
                'review_id, review_title, review_text, rating, verified, review_date, '
                'sentiment, sentiment_label, aspect_description, category_name, '
                'category_definition, aspect_type, parent_group_name, detail_text'
            ).eq('project_id', self.project_id).eq('category_pk', category_id).eq('product_id', product_id)
            
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
                logger.info(f"No reviews found for project {self.project_id}, category {category_id}, product {product_id}")
                return []
            
            logger.info(f"Retrieved {len(result.data)} review occurrences from database")
            return result.data
            
        except Exception as e:
            logger.error(f"Error getting all reviews data: {e}", exc_info=True)
            return []



    async def _get_all_competitor_data(self, selected_asins: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get all competitor data from review_aspect_data_view in a single query.
        
        Args:
            selected_asins: List of ASINs to get data for
            
        Returns:
            Dict mapping ASIN to all product and review data
        """
        try:
            # Get all data from review_aspect_data_view
            result = self.supabase.table('review_aspect_data_view').select(
                'product_id, brand, title, product_url, list_price_usd, price_usd, sentiment, category_name, review_id, rating'
            ).eq('project_id', self.project_id).in_('product_id', selected_asins).execute()
            
            if not result.data:
                logger.warning("No data found for selected ASINs")
                return {}
            
            # First, deduplicate by product_id to get unique product records
            unique_products = {}
            review_data = []
            
            for item in result.data:
                asin = item['product_id']
                
                # Store unique product information (first occurrence)
                if asin not in unique_products:
                    unique_products[asin] = {
                        'brand': item['brand'],
                        'title': item['title'],
                        'product_url': item['product_url'],
                        'list_price_usd': item['list_price_usd'],
                        'price_usd': item['price_usd'],
                        'rating': item['rating'],
                        'unique_reviews_count': 0,
                        'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                        'category_counts': {},
                        'review_ids': set()
                    }
                
                # Collect review data for processing
                review_data.append({
                    'asin': asin,
                    'sentiment': item['sentiment'],
                    'category_name': item['category_name'],
                    'review_id': item['review_id']
                })
            
            # Process review data to calculate metrics
            for review_item in review_data:
                asin = review_item['asin']
                product_data = unique_products[asin]
                
                # Count unique reviews
                product_data['review_ids'].add(review_item['review_id'])
                
                # Count sentiment
                sentiment = review_item['sentiment']
                if sentiment == '+':
                    product_data['sentiment_distribution']['positive'] += 1
                elif sentiment == '-':
                    product_data['sentiment_distribution']['negative'] += 1
                else:
                    product_data['sentiment_distribution']['neutral'] += 1
                
                # Count categories
                category = review_item['category_name']
                if category:
                    if category not in product_data['category_counts']:
                        product_data['category_counts'][category] = 0
                    product_data['category_counts'][category] += 1
            
            # Convert review_ids sets to counts
            for asin, data in unique_products.items():
                data['unique_reviews_count'] = len(data['review_ids'])
                del data['review_ids']  # Remove the set, keep only the count
            
            logger.info(f"Retrieved all competitor data for {len(unique_products)} ASINs")
            return unique_products
            
        except Exception as e:
            logger.error(f"Error getting all competitor data: {e}", exc_info=True)
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
            category_info = await self._get_category_info_for_matrix(category_pks)
            
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

    async def _get_category_info_for_matrix(self, category_pks: List[int]) -> Dict[int, Dict[str, Any]]:
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