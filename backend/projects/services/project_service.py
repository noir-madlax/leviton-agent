"""Project business logic service."""

import logging
import hashlib
from typing import List, Dict, Optional, Any
from datetime import datetime, timezone
from pathlib import Path
import sys
from fastapi import BackgroundTasks

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import get_supabase_client
from ..models import ProjectCreateRequest, Project, ProjectCreateResponse
from core.sse_manager import sse_manager

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
    
    def _calculate_overall_status(self, segmentation_status: str, review_analysis_status: str) -> str:
        """
        Calculate simplified overall status for frontend display.
        
        Args:
            segmentation_status: Current segmentation status
            review_analysis_status: Current review analysis status
            
        Returns:
            overall_status: 'creating', 'ready', or 'failed'
        """
        # Check for failure states first
        if segmentation_status == 'failed' or review_analysis_status == 'failed':
            return 'failed'
        
        # Check if still processing
        if (segmentation_status in ['pending', 'processing'] or 
            review_analysis_status in ['pending', 'processing']):
            return 'creating'
        
        # Both completed successfully
        if segmentation_status == 'completed' and review_analysis_status == 'completed':
            return 'ready'
        
        # Default to creating for any other state
        return 'creating'
    
    async def create_project(self, request: ProjectCreateRequest, background_tasks: BackgroundTasks) -> ProjectCreateResponse:
        """
        Create a new project, and schedule segmentation/analysis as background tasks.
        This method returns immediately after project creation.
        """
        try:
            # 1. Extract ASINs based on filters
            filtered_asins = await self._extract_asins_from_filters(request.filters)
            
            # 2. Calculate statistics
            stats = await self._calculate_project_stats(filtered_asins, request.filters)
            
            # 3. Calculate review analysis estimates for accurate display
            review_estimates = await self._calculate_review_analysis_estimate(filtered_asins)
            
            # 4. Create project record with segmentation fields
            initial_segmentation_status = "pending"
            initial_review_analysis_status = "pending"
            overall_status = self._calculate_overall_status(initial_segmentation_status, initial_review_analysis_status)
            
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
                "overall_status": overall_status,  # Add simplified status
                "segmentation_status": initial_segmentation_status,
                "segmentation_started_at": datetime.utcnow().isoformat(),
                "review_analysis_status": initial_review_analysis_status,  # Initialize review analysis status
                # Add review analysis estimates
                "estimated_reviews_to_analyze": review_estimates['estimated_reviews_to_analyze'],
                "estimated_llm_calls": review_estimates['estimated_llm_calls_extraction']
            }
            
            # 4. Save to database
            result = self.supabase.table('projects').insert(project_data).execute()
            
            if not result.data:
                raise Exception("Failed to create project")
            
            created_project = result.data[0]
            
            # 5. Create user project access if user_uid is provided
            if request.user_uid:
                try:
                    access_result = self.supabase.table('user_project_access').insert({
                        'user_uid': request.user_uid,
                        'project_id': created_project["id"],
                        'access_level': 'admin'
                    }).execute()
                    
                    if access_result.data:
                        logger.info(f"Created user access for {request.user_uid} to project {created_project['id']}")
                    else:
                        logger.warning(f"Failed to create user access for {request.user_uid}")
                except Exception as e:
                    logger.error(f"Error creating user project access: {e}")
                    # Continue with project creation even if access creation fails
            
            # 6. Broadcast initial project creation status
            await self._broadcast_progress_update(created_project["id"])
            
            # 7. Schedule segmentation processing as a background task
            if filtered_asins and request.filters.categories:
                background_tasks.add_task(
                    self._process_project_segmentation,
                    project_id=created_project["id"],
                    product_ids=filtered_asins,
                    category=request.filters.categories[0]
                )
            
            # 8. Return response immediately
            return ProjectCreateResponse(
                id=created_project["id"],
                project_name=created_project["project_name"],
                selected_product_asins=created_project["selected_product_asins"],
                total_products=created_project["total_products"],
                total_brands=created_project["total_brands"],
                total_reviews=created_project["total_reviews"],
                avg_monthly_sales=float(created_project["avg_monthly_sales"]),
                status=created_project["status"],
                overall_status=created_project["overall_status"],
                segmentation_status=created_project["segmentation_status"]
            )
            
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            raise
    
    async def _process_project_segmentation(self, project_id: str, product_ids: List[str], category: str):
        """处理项目的产品细分（异步）"""
        try:
            # 🔥 NEW: Group products by category paths first
            category_groups = await self._group_products_by_category_path(product_ids, category)
            
            if not category_groups:
                logger.warning(f"No category groups found for project {project_id}")
                await self._fail_segmentation(project_id, "No products found in categories")
                return
            
            logger.info(f"Found {len(category_groups)} category groups for project {project_id}")
            
            # Process each category group separately
            segmentation_service = self._get_segmentation_service()
            
            for full_category_path, group_product_ids in category_groups.items():
                # Extract terminal category from full path for segmentation service
                terminal_category = self._extract_terminal_category(full_category_path)
                
                logger.info(f"Processing category group '{full_category_path}' -> terminal category '{terminal_category}' with {len(group_product_ids)} products")
                
                # TODO: product_ids are actually ASIN strings, need to get actual product_id from platform_id
                # TODO: Temporarily using ASIN strings, to be handled later in segmentation service
                
                # TODO: Rename `project_id` in product_segment_* tables to `run_group_id` 
                # to better reflect its purpose of identifying a specific segmentation run group.
                # Create a unique, fixed-length ID for the segmentation run group
                # by hashing the project ID and the terminal category.
                run_group_id_str = f"{project_id}_{full_category_path}"
                run_group_id = hashlib.sha1(run_group_id_str.encode()).hexdigest()
                
                # Create separate segmentation run for each category group
                segmentation_request = StartSegmentationRequest(
                    product_ids=group_product_ids,  # Keep string format, handle in segmentation service
                    product_category=terminal_category,  # Use terminal category as input to segmentation
                    project_id=run_group_id  # Unique hash-based ID for this group
                )
                
                run_id = await segmentation_service.create_run(segmentation_request)
                
                # TODO: Update project association with segmentation run_id
                # TODO: Set segmentation status to "processing" when starting
                
                # Execute segmentation for this category group
                await segmentation_service.execute_run(run_id)
            
            # Update completion status after all groups are processed
            await self._complete_segmentation(project_id)
            
        except Exception as e:
            logger.error(f"Error in project segmentation: {e}")
            await self._fail_segmentation(project_id, str(e))

    async def _group_products_by_category_path(self, product_ids: List[str], category: str) -> Dict[str, List[str]]:
        """
        Group products by their full category path (categories_flat).
        Terminal category is extracted later for segmentation service input.
        
        Returns:
            Dict mapping full_category_path -> List[product_ids]
        """
        try:
            if not product_ids:
                return {}
            
            # Use direct SQL implementation to group by category path
            return await self._group_products_by_category_path_sql(product_ids)
            
        except Exception as e:
            logger.error(f"Error grouping products by category path: {e}")
            # Ultimate fallback: return all products as one group
            return {"Unknown Category": product_ids}
    
    async def _group_products_by_category_path_sql(self, product_ids: List[str]) -> Dict[str, List[str]]:
        """
        Fallback SQL implementation for category path grouping.
        
        Groups products by their full categories_flat path, extracting terminal category
        for segmentation service input.
        
        TODO: Consider caching category groupings for performance optimization
        TODO: Add validation for malformed category paths
        TODO: product_ids are actually ASIN strings, need to get actual product_id from platform_id
        TODO: Temporarily using ASIN strings, to be handled later in segmentation service
        """
        try:
            if not product_ids:
                return {}
            
            # Get product category data from Supabase
            result = self.supabase.table('product_wide_table').select(
                'platform_id, categories_flat'
            ).in_('platform_id', product_ids).execute()
            
            if not result.data:
                return {}
            
            # Group products by full categories_flat path
            groups = {}
            for row in result.data:
                categories_flat = row.get('categories_flat')
                if not categories_flat or not categories_flat.strip():
                    continue
                    
                # Use full categories_flat as the group key
                full_category_path = categories_flat.strip()
                if full_category_path not in groups:
                    groups[full_category_path] = []
                groups[full_category_path].append(row['platform_id'])
            
            logger.info(f"Grouped {len(product_ids)} products into {len(groups)} category groups")
            return groups
            
        except Exception as e:
            logger.error(f"Error in SQL terminal category grouping: {e}")
            # Ultimate fallback: return all products as one group
            return {"Unknown Category": product_ids}

    def _extract_terminal_category(self, full_category_path: str) -> str:
        """
        Extract terminal category from full category path.
        
        Args:
            full_category_path: Full category path like "Home > Electronics > Switches > Dimmer Switches"
            
        Returns:
            Terminal category name (last non-empty part after splitting by '>')
        """
        if not full_category_path or not full_category_path.strip():
            return "Unknown Category"
        
        # Split by '>' and get the last non-empty part
        parts = [part.strip() for part in full_category_path.split('>') if part.strip()]
        if parts:
            return parts[-1]
        
        return "Unknown Category"

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
                .select('segmentation_started_at, selected_product_asins, selected_categories, review_analysis_status')\
                .eq('id', project_id)\
                .single().execute()
            
            if project.data and project.data['segmentation_started_at']:
                # Calculate overall status
                overall_status = self._calculate_overall_status('completed', project.data.get('review_analysis_status', 'pending'))
                
                # Update segmentation completion and overall status
                started_at = datetime.fromisoformat(project.data['segmentation_started_at'].replace('Z', '+00:00'))
                completed_at = datetime.now(timezone.utc)  # 使用带时区的时间
                duration_seconds = int((completed_at - started_at).total_seconds())
                
                self.supabase.table('projects').update({
                    "segmentation_completed_at": completed_at.isoformat(),
                    "segmentation_duration_seconds": duration_seconds,
                    "segmentation_status": "completed",
                    "review_analysis_status": "pending",
                    "review_analysis_started_at": completed_at.isoformat(),
                    "overall_status": overall_status
                }).eq('id', project_id).execute()
                
                logger.info(f"Project {project_id} segmentation completed in {duration_seconds} seconds")
                
                # 推送状态更新
                await self._broadcast_progress_update(project_id)
                
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
            overall_status = self._calculate_overall_status('failed', 'failed')
            
            self.supabase.table('projects').update({
                "segmentation_status": "failed",
                "review_analysis_status": "failed", # If segmentation fails, review analysis also fails
                "overall_status": overall_status
            }).eq('id', project_id).execute()
            
            logger.error(f"Project {project_id} segmentation failed: {error_message}")
            
            # 推送状态更新
            await self._broadcast_progress_update(project_id)
        except Exception as e:
            logger.error(f"Error recording segmentation failure for project {project_id}: {e}")

    async def _process_project_review_analysis(self, project_id: str, product_ids: List[str], category: str):
        """处理项目的评论分析（异步）"""
        run_id = None
        try:
            logger.info(f"Starting review analysis for project {project_id} with {len(product_ids)} products")

            # Get project estimates for the run record
            project_result = self.supabase.table('projects')\
                .select('total_products, estimated_reviews_to_analyze, estimated_llm_calls')\
                .eq('id', project_id)\
                .single().execute()
            project_data = project_result.data or {}

            # 1. 创建 review_analysis_runs 记录
            run_result = self.supabase.table('review_analysis_runs').insert({
                "project_id": project_id,
                "status": "processing",
                "stage": "starting",
                "total_products": project_data.get('total_products'),
                "total_reviews_to_analyze": project_data.get('estimated_reviews_to_analyze'),
                "llm_calls_extraction": project_data.get('estimated_llm_calls') # Initial estimate
            }).execute()

            if not run_result.data:
                raise Exception("Failed to create review analysis run record.")
            
            run_id = run_result.data[0]['id']

            # 2. 更新 projects 表，关联 run_id
            self.supabase.table('projects').update({
                "review_analysis_status": "processing",
                "review_analysis_run_id": run_id
            }).eq('id', project_id).execute()

            await self._broadcast_progress_update(project_id)

            # 3. 定义进度回调函数
            async def progress_callback(progress_data: Dict[str, Any]):
                step_name = progress_data.get("step")
                if not step_name:
                    return
                
                logger.info(f"📈 Review Analysis Progress (Project: {project_id}, Run: {run_id}): {progress_data}")

                # Prepare updates for the main run table
                run_updates = {
                    "stage": step_name,
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Handle batch progress updates from details
                details = progress_data.get("details", {})
                if details:
                    # Update batch progress fields if present
                    if "extraction_batches_done" in details:
                        run_updates["extraction_batches_done"] = details["extraction_batches_done"]
                    if "extraction_batches_total" in details:
                        run_updates["extraction_batches_total"] = details["extraction_batches_total"]
                    if "categorization_batches_done" in details:
                        run_updates["categorization_batches_done"] = details["categorization_batches_done"]
                    if "categorization_batches_total" in details:
                        run_updates["categorization_batches_total"] = details["categorization_batches_total"]
                    if "consolidation_batches_done" in details:
                        run_updates["consolidation_batches_done"] = details["consolidation_batches_done"]
                    if "consolidation_batches_total" in details:
                        run_updates["consolidation_batches_total"] = details["consolidation_batches_total"]
                    # Refinement stage removed - aspects are assigned during categorization and reassigned during consolidation
                
                # Increment processed reviews count if applicable
                if progress_data.get("status") == "in_progress" and step_name == "extraction":
                    run_updates["processed_reviews_count"] = progress_data.get("progress_current", 0)

                # 更新主运行状态
                self.supabase.table('review_analysis_runs').update(run_updates).eq('id', run_id).execute()

                # Upsert 详细进度
                self.supabase.table('review_analysis_progress').upsert({
                    "run_id": run_id,
                    "step_name": step_name,
                    "status": progress_data.get("status"),
                    "progress_current": progress_data.get("progress_current"),
                    "progress_total": progress_data.get("progress_total"),
                    "details": progress_data.get("details"),
                    "updated_at": datetime.now(timezone.utc).isoformat()
                }, on_conflict="run_id,step_name").execute()
                
                # 广播更新到前端
                await self._broadcast_progress_update(project_id)

            # 4. 创建 review analysis 请求并执行
            review_service = DatabaseReviewAnalysisService()
            review_request = ReviewAnalysisRequest(
                project_id=project_id,
                product_ids=product_ids,
                product_category=category
            )
            
            analysis_id = await review_service.analyse(review_request, progress_callback)
            
            # 5. 更新完成状态
            await self._complete_review_analysis(project_id, run_id, analysis_id)
            
        except Exception as e:
            logger.exception(f"Error in project review analysis for project {project_id}: {e}")
            await self._fail_review_analysis(project_id, run_id, str(e))

    async def _complete_review_analysis(self, project_id: str, run_id: int, analysis_id: str):
        """记录评论分析完成状态"""
        try:
            project = self.supabase.table('projects')\
                .select('review_analysis_started_at, segmentation_status')\
                .eq('id', project_id)\
                .single().execute()

            if not project.data or not project.data.get('review_analysis_started_at'):
                logger.warning(f"Project {project_id} has no review analysis start time. Cannot calculate duration.")
                return

            started_at = datetime.fromisoformat(project.data['review_analysis_started_at'].replace('Z', '+00:00'))
            completed_at = datetime.now(timezone.utc)
            duration_seconds = int((completed_at - started_at).total_seconds())

            # Calculate overall status
            segmentation_status = project.data.get('segmentation_status', 'pending')
            overall_status = self._calculate_overall_status(segmentation_status, 'completed')

            # 更新 projects 表
            self.supabase.table('projects').update({
                "review_analysis_status": "completed",
                "review_analysis_completed_at": completed_at.isoformat(),
                "review_analysis_duration_seconds": duration_seconds,
                "overall_status": overall_status
            }).eq('id', project_id).execute()
            
            # 更新 review_analysis_runs 表
            self.supabase.table('review_analysis_runs').update({
                "status": "completed",
                "stage": "completed",
                "processed_reviews_count": self.supabase.table('review_analysis_runs').select('total_reviews_to_analyze').eq('id', run_id).single().execute().data.get('total_reviews_to_analyze', 0), # Mark all as processed on completion
                "completed_at": completed_at.isoformat()
            }).eq('id', run_id).execute()

            logger.info(f"Project {project_id} review analysis completed in {duration_seconds} seconds. Analysis ID: {analysis_id}")
            
            # 推送最终状态
            await self._broadcast_progress_update(project_id)

        except Exception as e:
            logger.error(f"Error completing review analysis for project {project_id}: {e}")

    async def _fail_review_analysis(self, project_id: str, run_id: Optional[int], error_message: str):
        """记录评论分析失败状态"""
        try:
            # Get current segmentation status to calculate overall status
            project = self.supabase.table('projects')\
                .select('segmentation_status')\
                .eq('id', project_id)\
                .single().execute()
            
            segmentation_status = project.data.get('segmentation_status', 'pending') if project.data else 'pending'
            overall_status = self._calculate_overall_status(segmentation_status, 'failed')
            
            # 更新 projects 表
            self.supabase.table('projects').update({
                "review_analysis_status": "failed",
                "overall_status": overall_status
            }).eq('id', project_id).execute()
            
            # 更新 review_analysis_runs 表
            if run_id:
                self.supabase.table('review_analysis_runs').update({
                    "status": "failed",
                    "error_message": error_message,
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }).eq('id', run_id).execute()

            logger.error(f"Project {project_id} review analysis failed: {error_message}")
            
            # 推送状态更新
            await self._broadcast_progress_update(project_id)
        except Exception as e:
            logger.error(f"Error recording review analysis failure for project {project_id}: {e}")

    async def _broadcast_progress_update(self, project_id: str):
        """Broadcast project progress update via SSE."""
        try:
            progress_data = await self.get_project_progress(project_id)
            
            # 🔥 详细日志：记录推送的进度数据
            logger.info(f"📡 Broadcasting progress update for project {project_id}:")
            logger.info(f"  - segmentation_status: {progress_data.get('segmentation_status')}")
            logger.info(f"  - review_analysis_status: {progress_data.get('review_analysis_status')}")
            logger.info(f"  - steps count: {len(progress_data.get('steps', []))}")
            
            # 记录每个步骤的状态
            for i, step in enumerate(progress_data.get('steps', [])):
                logger.info(f"  - Step {i+1}: {step.get('name')} = {step.get('status')}")
            
            await sse_manager.broadcast_to_project(project_id, progress_data)
            logger.info(f"✅ Successfully broadcasted progress update for project {project_id}")
        except Exception as e:
            logger.error(f"❌ Error broadcasting progress update for project {project_id}: {e}")

    async def _apply_multi_level_category_filter(self, query, category_id: str):
        """Apply multi-level category ID filter to a query.
        
        This method applies OR condition to search across all category hierarchy levels:
        category_id, category_l1_id, category_l2_id, category_l3_id, category_l4_id, category_l5_id, category_l6_id
        
        Args:
            query: Supabase query object
            category_id: Amazon category ID to search for
            
        Returns:
            Query object with multi-level category filter applied
        """
        return query.or_(
            f"category_id.eq.{category_id},"
            f"category_l1_id.eq.{category_id},"
            f"category_l2_id.eq.{category_id},"
            f"category_l3_id.eq.{category_id},"
            f"category_l4_id.eq.{category_id},"
            f"category_l5_id.eq.{category_id},"
            f"category_l6_id.eq.{category_id}"
        )

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
        """Extract ASINs using category_id with fallback strategy."""
        try:
            category_id = filters.category_id
            
            # 策略1：使用统一的多层级category ID查询
            query = self.supabase.table('product_wide_table').select('platform_id, monthly_sales_volume')
            query = query.neq('category', None).neq('brand', None)
            
            # Apply multi-level category filter
            query = await self._apply_multi_level_category_filter(query, category_id)
            
            # Apply other filters
            if filters.brands:
                query = query.in_('brand', filters.brands)
            
            if filters.sources:
                query = query.in_('source', filters.sources)
            
            result = query.execute()
            
            if result.data:
                logger.info(f"Found {len(result.data)} products via multi-level category_id match")
                return await self._process_query_results(result.data, filters)
            
            # 策略2：通过category_id获取名称，然后用名称查询category字段
            category_name = await self._get_category_name(category_id)
            if category_name:
                query = self.supabase.table('product_wide_table').select('platform_id, monthly_sales_volume')
                query = query.neq('category', None).neq('brand', None)
                query = query.eq('category', category_name)
                
                # Apply other filters
                if filters.brands:
                    query = query.in_('brand', filters.brands)
                
                if filters.sources:
                    query = query.in_('source', filters.sources)
                
                result = query.execute()
                
                if result.data:
                    logger.info(f"Found {len(result.data)} products via category name match: {category_name}")
                    return await self._process_query_results(result.data, filters)
            
            logger.warning(f"No products found for category_id {category_id}")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting ASINs by category_id: {e}")
            raise
    
    async def _get_category_name(self, category_id: str) -> Optional[str]:
        """获取类别名称"""
        try:
            result = self.supabase.table('amazon_categories')\
                .select('name')\
                .eq('category_id', category_id)\
                .single()\
                .execute()
            return result.data.get('name') if result.data else None
        except Exception as e:
            logger.warning(f"Failed to get category name for {category_id}: {e}")
            return None
    
    async def _process_query_results(self, data: List[Dict], filters) -> List[str]:
        """处理查询结果，应用销量过滤"""
        try:
            # Apply sales ranking filter in Python
            if filters.top_sales_count:
                # Filter out products with no sales volume (NULL or 0)
                products_with_sales = [
                    row for row in data 
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
                
                logger.info(f"Sales filtering: {len(data)} -> {len(products_with_sales)} with sales -> top {len(top_products)} selected")
                
            else:
                # No top sales filter, use all filtered products
                platform_ids = [row['platform_id'] for row in data if row.get('platform_id')]
            
            return list(set(platform_ids))  # Remove duplicates
            
        except Exception as e:
            logger.error(f"Error processing query results: {e}")
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
    
    async def list_projects(self, user_uid: Optional[str] = None) -> List[Project]:
        """List active projects with user access control."""
        try:
            # Get projects based on user access
            if user_uid:
                # Check if user has specific project access permissions
                access_result = self.supabase.table('user_project_access')\
                    .select('project_id, access_level')\
                    .eq('user_uid', user_uid)\
                    .execute()
                
                if access_result.data:
                    # User has specific access permissions - only show those projects
                    allowed_project_ids = [row['project_id'] for row in access_result.data]
                    logger.info(f"User {user_uid} has access to projects: {allowed_project_ids}")
                    result = self.supabase.table('projects')\
                        .select('*')\
                        .eq('status', 'active')\
                        .in_('id', allowed_project_ids)\
                        .order('created_at', desc=True)\
                        .execute()
                else:
                    # No specific permissions found - return empty list for security
                    logger.warning(f"No access permissions found for user UID: {user_uid}")
                    return []
            else:
                # No user UID provided - show all projects (legacy behavior)
                result = self.supabase.table('projects')\
                    .select('*')\
                    .eq('status', 'active')\
                    .order('created_at', desc=True)\
                    .execute()
            
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
        Uses multi-level category hierarchy filter - same logic as project creation.
        """
        try:
            if not filters or not filters.get('category_id'):
                return self._get_empty_data_structure()
            
            category_id = filters['category_id']
            
            # 策略1：使用统一的多层级category ID查询（与项目创建相同逻辑）
            query = self.supabase.table('product_wide_table').select(
                'category, source, brand, platform_id, title, price_usd, monthly_sales_volume, estimated_revenue, reviews_count'
            ).neq('category', None).neq('brand', None)
            
            # Apply multi-level category filter
            query = await self._apply_multi_level_category_filter(query, category_id)
            
            # Apply other filters
            if filters.get('sources'):
                query = query.in_('source', filters['sources'])
            if filters.get('brands'):
                query = query.in_('brand', filters['brands'])
            
            filtered_result = query.execute()
            
            if filtered_result.data:
                logger.info(f"Found {len(filtered_result.data)} products via multi-level category_id match")
                filtered_data = filtered_result.data
            else:
                # 策略2：通过category_id获取名称，然后用名称查询category字段（fallback）
                category_name = await self._get_category_name(category_id)
                if not category_name:
                    logger.warning(f"Category ID {category_id} not found in amazon_categories table")
                    return self._get_empty_data_structure()
                
                query = self.supabase.table('product_wide_table').select(
                    'category, source, brand, platform_id, title, price_usd, monthly_sales_volume, estimated_revenue, reviews_count'
                ).neq('category', None).neq('brand', None)
                query = query.eq('category', category_name)
                
                # Apply other filters
                if filters.get('sources'):
                    query = query.in_('source', filters['sources'])
                if filters.get('brands'):
                    query = query.in_('brand', filters['brands'])
                
                filtered_result = query.execute()
                
                if filtered_result.data:
                    logger.info(f"Found {len(filtered_result.data)} products via category name match: {category_name}")
                    filtered_data = filtered_result.data
                else:
                    logger.warning(f"No products found for category_id {category_id}")
                    return self._get_empty_data_structure()
            
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
            # 使用相同的策略获取可用选项
            all_options_query = self.supabase.table('product_wide_table').select(
                'category, source, brand'
            ).neq('category', None).neq('brand', None)
            all_options_query = all_options_query.eq('category_id', category_id)
            
            all_options_result = all_options_query.execute()
            
            if not all_options_result.data:
                # 策略2：通过category_name获取可用选项
                category_name = await self._get_category_name(category_id)
                if category_name:
                    all_options_query = self.supabase.table('product_wide_table').select(
                        'category, source, brand'
                    ).neq('category', None).neq('brand', None)
                    all_options_query = all_options_query.eq('category', category_name)
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
                "review_analysis_status": project.get("review_analysis_status", "pending"),
                "created_at": project.get("created_at"),
                "segmentation_started_at": project.get("segmentation_started_at"),
                "segmentation_completed_at": project.get("segmentation_completed_at"),
                "segmentation_duration_seconds": project.get("segmentation_duration_seconds"),
                "total_products": project.get("total_products", 0),
                "total_reviews": project.get("total_reviews", 0),
                "estimated_llm_calls": project.get("estimated_llm_calls", 0),
                "steps": []
            }
            
            # 步骤1: 项目创建 - 🔥 修复状态逻辑
            project_created = bool(project.get("created_at"))
            step1 = {
                "step": "project_creation",
                "name": "Project Creation",
                "status": "completed" if project_created else "pending",
                "started_at": project.get("created_at"),
                "completed_at": project.get("created_at") if project_created else None,
                "description": f"Created project with {project.get('total_products', 0)} products"
            }
            progress["steps"].append(step1)
            
            # 🔥 调试日志：记录项目创建状态计算
            logger.debug(f"🔍 Project {project_id} creation status calculation:")
            logger.debug(f"  - created_at: {project.get('created_at')}")
            logger.debug(f"  - project_created: {project_created}")
            logger.debug(f"  - step1 status: {step1['status']}")
            
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
                        
                        # 🔥 获取批次进度信息
                        extraction_batches_done = run_data.get("extraction_batches_done", 0)
                        extraction_batches_total = run_data.get("extraction_batches_total", 0)
                        consolidation_batches_done = run_data.get("consolidation_batches_done", 0)
                        consolidation_batches_total = run_data.get("consolidation_batches_total", 0)
                        # Refinement stage removed from review analysis workflow
                        
                        # 细分的子步骤 - 增加批次进度信息
                        if stage == "completed":
                            # 全部完成时才显示所有步骤为完成
                            sub_steps = [
                                {
                                    "name": f"Extraction ({total_products_in_run} products)", 
                                    "status": "completed",
                                    "description": f"{extraction_batches_done}/{extraction_batches_total} batches" if extraction_batches_total > 0 else "completed"
                                },
                                {
                                    "name": "Consolidation", 
                                    "status": "completed",
                                    "description": f"{consolidation_batches_done}/{consolidation_batches_total} batches" if consolidation_batches_total > 0 else "completed"
                                },
                                {
                                    "name": f"Refinement ({completed_assignments}/{total_products_in_run} assigned)", 
                                    "status": "completed",
                                    "description": "Final assignments completed"
                                }
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
                                    "status": extraction_status,
                                    "description": f"{extraction_batches_done}/{extraction_batches_total} batches" if extraction_batches_total > 0 else ""
                                },
                                {
                                    "name": "Consolidation", 
                                    "status": consolidation_status,
                                    "description": f"{consolidation_batches_done}/{consolidation_batches_total} batches" if consolidation_batches_total > 0 else ""
                                },
                                {
                                    "name": f"Refinement ({completed_assignments}/{total_products_in_run} assigned)",
                                    "status": refinement_status,
                                    "description": "Assigning final segments"
                                }
                            ]
                            
                            # 根据当前阶段更新描述
                            if stage == "extraction":
                                step3_description = f"Extracting product features from {total_products_in_run} products"
                            elif stage == "consolidation":
                                step3_description = "Consolidating product taxonomies"
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
            
            # 获取LLM调用次数估计用于显示
            estimated_llm_calls = project.get("estimated_llm_calls", 0)
            estimated_reviews_to_analyze = project.get("estimated_reviews_to_analyze", 0)
            
            # The main step object, to be populated
            step4 = {
                "step": "review_analysis",
                "name": "Review Analysis",
                "status": step4_status,
                "started_at": project.get("review_analysis_started_at"),
                "completed_at": project.get("review_analysis_completed_at"),
                "description": step4_description
            }

            if segmentation_status == "completed":
                if review_analysis_status == "pending":
                    step4["status"] = "pending"
                    step4["description"] = f"Waiting to start review analysis ({estimated_reviews_to_analyze} reviews)"
                elif review_analysis_status == "processing":
                    step4["status"] = "in_progress"
                    
                    # 🔥 获取评论分析的详细进度信息
                    if project.get("review_analysis_run_id"):
                        try:
                            # 获取主运行状态
                            run_result = self.supabase.table('review_analysis_runs')\
                                .select('status, stage, extraction_batches_done, extraction_batches_total, categorization_batches_done, categorization_batches_total, consolidation_batches_done, consolidation_batches_total')\
                                .eq('id', project["review_analysis_run_id"])\
                                .single().execute()
                            run_data = run_result.data or {}

                            # 获取所有子步骤的进度
                            progress_result = self.supabase.table('review_analysis_progress')\
                                .select('step_name, status, progress_current, progress_total, details')\
                                .eq('run_id', project["review_analysis_run_id"])\
                                .execute()
                            progress_map = {p['step_name']: p for p in progress_result.data} if progress_result.data else {}
                            
                            current_stage = run_data.get("stage", "starting")
                            
                            # 定义所有可能的子步骤 - refinement stage removed
                            all_stages = ["extraction", "categorization", "consolidation"]
                            sub_steps = []
                            total_progress_current = 0
                            total_progress_total = 0

                            for stage_name in all_stages:
                                progress_item = progress_map.get(stage_name, {})
                                status = progress_item.get('status', 'pending')
                                current = progress_item.get('progress_current') or 0
                                total = progress_item.get('progress_total') or 0
                                details = progress_item.get('details', {})
                                eta_seconds = details.get('eta_seconds') if details else None
                                
                                # If the main stage has moved past this one, mark it completed
                                if status == 'pending' and current_stage != stage_name and all_stages.index(current_stage) > all_stages.index(stage_name):
                                    status = 'completed'

                                # 🔥 获取批次进度信息
                                batches_done_field = f"{stage_name}_batches_done"
                                batches_total_field = f"{stage_name}_batches_total"
                                batches_done = run_data.get(batches_done_field, 0) or 0
                                batches_total = run_data.get(batches_total_field, 0) or 0
                                
                                # 构建描述信息
                                description_parts = []
                                if batches_total > 0:
                                    description_parts.append(f"{batches_done}/{batches_total} batches")
                                elif total > 0:
                                    description_parts.append(f"{current}/{total}")
                                    
                                if eta_seconds is not None and status == 'in_progress':
                                    minutes, seconds = divmod(eta_seconds, 60)
                                    description_parts.append(f"ETA: {minutes}m {seconds}s")
                                
                                description = " - ".join(description_parts) if description_parts else ""

                                sub_steps.append({
                                    "name": stage_name.replace('_', ' ').capitalize(),
                                    "status": status,
                                    "description": description
                                })
                                if stage_name == 'extraction':
                                    total_progress_current = current
                                    total_progress_total = total
                            
                            step4["sub_steps"] = sub_steps
                            step4["current_stage"] = current_stage
                            
                            # 更新主描述
                            if total_progress_total > 0:
                                step4["description"] = f"Processing review analysis: {total_progress_current}/{total_progress_total} batches processed in {current_stage.replace('_', ' ')} stage."
                            else:
                                step4["description"] = f"Processing review analysis in {current_stage.replace('_', ' ')} stage."

                        except Exception as e:
                            logger.warning(f"Failed to get review analysis details for run {project.get('review_analysis_run_id')}: {e}")
                            step4["description"] = "Processing review analysis..."
                    else:
                        step4["description"] = "Processing review analysis..."
                        
                elif review_analysis_status == "completed":
                    step4["status"] = "completed"
                    duration = project.get("review_analysis_duration_seconds", 0)
                    llm_calls = project.get("estimated_llm_calls", 0) # Just an estimate
                    num_reviews = project.get("estimated_reviews_to_analyze", 0)
                    step4["description"] = f"Completed review analysis: {num_reviews} reviews processed in {duration}s ({llm_calls} LLM calls used)"
                    
                    # 🔥 即使完成了也显示子步骤详情
                    if project.get("review_analysis_run_id"):
                        try:
                            # 获取主运行状态和批次信息
                            run_result = self.supabase.table('review_analysis_runs')\
                                .select('extraction_batches_done, extraction_batches_total, categorization_batches_done, categorization_batches_total, consolidation_batches_done, consolidation_batches_total')\
                                .eq('id', project["review_analysis_run_id"])\
                                .single().execute()
                            run_data = run_result.data or {}
                            
                            # 获取所有子步骤的进度
                            progress_result = self.supabase.table('review_analysis_progress')\
                                .select('step_name, status, progress_current, progress_total, details')\
                                .eq('run_id', project["review_analysis_run_id"])\
                                .execute()
                            progress_map = {p['step_name']: p for p in progress_result.data} if progress_result.data else {}
                            
                            # 定义所有可能的子步骤 - refinement stage removed  
                            all_stages = ["extraction", "categorization", "consolidation"]
                            sub_steps = []

                            for stage_name in all_stages:
                                progress_item = progress_map.get(stage_name, {})
                                current = progress_item.get('progress_current') or 0
                                total = progress_item.get('progress_total') or 0
                                
                                # 🔥 获取批次进度信息
                                batches_done_field = f"{stage_name}_batches_done"
                                batches_total_field = f"{stage_name}_batches_total"
                                batches_done = run_data.get(batches_done_field, 0) or 0
                                batches_total = run_data.get(batches_total_field, 0) or 0
                                
                                # 已完成的项目，优先显示批次信息
                                if batches_total > 0:
                                    description = f"{batches_done}/{batches_total} batches"
                                elif total > 0:
                                    description = f"{current}/{total}"
                                else:
                                    description = "completed"

                                sub_steps.append({
                                    "name": stage_name.replace('_', ' ').capitalize(),
                                    "status": "completed",
                                    "description": description
                                })
                            
                            step4["sub_steps"] = sub_steps
                            step4["current_stage"] = "completed"
                            
                        except Exception as e:
                            logger.warning(f"Failed to get completed review analysis details for run {project.get('review_analysis_run_id')}: {e}")
                
                elif review_analysis_status == "failed":
                    step4["status"] = "failed"
                    step4["description"] = "Review analysis failed"

            elif segmentation_status == "failed":
                step4["status"] = "failed"
                step4["description"] = "Cannot start, segmentation failed"
            
            progress["steps"].append(step4)

            # 步骤5: 数据准备
            data_preparation_status = "pending"
            step5_description = "Waiting for all processing to complete"
            
            if review_analysis_status == "completed":
                data_preparation_status = "completed"
                step5_description = "Project ready for analysis"
            elif review_analysis_status == "failed" or segmentation_status == "failed":
                data_preparation_status = "failed"
                step5_description = "Data preparation failed"
            
            step5 = {
                "step": "data_preparation",
                "name": "Data Preparation",
                "status": data_preparation_status,
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