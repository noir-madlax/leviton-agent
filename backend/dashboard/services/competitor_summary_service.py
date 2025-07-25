"""Competitor Summary Service for Dashboard module.

This service handles competitor summary data retrieval with efficient database queries.
"""

import logging
from typing import Dict, List, Any


logger = logging.getLogger(__name__)


class CompetitorSummaryService:
    """Service for competitor summary data retrieval.
    
    Provides efficient access to competitor product information and review metrics
    from product_wide_table and review_aspect_data_view.
    """

    def __init__(self):
        """Initialize CompetitorSummaryService."""
        from core.database.connection import get_supabase_client
        self.supabase = get_supabase_client()

    async def get_competitor_summary(self, project_id: str, selected_asins: List[str]) -> Dict[str, Any]:
        """Get comprehensive competitor summary for selected ASINs.
        
        Args:
            project_id: Project ID for filtering
            selected_asins: List of ASINs to analyze
            
        Returns:
            Dict containing competitor summary data
        """
        try:
            logger.info(f"Getting competitor summary for project {project_id}, {len(selected_asins)} ASINs")
            
            # Get product data from product_wide_table
            product_data = await self._get_product_summary_data(selected_asins)
            
            # Get unique review counts from review_aspect_data_view
            review_counts = await self._get_unique_review_counts(project_id, selected_asins)
            
            # Get additional metrics from review_aspect_data_view
            additional_metrics = await self._get_additional_metrics(project_id, selected_asins)
            
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
                    'list_price': product_info.get('list_price_usd'),
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
            logger.error(f"Error in CompetitorSummaryService: {e}", exc_info=True)
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
                product_data[item['platform_id']] = item
            
            logger.info(f"Retrieved product data for {len(product_data)} ASINs")
            return product_data
            
        except Exception as e:
            logger.error(f"Error getting product summary data: {e}")
            return {}

    async def _get_unique_review_counts(self, project_id: str, selected_asins: List[str]) -> Dict[str, int]:
        """Get unique review counts from review_aspect_data_view.
        
        Args:
            project_id: Project ID for filtering
            selected_asins: List of ASINs to get review counts for
            
        Returns:
            Dict mapping ASIN to unique review count
        """
        try:
            # Query the materialized view to get unique review counts
            result = self.supabase.table('review_aspect_data_view').select(
                'product_id, review_id'
            ).eq('project_id', project_id).in_('product_id', selected_asins).execute()
            
            if not result.data:
                logger.warning("No review data found for selected ASINs")
                return {asin: 0 for asin in selected_asins}
            
            # Count unique review_ids per product
            review_counts = {}
            for asin in selected_asins:
                unique_review_ids = set()
                for record in result.data:
                    if record['product_id'] == asin and record['review_id'] is not None:
                        unique_review_ids.add(record['review_id'])
                review_counts[asin] = len(unique_review_ids)
            
            logger.info(f"Calculated unique review counts: {review_counts}")
            return review_counts
            
        except Exception as e:
            logger.error(f"Error getting unique review counts: {e}")
            return {asin: 0 for asin in selected_asins}

    async def _get_additional_metrics(self, project_id: str, selected_asins: List[str]) -> Dict[str, Dict[str, Any]]:
        """Get additional metrics from review_aspect_data_view.
        
        Args:
            project_id: Project ID for filtering
            selected_asins: List of ASINs to get metrics for
            
        Returns:
            Dict mapping ASIN to additional metrics
        """
        try:
            # Get sentiment distribution and category counts
            result = self.supabase.table('review_aspect_data_view').select(
                'product_id, sentiment, category_name'
            ).eq('project_id', project_id).in_('product_id', selected_asins).execute()
            
            if not result.data:
                logger.warning("No additional metrics found for selected ASINs")
                return {asin: {} for asin in selected_asins}
            
            # Calculate metrics per product
            metrics = {}
            for asin in selected_asins:
                product_records = [r for r in result.data if r['product_id'] == asin]
                
                # Count sentiments
                positive_count = len([r for r in product_records if r['sentiment'] == '+'])
                negative_count = len([r for r in product_records if r['sentiment'] == '-'])
                neutral_count = len([r for r in product_records if r['sentiment'] not in ['+', '-']])
                
                # Count unique categories
                unique_categories = len(set(r['category_name'] for r in product_records if r['category_name']))
                
                metrics[asin] = {
                    'positive_aspects': positive_count,
                    'negative_aspects': negative_count,
                    'neutral_aspects': neutral_count,
                    'unique_categories': unique_categories,
                    'total_aspects': len(product_records)
                }
            
            logger.info(f"Calculated additional metrics for {len(metrics)} ASINs")
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting additional metrics: {e}")
            return {asin: {} for asin in selected_asins}

    async def get_matrix_view_data(
        self, 
        project_id: str,
        selected_asins: List[str], 
        aspect_type: str, 
        top_n: int
    ) -> Dict[str, Any]:
        """Get matrix view data for competitor analysis.
        
        Args:
            project_id: Project ID for filtering
            selected_asins: List of ASINs to analyze
            aspect_type: Aspect type filter ("phy_perf" or "use")
            top_n: Number of top aspect categories to include
            
        Returns:
            Dict containing matrix view data
        """
        try:
            logger.info(f"Getting matrix view data for project {project_id}, {len(selected_asins)} ASINs, aspect_type={aspect_type}, top_n={top_n}")
            
            # Map aspect_type to database values
            if aspect_type == "phy_perf":
                db_aspect_types = ["phy", "perf"]
            elif aspect_type == "use":
                db_aspect_types = ["use"]
            else:
                raise ValueError(f"Invalid aspect_type: {aspect_type}")
            
            # Get top aspect categories by total mentions
            top_categories = await self._get_top_aspect_categories(project_id, selected_asins, db_aspect_types, top_n)
            
            if not top_categories:
                logger.warning("No aspect categories found for the given criteria")
                return {
                    'aspect_categories': [],
                    'product_aspect_data': [],
                    'selected_asins': selected_asins,
                    'aspect_type': aspect_type,
                    'total_categories': 0
                }
            
            # Get category information
            category_info = await self._get_category_info([cat['category_pk'] for cat in top_categories])
            
            # Get product aspect data for the top categories
            product_aspect_data = await self._get_product_aspect_data(
                project_id,
                selected_asins, 
                [cat['category_pk'] for cat in top_categories]
            )
            
            # Build response
            aspect_categories = []
            for category in top_categories:
                cat_info = category_info.get(category['category_pk'], {})
                aspect_categories.append({
                    'category_id': category['category_pk'],
                    'category_name': cat_info.get('name', 'Unknown Category'),
                    'definition': cat_info.get('definition', ''),
                    'total_mentions': category['total_mentions']
                })
            
            # Group product aspect data by ASIN
            grouped_product_data = {}
            for data in product_aspect_data:
                asin = data['asin']
                if asin not in grouped_product_data:
                    grouped_product_data[asin] = {
                        'asin': asin,
                        'aspect_data': []
                    }
                
                grouped_product_data[asin]['aspect_data'].append({
                    'category_id': data['category_id'],
                    'total_mentions': data['total_mentions'],
                    'positive_mentions': data['positive_mentions'],
                    'negative_mentions': data['negative_mentions'],
                    'unique_reviews': data['unique_reviews']
                })
            
            # Convert to list format
            final_product_data = list(grouped_product_data.values())
            
            result = {
                'aspect_categories': aspect_categories,
                'product_aspect_data': final_product_data,
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

    async def _get_top_aspect_categories(
        self, 
        project_id: str,
        selected_asins: List[str], 
        aspect_types: List[str], 
        top_n: int
    ) -> List[Dict[str, Any]]:
        """Get top aspect categories by total mentions.
        
        Args:
            project_id: Project ID for filtering
            selected_asins: List of ASINs to analyze
            aspect_types: List of aspect types to include
            top_n: Number of top categories to return
            
        Returns:
            List of top categories with total mentions
        """
        try:
            # Query review_aspect_data_view to get category statistics
            result = self.supabase.table('review_aspect_data_view').select(
                'category_pk, category_name, aspect_type'
            ).eq('project_id', project_id).in_('product_id', selected_asins).in_('aspect_type', aspect_types).execute()
            
            if not result.data:
                logger.warning("No matrix review data found for the given criteria")
                return []
            
            # Calculate total mentions per category
            category_mentions = {}
            for record in result.data:
                category_pk = record['category_pk']
                if category_pk not in category_mentions:
                    category_mentions[category_pk] = {
                        'category_pk': category_pk,
                        'category_name': record['category_name'],
                        'total_mentions': 0
                    }
                category_mentions[category_pk]['total_mentions'] += 1
            
            # Sort by total mentions and get top N
            sorted_categories = sorted(
                category_mentions.values(),
                key=lambda x: x['total_mentions'],
                reverse=True
            )[:top_n]
            
            logger.info(f"Found {len(sorted_categories)} top categories with mentions ranging from {sorted_categories[-1]['total_mentions'] if sorted_categories else 0} to {sorted_categories[0]['total_mentions'] if sorted_categories else 0}")
            return sorted_categories
            
        except Exception as e:
            logger.error(f"Error getting top aspect categories: {e}")
            return []

    async def _get_category_info(self, category_pks: List[int]) -> Dict[int, Dict[str, Any]]:
        """Get category information for given category PKs.
        
        Args:
            category_pks: List of category primary keys
            
        Returns:
            Dict mapping category_pk to category info
        """
        try:
            result = self.supabase.table('review_analysis_aspect_categories').select(
                'category_pk, name, definition'
            ).in_('category_pk', category_pks).eq('stage', 'final').execute()
            
            if not result.data:
                logger.warning("No category information found")
                return {}
            
            category_info = {}
            for record in result.data:
                category_info[record['category_pk']] = {
                    'name': record['name'],
                    'definition': record['definition']
                }
            
            logger.info(f"Retrieved category info for {len(category_info)} categories")
            return category_info
            
        except Exception as e:
            logger.error(f"Error getting category info: {e}")
            return {}

    async def _get_product_aspect_data(
        self, 
        project_id: str,
        selected_asins: List[str], 
        category_pks: List[int]
    ) -> List[Dict[str, Any]]:
        """Get product aspect data for given ASINs and categories.
        
        Args:
            project_id: Project ID for filtering
            selected_asins: List of ASINs to analyze
            category_pks: List of category primary keys
            
        Returns:
            List of product aspect data
        """
        try:
            # Query review_aspect_data_view for detailed aspect data
            result = self.supabase.table('review_aspect_data_view').select(
                'product_id, category_pk, sentiment, review_id'
            ).eq('project_id', project_id).in_('product_id', selected_asins).in_('category_pk', category_pks).execute()
            
            if not result.data:
                logger.warning("No product aspect data found")
                return []
            
            # Group data by product and category
            product_category_data = {}
            for record in result.data:
                asin = record['product_id']
                category_pk = record['category_pk']
                sentiment = record['sentiment']
                review_id = record['review_id']
                
                key = (asin, category_pk)
                if key not in product_category_data:
                    product_category_data[key] = {
                        'asin': asin,
                        'category_id': category_pk,
                        'total_mentions': 0,
                        'positive_mentions': 0,
                        'negative_mentions': 0,
                        'unique_reviews': set()
                    }
                
                product_category_data[key]['total_mentions'] += 1
                if sentiment == '+':
                    product_category_data[key]['positive_mentions'] += 1
                elif sentiment == '-':
                    product_category_data[key]['negative_mentions'] += 1
                
                if review_id:
                    product_category_data[key]['unique_reviews'].add(review_id)
            
            # Convert to list format
            product_aspect_data = []
            for data in product_category_data.values():
                product_aspect_data.append({
                    'asin': data['asin'],
                    'category_id': data['category_id'],
                    'total_mentions': data['total_mentions'],
                    'positive_mentions': data['positive_mentions'],
                    'negative_mentions': data['negative_mentions'],
                    'unique_reviews': len(data['unique_reviews'])
                })
            
            logger.info(f"Generated product aspect data for {len(product_aspect_data)} product-category combinations")
            return product_aspect_data
            
        except Exception as e:
            logger.error(f"Error getting product aspect data: {e}")
            return [] 