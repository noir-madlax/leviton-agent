"""Project business logic service."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

from core.database.connection import get_supabase_client
from ..models import ProjectCreateRequest, Project, ProjectCreateResponse

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project management business logic."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_project(self, request: ProjectCreateRequest) -> ProjectCreateResponse:
        """Create a new project with ASIN extraction."""
        try:
            # 1. Extract ASINs based on filters
            filtered_asins = await self._extract_asins_from_filters(request.filters)
            
            # 2. Calculate statistics
            stats = await self._calculate_project_stats(filtered_asins, request.filters)
            
            # 3. Create project record
            project_data = {
                "project_name": request.project_name,
                "company_name": request.company_name,
                "user_name": request.user_name,
                "description": request.description,
                "selected_categories": request.filters.categories,
                "selected_sources": request.filters.sources,
                "selected_brands": request.filters.brands,
                "selected_product_asins": filtered_asins,
                "top_sales_count": int(request.filters.top_sales_count) if request.filters.top_sales_count else None,
                "total_products": int(stats["total_products"]),
                "total_brands": int(stats["total_brands"]),
                "total_reviews": int(stats["total_reviews"]),
                "avg_monthly_sales": float(stats["avg_monthly_sales"]),
                "status": "active"
            }
            
            # 4. Save to database
            result = self.supabase.table('projects').insert(project_data).execute()
            
            if not result.data:
                raise Exception("Failed to create project")
            
            created_project = result.data[0]
            
            # 5. Return response
            return ProjectCreateResponse(
                id=created_project["id"],
                project_name=created_project["project_name"],
                selected_product_asins=created_project["selected_product_asins"],
                total_products=created_project["total_products"],
                total_brands=created_project["total_brands"],
                total_reviews=created_project["total_reviews"],
                avg_monthly_sales=float(created_project["avg_monthly_sales"]),
                status=created_project["status"]
            )
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def _extract_asins_from_filters(self, filters) -> List[str]:
        """Extract platform ID list based on project filters."""
        try:
            # Build query
            query = self.supabase.table('product_wide_table').select('platform_id')
            
            # Apply filters
            if filters.categories:
                query = query.in_('category', filters.categories)
            
            if filters.brands:
                query = query.in_('brand', filters.brands)
            
            if filters.sources:
                query = query.in_('source', filters.sources)
            
            # Apply sales ranking filter
            if filters.top_sales_count:
                query = query.order('monthly_sales_volume', desc=True).limit(filters.top_sales_count)
            
            # Execute query
            result = query.execute()
            
            if not result.data:
                return []
            
            # Extract platform IDs (ASINs for Amazon, product IDs for other sources)
            platform_ids = [row['platform_id'] for row in result.data if row.get('platform_id')]
            return list(set(platform_ids))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting ASINs: {e}")
            raise
    
    async def _calculate_project_stats(self, asins: List[str], filters) -> dict:
        """Calculate project statistics based on ASIN list."""
        try:
            if not asins:
                return {
                    "total_products": 0,
                    "total_brands": 0,
                    "total_reviews": 0,
                    "avg_monthly_sales": 0.0
                }
            
            # Query product data for statistics
            result = self.supabase.table('product_wide_table').select(
                'platform_id, brand, reviews_count, monthly_sales_volume'
            ).in_('platform_id', asins).execute()
            
            if not result.data:
                return {
                    "total_products": 0,
                    "total_brands": 0,
                    "total_reviews": 0,
                    "avg_monthly_sales": 0.0
                }
            
            products = result.data
            
            # Calculate statistics
            total_products = len(products)
            total_brands = len(set(p['brand'] for p in products if p.get('brand')))
            
            # Handle reviews_count which might be strings like "547.0"
            total_reviews = 0
            for p in products:
                reviews_count = p.get('reviews_count', 0) or 0
                if isinstance(reviews_count, str):
                    try:
                        reviews_count = float(reviews_count)
                    except (ValueError, TypeError):
                        reviews_count = 0
                total_reviews += reviews_count
            
            # Calculate average monthly sales
            sales_volumes = []
            for p in products:
                sales_vol = p.get('monthly_sales_volume', 0) or 0
                if isinstance(sales_vol, str):
                    try:
                        sales_vol = float(sales_vol)
                    except (ValueError, TypeError):
                        sales_vol = 0
                sales_volumes.append(sales_vol)
            
            avg_monthly_sales = sum(sales_volumes) / len(sales_volumes) if sales_volumes else 0.0
            
            return {
                "total_products": int(total_products),
                "total_brands": int(total_brands),
                "total_reviews": int(total_reviews),
                "avg_monthly_sales": float(avg_monthly_sales)
            }
            
        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            raise
    
    async def get_project(self, project_id: str) -> Project:
        """Get project by ID."""
        try:
            result = self.supabase.table('projects').select('*').eq('id', project_id).single().execute()
            
            if not result.data:
                raise Exception(f"Project {project_id} not found")
            
            project_data = result.data
            return Project(**project_data)
            
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            raise
    
    async def list_projects(self) -> List[Project]:
        """List all active projects."""
        try:
            result = self.supabase.table('projects').select('*').eq('status', 'active').order('created_at', desc=True).execute()
            
            if not result.data:
                return []
            
            return [Project(**project) for project in result.data]
            
        except Exception as e:
            logger.error(f"Error listing projects: {e}")
            raise

    async def get_data_confirmation_data(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get data confirmation data for Step2 with optional filters
        """
        try:
            # Get all available options first
            all_options_result = self.supabase.table('product_wide_table').select(
                'category, source, brand'
            ).neq('category', None).neq('brand', None).execute()
            
            if not all_options_result.data:
                all_options_data = []
            else:
                all_options_data = all_options_result.data
            
            available_categories = sorted(list(set(row['category'] for row in all_options_data if row['category'])))
            available_sources = sorted(list(set(row['source'] for row in all_options_data if row['source'])))
            available_brands = sorted(list(set(row['brand'] for row in all_options_data if row['brand'])))
            
            # Build filtered query
            query = self.supabase.table('product_wide_table').select(
                'category, source, brand, platform_id, title, price_usd, monthly_sales_volume, estimated_revenue, reviews_count'
            ).neq('category', None).neq('brand', None)
            
            # Apply filters
            if filters:
                if filters.get('categories'):
                    query = query.in_('category', filters['categories'])
                if filters.get('sources'):
                    query = query.in_('source', filters['sources'])
                if filters.get('brands'):
                    query = query.in_('brand', filters['brands'])
            
            # Execute filtered query
            filtered_result = query.execute()
            
            if not filtered_result.data:
                filtered_data = []
            else:
                filtered_data = filtered_result.data
            
            # Convert and clean data
            for row in filtered_data:
                if row.get('monthly_sales_volume'):
                    try:
                        row['monthly_sales_volume'] = int(float(row['monthly_sales_volume']))
                    except (ValueError, TypeError):
                        row['monthly_sales_volume'] = 0
                if row.get('reviews_count'):
                    try:
                        row['reviews_count'] = int(float(row['reviews_count']))
                    except (ValueError, TypeError):
                        row['reviews_count'] = 0
                if row.get('estimated_revenue'):
                    try:
                        row['estimated_revenue'] = float(row['estimated_revenue'])
                    except (ValueError, TypeError):
                        row['estimated_revenue'] = 0.0
                if row.get('price_usd'):
                    try:
                        row['price_usd'] = float(row['price_usd'])
                    except (ValueError, TypeError):
                        row['price_usd'] = 0.0
            
            # Sort by sales volume
            sorted_products = sorted(
                [row for row in filtered_data if row.get('monthly_sales_volume') is not None and row['monthly_sales_volume'] > 0],
                key=lambda x: x['monthly_sales_volume'] or 0,
                reverse=True
            )
            
            # Apply top sales count filter if specified
            if filters and filters.get('topSalesCount'):
                top_count = int(filters['topSalesCount'])
                if top_count < len(sorted_products):
                    final_products = sorted_products[:top_count]
                else:
                    final_products = filtered_data
            else:
                final_products = filtered_data
            
            # Calculate statistics
            total_products = len(final_products)
            total_brands = len(set(row['brand'] for row in final_products if row.get('brand')))
            total_reviews = sum(row.get('reviews_count', 0) or 0 for row in final_products)
            
            sales_volumes = [row.get('monthly_sales_volume', 0) for row in final_products if row.get('monthly_sales_volume') is not None and row['monthly_sales_volume'] > 0]
            avg_monthly_sales = sum(sales_volumes) / len(sales_volumes) if sales_volumes else 0
            
            # Source statistics
            source_stats = []
            for source in available_sources:
                count = len([row for row in final_products if row.get('source') == source])
                if count > 0:
                    source_stats.append({
                        'name': source,
                        'count': count,
                        'percentage': round((count / total_products) * 100) if total_products > 0 else 0
                    })
            
            # Category statistics
            category_stats = []
            for category in available_categories:
                count = len([row for row in final_products if row.get('category') == category])
                if count > 0:
                    category_stats.append({
                        'name': category,
                        'count': count,
                        'percentage': round((count / total_products) * 100) if total_products > 0 else 0
                    })
            
            # Brand statistics (top 10)
            brand_counts = {}
            for row in final_products:
                brand = row.get('brand')
                if brand:
                    brand_counts[brand] = brand_counts.get(brand, 0) + 1
            
            brand_stats = []
            for brand, count in sorted(brand_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                brand_stats.append({
                    'name': brand,
                    'count': count,
                    'percentage': round((count / total_products) * 100) if total_products > 0 else 0
                })
            
            # Top products for preview (limit to 50)
            top_products = sorted_products[:min(50, len(final_products))]
            
            return {
                'availableCategories': available_categories,
                'availableSources': available_sources,
                'availableBrands': available_brands,
                'stats': {
                    'totalProducts': total_products,
                    'totalBrands': total_brands,
                    'totalReviews': total_reviews,
                    'avgMonthlySales': avg_monthly_sales,
                    'sources': source_stats,
                    'categories': category_stats,
                    'brands': brand_stats
                },
                'topProducts': top_products
            }
            
        except Exception as e:
            logger.error(f"Error getting data confirmation data: {str(e)}")
            # Return empty structure on error
            return {
                'availableCategories': [],
                'availableSources': [],
                'availableBrands': [],
                'stats': {
                    'totalProducts': 0,
                    'totalBrands': 0,
                    'totalReviews': 0,
                    'avgMonthlySales': 0,
                    'sources': [],
                    'categories': [],
                    'brands': []
                },
                'topProducts': []
            } 