"""Competitor Analysis Chart Service for Dashboard module.

This service handles competitor analysis data retrieval with efficient database queries.
"""

import logging
from typing import Dict, List, Any, Optional

from dashboard.services.base_service import FilterService
from core.models.filters import ProjectFilters
from core.database.connection import get_supabase_client
from ..base_models import FiltersModel, DateRangeModel
from ..reviewCore import ReviewAnalysisBaseService
from ..reviewCore.data_service import ReviewDataService

logger = logging.getLogger(__name__)


class CompetitorAnalysisChartService(ReviewAnalysisBaseService):
    """Service for competitor analysis data retrieval.
    
    Provides efficient access to competitor product information and review metrics
    from product_wide_table and review_aspect_data_view.
    
    Note: This service uses selected_asins from the request instead of project filters
    since competitor analysis is specifically about analyzing provided ASINs.
    """

    def __init__(self, project_id: str, filters: Optional[FiltersModel] = None,
                 selected_asins: Optional[List[str]] = None, date_range: Optional[DateRangeModel] = None):
        """Initialize CompetitorAnalysisChartService.
        
        Args:
            project_id: Project ID (used for review data filtering)
            filters: Optional filters (not used for competitor analysis)
            selected_asins: Optional list of ASINs to analyze
            date_range: Optional date range (not used for competitor analysis)
        """
        # Initialize base service but override project ASIN validation for competitor analysis
        super().__init__(project_id)
        
        # Store selected_asins for later use
        self.selected_asins = selected_asins or []
        
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

    async def get_competitor_summary(self, selected_asins: Optional[List[str]] = None) -> Dict[str, Any]:
        """Get comprehensive competitor summary for selected ASINs.
        
        Args:
            selected_asins: Optional list of ASINs to analyze (uses instance selected_asins if not provided)
            
        Returns:
            Dict containing competitor summary data
        """
        # Use provided selected_asins or fall back to instance selected_asins
        asins_to_analyze = selected_asins or self.selected_asins
        
        if not asins_to_analyze:
            logger.warning("No selected_asins provided for competitor summary")
            return {
                'products': [],
                'total_products': 0,
                'selected_asins': []
            }
        
        try:
            logger.info(f"Getting competitor summary for project {self.project_id}, {len(asins_to_analyze)} ASINs")
            
            # Get all data from review_aspect_data_view in a single query
            all_data = await self._get_all_competitor_data(asins_to_analyze)
            
            # Process the data to create the response
            products = []
            for asin in asins_to_analyze:
                asin_data = all_data.get(asin, {})
                
                # Transform rating from string to float if needed
                rating = asin_data.get('rating')
                if isinstance(rating, str) and 'out of' in rating:
                    # Extract numeric rating from "5.0 out of 5 stars" format
                    try:
                        rating = float(rating.split(' out of')[0])
                    except (ValueError, IndexError):
                        rating = None
                elif isinstance(rating, str):
                    try:
                        # Convert simple string rating to float if needed
                        rating = float(rating)
                    except (ValueError, TypeError):
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
                'selected_asins': asins_to_analyze
            }
            
            logger.info(f"Competitor summary service returned data for {len(products)} products")
            return result
            
        except Exception as e:
            logger.error(f"Error in CompetitorAnalysisChartService: {e}", exc_info=True)
            return {
                'products': [],
                'total_products': 0,
                'selected_asins': asins_to_analyze
            }

    async def get_reviews_by_category_product(
        self, 
        category_id: int, 
        product_id: str,
        limit: int = 100,
        offset: int = 0,
        sort_by: str = "review_id",
        sort_order: str = "desc",
        sentiment_filter: Optional[str] = None,
        rating_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get reviews for a specific category and product with deduplication and aspect aggregation.
        
        Args:
            category_id: Category ID to filter by
            product_id: Product ID (ASIN) to filter by
            limit: Number of reviews to return (default: 100)
            offset: Offset for pagination (default: 0)
            sort_by: Sort field (review_id, date, rating, sentiment)
            sort_order: Sort direction (asc, desc)
            sentiment_filter: Filter by sentiment (positive, negative). If None, returns all sentiments.
            rating_filter: Filter by rating (high: 4-5 stars, mid: 3 stars, low: 1-2 stars). If None, returns all ratings.
            
        Returns:
            Dict containing deduplicated reviews with aggregated aspects
        """
        try:
            logger.info(f"Getting reviews for project {self.project_id}, category {category_id}, product {product_id}")
            
            # Get category information first
            category_info = await self._get_category_info(category_id)
            
            # Determine aspect_types based on category's aspect_type
            if category_info and 'aspect_type' in category_info:
                category_aspect_type = category_info['aspect_type']
                # Map category aspect_type to request aspect_types
                if category_aspect_type in ['phy', 'perf']:
                    aspect_types = ['phy_perf']  # Both 'phy' and 'perf' categories use 'phy_perf' mapping
                elif category_aspect_type == 'use':
                    aspect_types = ['use']  # 'use' categories use 'use' mapping
                else:
                    logger.warning(f"Unknown aspect_type '{category_aspect_type}' for category {category_id}, defaulting to phy_perf")
                    aspect_types = ['phy_perf']  # Default fallback
            else:
                logger.warning(f"Could not determine aspect_type for category {category_id}, defaulting to phy_perf")
                aspect_types = ['phy_perf']  # Default fallback
            
            logger.info(f"Using aspect_types {aspect_types} for category {category_id} (category aspect_type: {category_info.get('aspect_type', 'unknown') if category_info else 'none'})")
            
            data_service = ReviewDataService(get_supabase_client())
            result = await data_service.get_reviews_by_category(
                project_id=self.project_id,
                category_id=category_id,
                asins=[product_id],  # Only the specific product for clicked view
                sort_by=sort_by,
                sort_order=sort_order,
                aspect_types=aspect_types,  # Use dynamic aspect types based on category
                sentiment_filter=sentiment_filter,
                rating_filter=rating_filter
            )
            
            # The centralized service now returns deduplicated reviews
            deduplicated_reviews = result['reviews']
            
            # Apply pagination
            total_reviews = result['total_count']
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
        """Get all competitor data with correct ratings from product_wide_table and review data from review_aspect_data_view.
        
        Args:
            selected_asins: List of ASINs to get data for
            
        Returns:
            Dict mapping ASIN to all product and review data
        """
        try:
            # Get product information with correct average ratings from product_wide_table
            product_result = self.supabase.table('product_wide_table').select(
                'platform_id, brand, title, product_url, list_price_usd, price_usd, rating'
            ).in_('platform_id', selected_asins).execute()
            
            if not product_result.data:
                logger.warning("No product data found for selected ASINs")
                return {}
            
            # Get review data from review_aspect_data_view for sentiment and category analysis
            review_result = self.supabase.table('review_aspect_data_view').select(
                'product_id, sentiment, category_name, review_id'
            ).eq('project_id', self.project_id).in_('product_id', selected_asins).execute()
            
            # Initialize product data with correct ratings
            unique_products = {}
            for item in product_result.data:
                asin = item['platform_id']
                rating_value = item['rating']
                logger.info(f"DEBUG: ASIN {asin} rating from product_wide_table: {rating_value} (type: {type(rating_value)})")
                unique_products[asin] = {
                    'brand': item['brand'],
                    'title': item['title'],
                    'product_url': item['product_url'],
                    'list_price_usd': item['list_price_usd'],
                    'price_usd': item['price_usd'],
                    'rating': rating_value,  # This is the correct average rating from product_wide_table
                    'unique_reviews_count': 0,
                    'sentiment_distribution': {'positive': 0, 'negative': 0, 'neutral': 0},
                    'category_counts': {},
                    'review_ids': set()
                }
            
            # Process review data if available
            review_data = []
            if review_result.data:
                for item in review_result.data:
                    review_data.append({
                        'asin': item['product_id'],
                        'sentiment': item['sentiment'],
                        'category_name': item['category_name'],
                        'review_id': item['review_id']
                    })
            
            # Process review data to calculate metrics
            for review_item in review_data:
                asin = review_item['asin']
                # Only process if the ASIN exists in our product data
                if asin in unique_products:
                    product_data = unique_products[asin]
                    
                    # Count unique reviews
                    if review_item['review_id']:
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
            
            logger.info(f"Retrieved all competitor data for {len(unique_products)} ASINs with correct ratings from product_wide_table")
            return unique_products
            
        except Exception as e:
            logger.error(f"Error getting all competitor data: {e}", exc_info=True)
            return {}

    async def get_matrix_view_data(
        self, 
        aspect_type: str, 
        options: Dict[str, Any],
        selected_asins: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Get competitor matrix view data with flexible options.
        
        Args:
            aspect_type: Aspect type filter ('phy_perf' or 'use')
            options: Matrix view options for sorting and filtering
            selected_asins: Optional list of ASINs to analyze (uses instance selected_asins if not provided)
            
        Returns:
            Dict containing matrix view data
        """
        # Use provided selected_asins or fall back to instance selected_asins
        asins_to_analyze = selected_asins or self.selected_asins
        
        if not asins_to_analyze:
            logger.warning("No selected_asins provided for matrix view")
            return {
                'aspect_categories': [],
                'product_aspect_data': [],
                'selected_asins': [],
                'aspect_type': aspect_type,
                'total_categories': 0
            }
        
        try:
            logger.info(f"Getting matrix view data for project {self.project_id}, {len(asins_to_analyze)} ASINs, aspect_type: {aspect_type}")
            
            # Map aspect_type to database values
            aspect_type_map = {
                'phy_perf': ['phy', 'perf'],
                'use': ['use']
            }
            db_aspect_types = aspect_type_map.get(aspect_type, [aspect_type])
            
            # Get aspect categories with options
            categories = await self._get_aspect_categories_with_options(
                asins_to_analyze, db_aspect_types, options
            )
            
            if not categories:
                return {
                    'aspect_categories': [],
                    'product_aspect_data': [],
                    'selected_asins': asins_to_analyze,
                    'aspect_type': aspect_type,
                    'total_categories': 0
                }
            
            # Get category PKs for product aspect data
            category_pks = [cat['category_pk'] for cat in categories]
            
            # Get category information including definitions
            category_info = await self._get_category_info_for_matrix(category_pks)
            
            # Get product aspect data
            product_aspect_data = await self._get_product_aspect_data(asins_to_analyze, category_pks)
            
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
                'selected_asins': asins_to_analyze,
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
                'selected_asins': asins_to_analyze,
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
                'category_pk, category_name, aspect_type, sentiment, review_id, product_id'
            ).eq('project_id', self.project_id).in_('product_id', selected_asins).in_('aspect_type', aspect_types).execute()
            
            if not result.data:
                logger.warning("No aspect data found for selected ASINs and aspect types")
                return []
            
            # Calculate metrics per category
            category_metrics = {}
            for item in result.data:
                category_pk = item['category_pk']
                product_id = item['product_id']
                review_id = item['review_id']
                sentiment = item['sentiment']
                
                if category_pk not in category_metrics:
                    category_metrics[category_pk] = {
                        'category_pk': category_pk,
                        'category_name': item['category_name'],
                        'total_reviews': set(),  # Use set for unique review counting
                        'positive_reviews': set(),
                        'negative_reviews': set()
                    }
                
                # Create unique review key using (product_id, review_id)
                unique_review_key = (product_id, review_id)
                category_metrics[category_pk]['total_reviews'].add(unique_review_key)
                
                # Track sentiment-specific reviews
                if sentiment == '+':
                    category_metrics[category_pk]['positive_reviews'].add(unique_review_key)
                elif sentiment == '-':
                    category_metrics[category_pk]['negative_reviews'].add(unique_review_key)
            
            # Convert to list and add review counts
            categories = []
            for cat_data in category_metrics.values():
                # Convert sets to counts
                cat_data['total_reviews'] = len(cat_data['total_reviews'])
                cat_data['positive_reviews'] = len(cat_data['positive_reviews'])
                cat_data['negative_reviews'] = len(cat_data['negative_reviews'])
                categories.append(cat_data)
            
            # Apply filters and sorting in one pass
            filtered_categories = categories
            
            # Filter by minimum reviews
            min_reviews = options.get('min_reviews')
            if min_reviews is not None:
                filtered_categories = [cat for cat in filtered_categories if cat['total_reviews'] >= min_reviews]
            
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
                    filtered_categories = [cat for cat in filtered_categories if cat['positive_reviews'] > 0 and cat['negative_reviews'] == 0]
                elif sentiment_filter == 'negative_only':
                    filtered_categories = [cat for cat in filtered_categories if cat['negative_reviews'] > 0 and cat['positive_reviews'] == 0]
                elif sentiment_filter == 'mixed_only':
                    filtered_categories = [cat for cat in filtered_categories if cat['positive_reviews'] > 0 and cat['negative_reviews'] > 0]
            
            # Apply sorting
            sort_by = options.get('sort_by', 'total_reviews')
            sort_direction = options.get('sort_direction', 'desc')
            reverse = sort_direction == 'desc'
            
            if sort_by == 'total_reviews':
                filtered_categories.sort(key=lambda x: x['total_reviews'], reverse=reverse)
            elif sort_by == 'positive_reviews':
                filtered_categories.sort(key=lambda x: x['positive_reviews'], reverse=reverse)
            elif sort_by == 'negative_reviews':
                filtered_categories.sort(key=lambda x: x['negative_reviews'], reverse=reverse)
            elif sort_by == 'positive_ratio':
                # Sort by positive sentiment ratio
                filtered_categories.sort(key=lambda x: x['positive_reviews'] / max(x['total_reviews'], 1), reverse=reverse)
            
            # Apply limit
            max_categories = options.get('max_categories', 10)
            categories = filtered_categories[:max_categories]
            
            logger.info(f"Retrieved {len(categories)} aspect categories after filtering and sorting")
            return categories
            
        except Exception as e:
            logger.error(f"Error getting aspect categories with options: {e}", exc_info=True)
            return []



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