"""Project business logic service."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
import sys
import asyncio

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import get_supabase_client
from ..models import ProjectCreateRequest, Project, ProjectCreateResponse
from categories.services import CategoryService

# 导入产品细分相关模块
from product_segment.models import StartSegmentationRequest
from product_segment.services.db_product_segmentation import DatabaseProductSegmentationService
from product_segment.repositories.product_segment_assignment_repository import ProductSegmentRepository
from product_segment.repositories.product_segment_run_repository import SegmentationRunRepository
from product_segment.repositories.product_segment_taxonomy_repository import ProductTaxonomyRepository

# 导入评论分析相关模块
from review_analysis.models import ReviewAnalysisRequest
from review_analysis.services.db_review_analysis import DatabaseReviewAnalysisService
from review_analysis import review_analysis_config as ra_cfg

logger = logging.getLogger(__name__)


class ProjectService:
    """Service for project management business logic."""
    
    def __init__(self):
        self.supabase = get_supabase_client()
    
    async def create_project(self, request: ProjectCreateRequest) -> ProjectCreateResponse:
        """Create a new project with ASIN extraction and segmentation."""
        try:
            # 1. Extract ASINs based on filters
            filtered_asins = await self._extract_asins_from_filters(request.filters)
            
            # 2. Calculate statistics
            stats = await self._calculate_project_stats(filtered_asins, request.filters)
            
            # 3. Calculate review analysis estimates for accurate display
            review_estimates = await self._calculate_review_analysis_estimate(filtered_asins)
            
            # 4. Create project record with segmentation fields
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
                "total_reviews": int(stats["total_reviews"]),  # This is total reviews in dataset
                "avg_monthly_sales": float(stats["avg_monthly_sales"]),
                "status": "active",
                "segmentation_status": "pending",
                "segmentation_started_at": datetime.utcnow().isoformat(),
                # Add review analysis estimates
                "estimated_reviews_to_analyze": review_estimates['estimated_reviews_to_analyze'],
                "estimated_llm_calls": review_estimates['estimated_llm_calls_extraction']
            }
            
            # 4. Save to database
            result = self.supabase.table('projects').insert(project_data).execute()
            
            if not result.data:
                raise Exception("Failed to create project")
            
            created_project = result.data[0]
            
            # 5. Trigger segmentation processing (async)
            if filtered_asins and request.filters.categories:
                await self._process_project_segmentation(
                    created_project["id"],
                    filtered_asins,
                    request.filters.categories[0]
                )
            
            # 6. Return response
            return ProjectCreateResponse(
                id=created_project["id"],
                project_name=created_project["project_name"],
                selected_product_asins=created_project["selected_product_asins"],
                total_products=created_project["total_products"],
                total_brands=created_project["total_brands"],
                total_reviews=created_project["total_reviews"],
                avg_monthly_sales=float(created_project["avg_monthly_sales"]),
                status=created_project["status"],
                segmentation_status=created_project["segmentation_status"]
            )
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def _process_project_segmentation(self, project_id: str, product_ids: List[str], category: str):
        """处理项目的产品细分（异步）"""
        try:
            # 1. 创建segment运行，关联项目
            segmentation_service = self._get_segmentation_service()
            
            # 注意：这里的product_ids实际上是ASIN字符串，需要从platform_id获取实际的product_id
            # 暂时使用ASIN字符串，后续在segmentation service中处理
            segmentation_request = StartSegmentationRequest(
                product_ids=product_ids,  # 保持字符串格式，在segmentation中处理
                product_category=category,
                project_id=project_id
            )
            
            run_id = await segmentation_service.create_run(segmentation_request)
            
            # 2. 更新项目关联
            self.supabase.table('projects').update({
                "segmentation_run_id": run_id,
                "segmentation_status": "processing"
            }).eq('id', project_id).execute()
            
            # 3. 执行细分处理
            await segmentation_service.execute_run(run_id)
            
            # 4. 更新完成状态和耗时
            await self._complete_segmentation(project_id)
            
        except Exception as e:
            logger.error(f"Error in project segmentation: {e}")
            await self._fail_segmentation(project_id, str(e))

    def _get_segmentation_service(self) -> DatabaseProductSegmentationService:
        """获取产品细分服务实例"""
        run_repo = SegmentationRunRepository(self.supabase)
        assignment_repo = ProductSegmentRepository(self.supabase)
        taxonomy_repo = ProductTaxonomyRepository(self.supabase)
        
        return DatabaseProductSegmentationService(
            run_repo=run_repo,
            segment_repo=assignment_repo,
            taxonomy_repo=taxonomy_repo,
            title_fetcher=self._get_product_title
        )

    def _get_product_title(self, product_id: int) -> str:
        """从product_wide_table获取产品标题"""
        try:
            result = self.supabase.table('product_wide_table')\
                .select('title')\
                .eq('id', product_id)\
                .single()\
                .execute()
            
            return result.data.get('title', f'Product {product_id}') if result.data else f'Product {product_id}'
        except Exception as e:
            logger.warning(f"Failed to get title for product {product_id}: {e}")
            return f'Product {product_id}'

    async def _complete_segmentation(self, project_id: str):
        """记录细分完成时间和耗时，并触发review analysis"""
        try:
            # 获取开始时间和项目信息
            project = self.supabase.table('projects')\
                .select('segmentation_started_at, selected_product_asins, selected_categories')\
                .eq('id', project_id)\
                .single().execute()
            
            if project.data and project.data['segmentation_started_at']:
                started_at = datetime.fromisoformat(project.data['segmentation_started_at'].replace('Z', '+00:00'))
                completed_at = datetime.now(timezone.utc)  # 使用带时区的时间
                duration_seconds = int((completed_at - started_at).total_seconds())
                
                self.supabase.table('projects').update({
                    "segmentation_completed_at": completed_at.isoformat(),
                    "segmentation_duration_seconds": duration_seconds,
                    "segmentation_status": "completed",
                    "review_analysis_status": "pending",
                    "review_analysis_started_at": completed_at.isoformat()
                }).eq('id', project_id).execute()
                
                logger.info(f"Project {project_id} segmentation completed in {duration_seconds} seconds")
                
                # 触发review analysis
                if project.data.get('selected_product_asins') and project.data.get('selected_categories'):
                    await self._process_project_review_analysis(
                        project_id,
                        project.data['selected_product_asins'],
                        project.data['selected_categories'][0] if project.data['selected_categories'] else "Unknown"
                    )
        except Exception as e:
            logger.error(f"Error completing segmentation for project {project_id}: {e}")

    async def _fail_segmentation(self, project_id: str, error_message: str):
        """记录细分失败状态"""
        try:
            self.supabase.table('projects').update({
                "segmentation_status": "failed"
            }).eq('id', project_id).execute()
            
            logger.error(f"Project {project_id} segmentation failed: {error_message}")
        except Exception as e:
            logger.error(f"Error recording segmentation failure for project {project_id}: {e}")

    async def _process_project_review_analysis(self, project_id: str, product_ids: List[str], category: str):
        """处理项目的评论分析（异步）"""
        try:
            logger.info(f"Starting review analysis for project {project_id} with {len(product_ids)} products")
            
            # 1. 更新状态为处理中
            self.supabase.table('projects').update({
                "review_analysis_status": "processing"
            }).eq('id', project_id).execute()
            
            # 2. 创建review analysis请求
            review_service = DatabaseReviewAnalysisService()
            review_request = ReviewAnalysisRequest(
                project_id=project_id,
                product_ids=product_ids,  # ASINs
                product_category=category
            )
            
            # 3. 执行review analysis
            analysis_id = await review_service.analyse(review_request)
            
            # 4. 更新完成状态
            await self._complete_review_analysis(project_id, analysis_id)
            
        except Exception as e:
            logger.error(f"Error in project review analysis: {e}")
            await self._fail_review_analysis(project_id, str(e))

    async def _complete_review_analysis(self, project_id: str, analysis_id: str):
        """记录review analysis完成"""
        try:
            # 获取开始时间
            project = self.supabase.table('projects')\
                .select('review_analysis_started_at')\
                .eq('id', project_id)\
                .single().execute()
            
            if project.data and project.data['review_analysis_started_at']:
                started_at = datetime.fromisoformat(project.data['review_analysis_started_at'].replace('Z', '+00:00'))
                completed_at = datetime.now(timezone.utc)
                duration_seconds = int((completed_at - started_at).total_seconds())
                
                self.supabase.table('projects').update({
                    "review_analysis_completed_at": completed_at.isoformat(),
                    "review_analysis_duration_seconds": duration_seconds,
                    "review_analysis_status": "completed",
                    "review_analysis_id": analysis_id
                }).eq('id', project_id).execute()
                
                logger.info(f"Project {project_id} review analysis completed in {duration_seconds} seconds")
        except Exception as e:
            logger.error(f"Error completing review analysis for project {project_id}: {e}")

    async def _fail_review_analysis(self, project_id: str, error_message: str):
        """记录review analysis失败状态"""
        try:
            self.supabase.table('projects').update({
                "review_analysis_status": "failed"
            }).eq('id', project_id).execute()
            
            logger.error(f"Project {project_id} review analysis failed: {error_message}")
        except Exception as e:
            logger.error(f"Error recording review analysis failure for project {project_id}: {e}")

    async def _extract_asins_from_filters(self, filters) -> List[str]:
        """Extract platform ID list based on project filters.
        
        CRITICAL: Must match the exact logic used in get_data_confirmation_data_by_category_id()
        to ensure consistency between preview and saved project.
        """
        try:
            # 🔥 关键修复：使用与get_data_confirmation_data_by_category_id()完全相同的逻辑
            # 如果有category_id，优先使用category_id过滤逻辑
            if hasattr(filters, 'category_id') and filters.category_id:
                return await self._extract_asins_by_category_id(filters)
            
            # 原有逻辑作为fallback（向后兼容）
            return await self._extract_asins_by_category_name(filters)
            
        except Exception as e:
            logger.error(f"Error extracting ASINs: {e}")
            raise
    
    async def _extract_asins_by_category_id(self, filters) -> List[str]:
        """Extract ASINs using category_id - 与get_data_confirmation_data_by_category_id()完全相同的逻辑"""
        try:
            # Get category level to determine which field to query
            category_level = None
            if filters.category_id:
                # Get category level from amazon_categories table
                category_result = self.supabase.table('amazon_categories')\
                    .select('level')\
                    .eq('category_id', filters.category_id)\
                    .single()\
                    .execute()
                
                if category_result.data:
                    category_level = category_result.data['level']
                    logger.info(f"Category ID {filters.category_id} found at level {category_level}")
                else:
                    logger.warning(f"Category ID {filters.category_id} not found in amazon_categories table")
                    return []
            
            # Build filtered query using category_l{level}_id field - 与get_data_confirmation_data_by_category_id()完全相同
            query = self.supabase.table('product_wide_table').select('platform_id, monthly_sales_volume')
            
            # Apply base filters
            query = query.neq('category', None).neq('brand', None)
            
            # Apply category filter using appropriate level field
            if category_level and filters.category_id:
                category_field = f'category_l{category_level}_id'
                query = query.eq(category_field, filters.category_id)
                logger.info(f"Filtering by {category_field} = {filters.category_id}")
            
            # Apply other filters
            if filters.brands:
                query = query.in_('brand', filters.brands)
            
            if filters.sources:
                query = query.in_('source', filters.sources)
            
            # Execute query to get all filtered data
            result = query.execute()
            
            if not result.data:
                return []
            
            # Apply sales ranking filter in Python (与get_data_confirmation_data_by_category_id()完全相同)
            if filters.top_sales_count:
                # Filter out products with no sales volume (NULL or 0)
                products_with_sales = [
                    row for row in result.data 
                    if row.get('monthly_sales_volume') is not None and row['monthly_sales_volume'] > 0
                ]
                
                # Sort by sales volume (descending)
                sorted_products = sorted(
                    products_with_sales,
                    key=lambda x: x['monthly_sales_volume'] or 0,
                    reverse=True
                )
                
                # Take top N products
                top_products = sorted_products[:filters.top_sales_count]
                
                # Extract platform IDs
                platform_ids = [row['platform_id'] for row in top_products if row.get('platform_id')]
                
                logger.info(f"ASIN extraction by category_id: filtered {len(result.data)} -> {len(products_with_sales)} with sales -> top {len(top_products)} selected")
                
            else:
                # No top sales filter, use all filtered products
                platform_ids = [row['platform_id'] for row in result.data if row.get('platform_id')]
            
            return list(set(platform_ids))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting ASINs by category_id: {e}")
            raise
    
    async def _extract_asins_by_category_name(self, filters) -> List[str]:
        """Extract ASINs using category names - 原有逻辑作为fallback"""
        try:
            # Build query - get all necessary fields for filtering
            query = self.supabase.table('product_wide_table').select('platform_id, monthly_sales_volume')
            
            # Apply base filters (match data confirmation logic)
            query = query.neq('category', None).neq('brand', None)
            
            # Apply user filters
            if filters.categories:
                query = query.in_('category', filters.categories)
            
            if filters.brands:
                query = query.in_('brand', filters.brands)
            
            if filters.sources:
                query = query.in_('source', filters.sources)
            
            # Execute query to get all filtered data
            result = query.execute()
            
            if not result.data:
                return []
            
            # Apply sales ranking filter in Python (matches data confirmation logic)
            if filters.top_sales_count:
                # Filter out products with no sales volume (NULL or 0)
                products_with_sales = [
                    row for row in result.data 
                    if row.get('monthly_sales_volume') is not None and row['monthly_sales_volume'] > 0
                ]
                
                # Sort by sales volume (descending)
                sorted_products = sorted(
                    products_with_sales,
                    key=lambda x: x['monthly_sales_volume'] or 0,
                    reverse=True
                )
                
                # Take top N products
                top_products = sorted_products[:filters.top_sales_count]
                
                # Extract platform IDs
                platform_ids = [row['platform_id'] for row in top_products if row.get('platform_id')]
                
                logger.info(f"ASIN extraction by category_name: filtered {len(result.data)} -> {len(products_with_sales)} with sales -> top {len(top_products)} selected")
                
            else:
                # No top sales filter, use all filtered products
                platform_ids = [row['platform_id'] for row in result.data if row.get('platform_id')]
            
            return list(set(platform_ids))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error extracting ASINs by category_name: {e}")
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
            
            # Calculate actual reviews from product_reviews table instead of reviews_count field
            product_asins = [str(p['platform_id']) for p in products if p.get('platform_id')]
            total_reviews = 0
            if product_asins:
                review_count_result = self.supabase.table('product_reviews')\
                    .select('review_id', count='exact')\
                    .in_('product_id', product_asins)\
                    .execute()
                total_reviews = review_count_result.count or 0
            
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
            
            # 处理数据类型转换
            projects = []
            for project_data in result.data:
                # 确保datetime字段格式正确
                if project_data.get('created_at'):
                    if isinstance(project_data['created_at'], str):
                        project_data['created_at'] = datetime.fromisoformat(project_data['created_at'].replace('Z', '+00:00'))
                else:
                    project_data['created_at'] = datetime.utcnow()
                
                if project_data.get('updated_at'):
                    if isinstance(project_data['updated_at'], str):
                        project_data['updated_at'] = datetime.fromisoformat(project_data['updated_at'].replace('Z', '+00:00'))
                else:
                    project_data['updated_at'] = project_data['created_at']
                
                # 处理可选的datetime字段
                for field in ['segmentation_started_at', 'segmentation_completed_at']:
                    if project_data.get(field) and isinstance(project_data[field], str):
                        project_data[field] = datetime.fromisoformat(project_data[field].replace('Z', '+00:00'))
                
                # 确保必需字段有默认值
                project_data.setdefault('total_products', 0)
                project_data.setdefault('total_brands', 0)
                project_data.setdefault('total_reviews', 0)
                project_data.setdefault('avg_monthly_sales', 0.0)
                project_data.setdefault('selected_categories', [])
                project_data.setdefault('selected_sources', [])
                project_data.setdefault('selected_brands', [])
                project_data.setdefault('selected_product_asins', [])
                
                projects.append(Project(**project_data))
            
            return projects
            
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
            
            # Calculate actual reviews from product_reviews table instead of reviews_count field
            product_asins = [str(row['platform_id']) for row in final_products if row.get('platform_id')]
            actual_review_count = 0
            if product_asins:
                review_count_result = self.supabase.table('product_reviews')\
                    .select('review_id', count='exact')\
                    .in_('product_id', product_asins)\
                    .execute()
                actual_review_count = review_count_result.count or 0
            
            total_reviews = actual_review_count  # Use actual count instead of reviews_count field
            
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
            
            # Calculate review analysis estimates
            review_estimates = await self._calculate_review_analysis_estimate(product_asins)
            
            return {
                'availableCategories': available_categories,
                'availableSources': available_sources,
                'availableBrands': available_brands,
                'stats': {
                    'totalProducts': total_products,
                    'totalBrands': total_brands,
                    'totalReviews': total_reviews,  # Total reviews in database
                    'avgMonthlySales': avg_monthly_sales,
                    'sources': source_stats,
                    'categories': category_stats,
                    'brands': brand_stats,
                    # 🚀 Review analysis estimates (no sampling)
                    'estimatedReviewsToAnalyze': review_estimates['estimated_reviews_to_analyze'],
                    'estimatedLlmCalls': review_estimates['estimated_llm_calls_extraction']
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

    async def get_data_confirmation_data_by_category_id(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get data confirmation data for Step2 with category ID filter.
        Uses hierarchical category_l{level}_id fields for direct querying.
        """
        try:
            # Get category level to determine which field to query
            category_level = None
            if filters and filters.get('category_id'):
                # Get category level from amazon_categories table
                category_result = self.supabase.table('amazon_categories')\
                    .select('level')\
                    .eq('category_id', filters['category_id'])\
                    .single()\
                    .execute()
                
                if category_result.data:
                    category_level = category_result.data['level']
                    logger.info(f"Category ID {filters['category_id']} found at level {category_level}")
                else:
                    logger.warning(f"Category ID {filters['category_id']} not found in amazon_categories table")
                    return self._get_empty_data_structure()
            
            # Build filtered query using category_l{level}_id field
            query = self.supabase.table('product_wide_table').select(
                'category, source, brand, platform_id, title, price_usd, monthly_sales_volume, estimated_revenue, reviews_count'
            ).neq('category', None).neq('brand', None)
            
            # Apply category filter using appropriate level field
            if category_level and filters.get('category_id'):
                category_field = f'category_l{category_level}_id'
                query = query.eq(category_field, filters['category_id'])
                logger.info(f"Filtering by {category_field} = {filters['category_id']}")
            
            # Apply other filters
            if filters:
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
            
            # Convert and clean data (same as original method)
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
            
            # Get available options from all data for this category
            all_options_query = self.supabase.table('product_wide_table').select(
                'category, source, brand'
            ).neq('category', None).neq('brand', None)
            
            if category_level and filters.get('category_id'):
                category_field = f'category_l{category_level}_id'
                all_options_query = all_options_query.eq(category_field, filters['category_id'])
            
            all_options_result = all_options_query.execute()
            all_options_data = all_options_result.data if all_options_result.data else []
            
            available_categories = sorted(list(set(row['category'] for row in all_options_data if row['category'])))
            available_sources = sorted(list(set(row['source'] for row in all_options_data if row['source'])))
            available_brands = sorted(list(set(row['brand'] for row in all_options_data if row['brand'])))
            
            # Calculate statistics
            total_products = len(final_products)
            total_brands = len(set(row['brand'] for row in final_products if row.get('brand')))
            
            # Calculate actual reviews from product_reviews table instead of reviews_count field
            product_asins = [str(row['platform_id']) for row in final_products if row.get('platform_id')]
            actual_review_count = 0
            if product_asins:
                review_count_result = self.supabase.table('product_reviews')\
                    .select('review_id', count='exact')\
                    .in_('product_id', product_asins)\
                    .execute()
                actual_review_count = review_count_result.count or 0
            
            total_reviews = actual_review_count  # Use actual count instead of reviews_count field
            
            # Calculate review analysis estimates (no sampling)
            review_estimates = await self._calculate_review_analysis_estimate(product_asins)
            
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
                    'totalReviews': total_reviews,  # Now shows actual reviews from product_reviews table
                    'avgMonthlySales': avg_monthly_sales,
                    'sources': source_stats,
                    'categories': category_stats,
                    'brands': brand_stats,
                    # 🚀 Review analysis estimates (no sampling)
                    'estimatedReviewsToAnalyze': review_estimates['estimated_reviews_to_analyze'],
                    'estimatedLlmCalls': review_estimates['estimated_llm_calls_extraction']
                },
                'topProducts': top_products
            }
            
        except Exception as e:
            logger.error(f"Error getting data confirmation data by category ID: {str(e)}")
            return self._get_empty_data_structure()
    
    def _get_empty_data_structure(self):
        """Return empty data structure for error cases."""
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

    async def get_project_progress(self, project_id: str) -> Dict[str, Any]:
        """Get project processing progress and status."""
        try:
            # 获取项目基本信息
            project_result = self.supabase.table('projects')\
                .select('*')\
                .eq('id', project_id)\
                .single()\
                .execute()
            
            if not project_result.data:
                raise ValueError(f"Project {project_id} not found")
            
            project = project_result.data
            
            # 基础进度信息
            progress = {
                "project_id": project_id,
                "project_name": project["project_name"],
                "status": project.get("status", "unknown"),
                "segmentation_status": project.get("segmentation_status", "pending"),
                "created_at": project.get("created_at"),
                "segmentation_started_at": project.get("segmentation_started_at"),
                "segmentation_completed_at": project.get("segmentation_completed_at"),
                "segmentation_duration_seconds": project.get("segmentation_duration_seconds"),
                "total_products": project.get("total_products", 0),
                "steps": []
            }
            
            # 步骤1: 项目创建
            step1 = {
                "step": "project_creation",
                "name": "Project Creation",
                "status": "completed" if project.get("created_at") else "pending",
                "started_at": project.get("created_at"),
                "completed_at": project.get("created_at"),
                "description": f"Created project with {project.get('total_products', 0)} products"
            }
            progress["steps"].append(step1)
            
            # 步骤2: ASIN提取
            step2 = {
                "step": "asin_extraction", 
                "name": "Product Selection",
                "status": "completed" if project.get("selected_product_asins") else "pending",
                "started_at": project.get("created_at"),
                "completed_at": project.get("created_at"),
                "description": f"Extracted {len(project.get('selected_product_asins', []))} product ASINs"
            }
            progress["steps"].append(step2)
            
            # 步骤3: 产品细分
            segmentation_status = project.get("segmentation_status", "pending")
            step3_status = "pending"
            step3_description = "Waiting to start product segmentation"
            
            if segmentation_status == "processing":
                step3_status = "in_progress"
                step3_description = "Processing product segmentation with AI"
            elif segmentation_status == "completed":
                step3_status = "completed"
                duration = project.get("segmentation_duration_seconds", 0)
                step3_description = f"Completed product segmentation in {duration} seconds"
            elif segmentation_status == "failed":
                step3_status = "failed"
                step3_description = "Product segmentation failed"
            
            step3 = {
                "step": "product_segmentation",
                "name": "Product Segmentation", 
                "status": step3_status,
                "started_at": project.get("segmentation_started_at"),
                "completed_at": project.get("segmentation_completed_at"),
                "description": step3_description
            }
            progress["steps"].append(step3)
            
            # 如果有segmentation_run_id，获取详细的细分进度
            if project.get("segmentation_run_id"):
                try:
                    run_result = self.supabase.table('product_segment_runs')\
                        .select('*')\
                        .eq('id', project["segmentation_run_id"])\
                        .single()\
                        .execute()
                    
                    if run_result.data:
                        run_data = run_result.data
                        stage = run_data.get("stage", "init")
                        
                        # 🔥 获取详细的产品分配进度 - 批次级别信息
                        assignments_result = self.supabase.table('product_segment_assignments')\
                            .select('product_id, segment_name', count='exact')\
                            .eq('run_id', project["segmentation_run_id"])\
                            .execute()
                        
                        total_products_in_run = assignments_result.count or 0
                        completed_assignments = 0
                        
                        if assignments_result.data:
                            # 计算已完成分配的产品数量（有segment_name的）
                            completed_assignments = len([
                                a for a in assignments_result.data 
                                if a.get('segment_name') and a['segment_name'] != '__UNASSIGNED__'
                            ])
                        
                        # 细分的子步骤 - 增加批次进度信息
                        if stage == "completed":
                            # 全部完成时才显示所有步骤为完成
                            sub_steps = [
                                {"name": f"Extraction ({total_products_in_run} products)", "status": "completed"},
                                {"name": "Consolidation", "status": "completed"},
                                {"name": f"Refinement ({completed_assignments}/{total_products_in_run} assigned)", "status": "completed"}
                            ]
                            step3_description = f"Completed product segmentation: {completed_assignments}/{total_products_in_run} products assigned to segments"
                        else:
                            # 处理中时，显示详细的批次进度
                            extraction_status = "completed" if stage in ["consolidation", "refinement", "completed"] else ("in_progress" if stage == "extraction" else "pending")
                            consolidation_status = "completed" if stage in ["refinement", "completed"] else ("in_progress" if stage == "consolidation" else "pending")
                            refinement_status = "completed" if stage == "completed" else ("in_progress" if stage == "refinement" else "pending")
                            
                            sub_steps = [
                                {
                                    "name": f"Extraction ({total_products_in_run} products)",
                                    "status": extraction_status
                                },
                                {
                                    "name": "Consolidation", 
                                    "status": consolidation_status
                                },
                                {
                                    "name": f"Refinement ({completed_assignments}/{total_products_in_run} assigned)",
                                    "status": refinement_status
                                }
                            ]
                            
                            # 根据当前阶段更新描述
                            if stage == "extraction":
                                step3_description = f"Extracting product features from {total_products_in_run} products"
                            elif stage == "consolidation":
                                step3_description = f"Consolidating product taxonomies"
                            elif stage == "refinement":
                                step3_description = f"Refining product assignments: {completed_assignments}/{total_products_in_run} products assigned"
                            else:
                                step3_description = f"Processing product segmentation: {completed_assignments}/{total_products_in_run} products assigned"
                        
                        step3["sub_steps"] = sub_steps
                        step3["current_stage"] = stage
                        step3["description"] = step3_description
                        
                except Exception as e:
                    logger.warning(f"Failed to get segmentation run details: {e}")
            
            # 步骤4: 评论分析 - 增加详细进度信息
            review_analysis_status = project.get("review_analysis_status", "pending")
            step4_status = "pending"
            step4_description = "Waiting for segmentation completion"
            
            if segmentation_status == "completed":
                if review_analysis_status == "pending":
                    step4_status = "pending"
                    step4_description = "Waiting to start review analysis"
                elif review_analysis_status == "processing":
                    step4_status = "in_progress"
                    
                    # 🔥 获取评论分析的详细进度信息
                    if project.get("review_analysis_id"):
                        try:
                            # 获取评论分析的进度统计
                            analysis_result = self.supabase.table('review_analysis_runs')\
                                .select('*')\
                                .eq('id', project["review_analysis_id"])\
                                .single()\
                                .execute()
                            
                            if analysis_result.data:
                                analysis_data = analysis_result.data
                                stage = analysis_data.get("stage", "init")
                                
                                # 获取评论数量统计
                                total_reviews = project.get("total_reviews", 0)
                                processed_reviews = 0
                                
                                # 查询已处理的评论数量
                                if project.get("selected_product_asins"):
                                    processed_result = self.supabase.table('review_analysis_aspect_occurrences')\
                                        .select('review_id', count='exact')\
                                        .eq('analysis_id', project["review_analysis_id"])\
                                        .execute()
                                    
                                    processed_reviews = processed_result.count or 0
                                
                                step4_description = f"Processing review analysis: {processed_reviews}/{total_reviews} reviews analyzed ({stage.replace('_', ' ')})"
                                
                                # 添加评论分析的子步骤
                                extraction_status = "completed" if stage in ["consolidation", "completed"] else ("in_progress" if stage == "extraction" else "pending")
                                consolidation_status = "completed" if stage == "completed" else ("in_progress" if stage == "consolidation" else "pending")
                                
                                step4_sub_steps = [
                                    {
                                        "name": f"Aspect Extraction ({processed_reviews}/{total_reviews} reviews)",
                                        "status": extraction_status
                                    },
                                    {
                                        "name": "Category Consolidation",
                                        "status": consolidation_status
                                    }
                                ]
                                
                                step4["sub_steps"] = step4_sub_steps
                                step4["current_stage"] = stage
                                
                        except Exception as e:
                            logger.warning(f"Failed to get review analysis details: {e}")
                            step4_description = "Processing review analysis with AI"
                    else:
                        step4_description = "Processing review analysis with AI"
                        
                elif review_analysis_status == "completed":
                    step4_status = "completed"
                    duration = project.get("review_analysis_duration_seconds", 0)
                    total_reviews = project.get("total_reviews", 0)
                    step4_description = f"Completed review analysis: {total_reviews} reviews processed in {duration} seconds"
                elif review_analysis_status == "failed":
                    step4_status = "failed"
                    step4_description = "Review analysis failed"
            elif segmentation_status == "failed":
                step4_status = "failed"
                step4_description = "Cannot start review analysis due to segmentation failure"
            
            step4 = {
                "step": "review_analysis",
                "name": "Review Analysis",
                "status": step4_status,
                "started_at": project.get("review_analysis_started_at"),
                "completed_at": project.get("review_analysis_completed_at"),
                "description": step4_description
            }
            progress["steps"].append(step4)

            # 步骤5: 数据准备完成
            step5_status = "pending"
            step5_description = "Waiting for all processing to complete"
            
            if review_analysis_status == "completed":
                step5_status = "completed"
                step5_description = "Project ready for analysis"
            elif review_analysis_status == "failed" or segmentation_status == "failed":
                step5_status = "failed"
                step5_description = "Data preparation failed"
            
            step5 = {
                "step": "data_preparation",
                "name": "Data Preparation",
                "status": step5_status,
                "started_at": project.get("review_analysis_completed_at"),
                "completed_at": project.get("review_analysis_completed_at"),
                "description": step5_description
            }
            progress["steps"].append(step5)
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting project progress for {project_id}: {e}")
            raise 

    async def _calculate_review_analysis_estimate(self, product_ids: List[str]) -> Dict[str, Any]:
        """Calculate the estimated number of reviews that will actually be analyzed."""
        try:
            total_estimated_reviews = 0
            total_estimated_llm_calls = 0
            
            if not product_ids:
                return {
                    'estimated_reviews_to_analyze': 0,
                    'estimated_llm_calls_extraction': 0,
                    'sampling_strategy': 'none'
                }
            
            supabase = get_supabase_client()
            
            # Get total review count for all products
            review_result = supabase.table('product_reviews')\
                .select('review_id', count='exact')\
                .in_('product_id', product_ids)\
                .execute()
            
            total_estimated_reviews = review_result.count or 0
            
            # Calculate LLM calls needed
            if total_estimated_reviews > 0:
                total_estimated_llm_calls = (total_estimated_reviews + ra_cfg.REVIEWS_PER_EXTRACTION_PROMPT - 1) // ra_cfg.REVIEWS_PER_EXTRACTION_PROMPT
            
            return {
                'estimated_reviews_to_analyze': total_estimated_reviews,
                'estimated_llm_calls_extraction': total_estimated_llm_calls,
                'sampling_strategy': 'none'  # No sampling applied
            }
            
        except Exception as e:
            logger.error(f"Error calculating review analysis estimate: {e}")
            return {
                'estimated_reviews_to_analyze': 0,
                'estimated_llm_calls_extraction': 0,
                'sampling_strategy': 'none'
            } 