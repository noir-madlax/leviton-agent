"""Project business logic service."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone

from core.database.connection import get_supabase_client
from ..models import ProjectCreateRequest, Project, ProjectCreateResponse

# 导入产品细分相关模块
from product_segment.models import StartSegmentationRequest
from product_segment.services.db_product_segmentation import DatabaseProductSegmentationService
from product_segment.repositories.product_segment_assignment_repository import ProductSegmentRepository
from product_segment.repositories.product_segment_run_repository import SegmentationRunRepository
from product_segment.repositories.product_segment_taxonomy_repository import ProductTaxonomyRepository

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
            
            # 3. Create project record with segmentation fields
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
                "status": "active",
                "segmentation_status": "pending",
                "segmentation_started_at": datetime.utcnow().isoformat()
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
        """记录细分完成时间和耗时"""
        try:
            # 获取开始时间
            project = self.supabase.table('projects')\
                .select('segmentation_started_at')\
                .eq('id', project_id)\
                .single().execute()
            
            if project.data and project.data['segmentation_started_at']:
                started_at = datetime.fromisoformat(project.data['segmentation_started_at'].replace('Z', '+00:00'))
                completed_at = datetime.now(timezone.utc)  # 使用带时区的时间
                duration_seconds = int((completed_at - started_at).total_seconds())
                
                self.supabase.table('projects').update({
                    "segmentation_completed_at": completed_at.isoformat(),
                    "segmentation_duration_seconds": duration_seconds,
                    "segmentation_status": "completed"
                }).eq('id', project_id).execute()
                
                logger.info(f"Project {project_id} segmentation completed in {duration_seconds} seconds")
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

    async def _extract_asins_from_filters(self, filters) -> List[str]:
        """Extract platform ID list based on project filters.
        
        CRITICAL: Must match the exact logic used in get_data_confirmation_data()
        to ensure consistency between preview and saved project.
        """
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
                
                logger.info(f"ASIN extraction: filtered {len(result.data)} -> {len(products_with_sales)} with sales -> top {len(top_products)} selected")
                
            else:
                # No top sales filter, use all filtered products
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
                        
                        # 细分的子步骤 - 修改显示逻辑避免误导用户
                        # 只有当前正在执行的步骤显示为in_progress，其他都显示为pending，直到整个分割完成
                        if stage == "completed":
                            # 全部完成时才显示所有步骤为完成
                            sub_steps = [
                                {"name": "Extraction", "status": "completed"},
                                {"name": "Consolidation", "status": "completed"},
                                {"name": "Refinement", "status": "completed"}
                            ]
                        else:
                            # 处理中时，只显示当前步骤为进行中，其他为等待
                            sub_steps = [
                                {
                                    "name": "Extraction",
                                    "status": "in_progress" if stage == "extraction" else "pending"
                                },
                                {
                                    "name": "Consolidation", 
                                    "status": "in_progress" if stage == "consolidation" else "pending"
                                },
                                {
                                    "name": "Refinement",
                                    "status": "in_progress" if stage == "refinement" else "pending"
                                }
                            ]
                        
                        step3["sub_steps"] = sub_steps
                        step3["current_stage"] = stage
                        
                except Exception as e:
                    logger.warning(f"Failed to get segmentation run details: {e}")
            
            # 步骤4: 数据准备完成
            step4_status = "pending"
            step4_description = "Waiting for segmentation completion"
            
            if segmentation_status == "completed":
                step4_status = "completed"
                step4_description = "Project ready for analysis"
            elif segmentation_status == "failed":
                step4_status = "failed"
                step4_description = "Data preparation failed"
            
            step4 = {
                "step": "data_preparation",
                "name": "Data Preparation",
                "status": step4_status,
                "started_at": project.get("segmentation_completed_at"),
                "completed_at": project.get("segmentation_completed_at"),
                "description": step4_description
            }
            progress["steps"].append(step4)
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting project progress for {project_id}: {e}")
            raise 