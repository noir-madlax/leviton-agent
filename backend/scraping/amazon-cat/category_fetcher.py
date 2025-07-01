"""Category Fetcher - Core Fetching Logic"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
import sys
sys.path.insert(0, str(current_dir))

from models import (
    CategoryInfo, FetchConfig, RunStatus, CategoryFetchStatus, 
    CategoryHierarchy, APIResponse
)
from api_client import RainforestCategoryAPI
from category_repository import CategoryRepository
from progress_tracker import ProgressTracker
from category_config import CategoryFetcherConfig


logger = logging.getLogger(__name__)


class CategoryFetcher:
    """核心类别获取器"""
    
    def __init__(self, config: FetchConfig):
        """
        初始化类别获取器
        
        Args:
            config: 获取配置
        """
        self.config = config
        self.run_id = None  # 将在start_fetch时设置
        
        # 添加项目根目录到Python路径
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))
        
        # 获取数据库客户端
        from core.database.connection import get_supabase_service_client
        supabase_client = get_supabase_service_client()
        self.repository = CategoryRepository(supabase_client)
        
        # 初始化组件
        self.api_client = RainforestCategoryAPI(
            delay_seconds=config.api_delay_seconds
        )
        self.hierarchy = CategoryHierarchy(root_categories=[])
        
        # 运行状态
        self.is_running = False
        self.should_stop = False
        self.request_id: Optional[int] = None
        
        logger.info("Initialized CategoryFetcher")
    
    async def start_fetch(self, target_category: Optional[str] = None) -> Dict[str, Any]:
        """
        开始获取类别
        
        Args:
            target_category: 指定的目标类别名称（可选）
            
        Returns:
            Dict[str, Any]: 获取结果
        """
        if self.is_running:
            return {"success": False, "error": "Fetcher is already running"}
        
        self.is_running = True
        self.should_stop = False
        
        try:
            # 生成run_id
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            domain_short = self.config.amazon_domain.replace("amazon.", "").replace(".com", "").replace(".co.", "")
            self.run_id = f"run_{domain_short}_{timestamp}"
            
            # 初始化进度跟踪器
            self.progress_tracker = ProgressTracker(self.run_id)
            
            # 初始化运行
            await self._initialize_run()
            
            # 开始获取流程
            if target_category:
                result = await self._fetch_specific_category(target_category)
            else:
                result = await self._fetch_all_categories()
            
            # 在结果中包含run_id
            result["run_id"] = self.run_id
            
            # 完成运行
            await self._finalize_run(result["success"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error in category fetch: {e}")
            await self._finalize_run(False, str(e))
            return {"success": False, "error": str(e)}
        
        finally:
            self.is_running = False
    
    async def resume_fetch(self, run_id: str) -> Dict[str, Any]:
        """
        恢复之前中断的获取
        
        Args:
            run_id: 要恢复的运行ID
            
        Returns:
            Dict[str, Any]: 恢复结果
        """
        if self.is_running:
            return {"success": False, "error": "Fetcher is already running"}
        
        self.is_running = True
        self.should_stop = False
        
        try:
            # 设置run_id并初始化进度跟踪器
            self.run_id = run_id
            self.progress_tracker = ProgressTracker(self.run_id)
            
            # 加载现有运行状态
            if not self.progress_tracker.load_existing_run():
                return {"success": False, "error": "No existing run found to resume"}
            
            self.progress_tracker.update_progress("Resuming fetch from previous state")
            
            # 重建层级结构
            await self._rebuild_hierarchy()
            
            # 根据配置继续获取
            if self.config.target_category:
                result = await self._fetch_specific_category(self.config.target_category)
            else:
                result = await self._fetch_all_categories()
            
            # 在结果中包含run_id
            result["run_id"] = self.run_id
            
            # 完成运行
            await self._finalize_run(result["success"])
            
            return result
            
        except Exception as e:
            logger.error(f"Error resuming fetch: {e}")
            await self._finalize_run(False, str(e))
            return {"success": False, "error": str(e)}
        
        finally:
            self.is_running = False
    
    async def stop_fetch(self):
        """停止获取"""
        self.should_stop = True
        self.progress_tracker.update_progress("Stop requested by user")
        logger.info("Category fetch stop requested")
    
    async def _initialize_run(self):
        """初始化运行"""
        from models import FetchRun
        
        # 创建获取运行记录
        fetch_run = FetchRun(
            run_id=self.run_id,
            domain=self.config.amazon_domain,
            status=RunStatus.INITIALIZING,
            started_at=datetime.now(),
            config=self.config
        )
        
        # 初始化进度跟踪器
        self.progress_tracker.initialize_run(fetch_run)
        
        # 创建数据库记录
        config_data = {
            "domain": self.config.amazon_domain,
            "api_delay": self.config.api_delay_seconds,
            "max_retries": self.config.max_retries,
            "max_depth": self.config.max_depth,
            "skip_existing": self.config.skip_existing,
            "target_category": self.config.target_category
        }
        
        self.request_id = await self.repository.create_fetch_request(self.run_id, config_data)
        
        # 确保API连接正常
        if not self.api_client.test_connection():
            raise Exception("Failed to connect to Rainforest API")
        
        self.progress_tracker.update_run_status(RunStatus.RUNNING)
        logger.info("Run initialization completed")
    
    async def _fetch_all_categories(self) -> Dict[str, Any]:
        """获取所有类别"""
        try:
            self.progress_tracker.update_progress("Starting to fetch all categories")
            
            # 获取根级别类别
            root_categories = await self._fetch_root_categories()
            if not root_categories:
                return {"success": False, "error": "Failed to fetch root categories"}
            
            self.progress_tracker.add_categories(root_categories)
            self.progress_tracker.update_progress(f"Found {len(root_categories)} root categories")
            
            # 逐个处理根类别
            success_count = 0
            failed_count = 0
            
            for root_category in root_categories:
                if self.should_stop:
                    break
                
                try:
                    await self._fetch_category_tree(root_category)
                    success_count += 1
                    self.progress_tracker.increment_processed_count()
                    
                except Exception as e:
                    logger.error(f"Failed to fetch tree for {root_category.name}: {e}")
                    self.progress_tracker.update_category_status(
                        root_category.category_id, 
                        CategoryFetchStatus.FAILED, 
                        str(e)
                    )
                    failed_count += 1
                    self.progress_tracker.increment_failed_count()
            
            total_categories = len(self.hierarchy.category_map)
            
            return {
                "success": True,
                "total_categories": total_categories,
                "root_categories": len(root_categories),
                "success_count": success_count,
                "failed_count": failed_count,
                "api_calls": self.progress_tracker.fetch_run.api_calls_made if self.progress_tracker.fetch_run else 0
            }
            
        except Exception as e:
            logger.error(f"Error in fetch_all_categories: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fetch_specific_category(self, category_name: str) -> Dict[str, Any]:
        """获取指定类别的树"""
        try:
            self.progress_tracker.update_progress(f"Starting to fetch category: {category_name}")
            
            # 获取根级别类别
            root_categories = await self._fetch_root_categories()
            if not root_categories:
                return {"success": False, "error": "Failed to fetch root categories"}
            
            # 查找目标类别
            target_category = None
            for category in root_categories:
                if category.name.lower() == category_name.lower():
                    target_category = category
                    break
            
            if not target_category:
                available_categories = [cat.name for cat in root_categories]
                return {
                    "success": False, 
                    "error": f"Category '{category_name}' not found. Available: {available_categories}"
                }
            
            self.progress_tracker.add_categories([target_category])
            self.progress_tracker.update_progress(f"Found target category: {target_category.name}")
            
            # 获取目标类别树
            await self._fetch_category_tree(target_category)
            
            total_categories = len(self.hierarchy.category_map)
            
            return {
                "success": True,
                "target_category": target_category.name,
                "total_categories": total_categories,
                "api_calls": self.progress_tracker.fetch_run.api_calls_made if self.progress_tracker.fetch_run else 0
            }
            
        except Exception as e:
            logger.error(f"Error in fetch_specific_category: {e}")
            return {"success": False, "error": str(e)}
    
    async def _fetch_root_categories(self) -> List[CategoryInfo]:
        """获取根级别类别"""
        try:
            self.progress_tracker.update_progress("Fetching root categories")
            
            # 调用API获取根类别
            api_response = self.api_client.get_root_categories(domain=self.config.amazon_domain)
            self.progress_tracker.increment_api_calls()
            
            # 保存API响应
            await self._save_api_response(api_response, "root_categories")
            
            if not api_response.success:
                raise Exception(f"API call failed: {api_response.error_message}")
            
            # 解析类别
            category_data_list = self.api_client.parse_categories_from_response(api_response)
            
            # 转换为CategoryInfo对象
            root_categories = []
            for cat_data in category_data_list:
                category = CategoryInfo(
                    category_id=cat_data["category_id"],
                    name=cat_data["name"],
                    level=1,
                    parent_id=None,
                    link=cat_data.get("link"),
                    status=CategoryFetchStatus.PENDING
                )
                root_categories.append(category)
                self.hierarchy.add_category(category)
            
            logger.info(f"Fetched {len(root_categories)} root categories")
            return root_categories
            
        except Exception as e:
            logger.error(f"Error fetching root categories: {e}")
            raise
    
    async def _fetch_category_tree(self, root_category: CategoryInfo):
        """递归获取类别树"""
        try:
            self.progress_tracker.update_progress(
                f"Processing category tree: {root_category.name}",
                root_category.category_id
            )
            
            # 使用栈进行深度优先遍历
            stack = [root_category]
            
            while stack and not self.should_stop:
                current_category = stack.pop()
                
                # 检查是否已达到最大深度
                if current_category.level >= self.config.max_depth:
                    self.progress_tracker.update_category_status(
                        current_category.category_id, 
                        CategoryFetchStatus.SKIPPED,
                        "Max depth reached"
                    )
                    continue
                
                # 检查是否跳过已存在的类别
                if self.config.skip_existing and await self.repository.category_exists(current_category.category_id):
                    self.progress_tracker.update_category_status(
                        current_category.category_id, 
                        CategoryFetchStatus.SKIPPED,
                        "Already exists in database"
                    )
                    continue
                
                # 更新当前类别状态
                self.progress_tracker.update_category_status(
                    current_category.category_id, 
                    CategoryFetchStatus.PROCESSING
                )
                
                # 获取子类别
                children = await self._fetch_category_children(current_category)
                
                if children:
                    # 添加子类别到层级结构
                    self.progress_tracker.add_categories(children)
                    
                    # 将子类别添加到栈中（逆序以保持顺序）
                    stack.extend(reversed(children))
                    
                    # 更新当前类别的子类别计数
                    current_category.children_count = len(children)
                
                # 保存当前类别到数据库
                if await self.repository.save_category(current_category, self.config.amazon_domain):
                    self.progress_tracker.update_category_status(
                        current_category.category_id, 
                        CategoryFetchStatus.COMPLETED
                    )
                else:
                    self.progress_tracker.update_category_status(
                        current_category.category_id, 
                        CategoryFetchStatus.FAILED,
                        "Failed to save to database"
                    )
                
                self.progress_tracker.increment_processed_count()
                
                # 小延迟避免过快处理
                await asyncio.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error in category tree fetch for {root_category.name}: {e}")
            self.progress_tracker.update_category_status(
                root_category.category_id, 
                CategoryFetchStatus.FAILED,
                str(e)
            )
            raise
    
    async def _fetch_category_children(self, parent_category: CategoryInfo) -> List[CategoryInfo]:
        """获取指定类别的子类别"""
        try:
            retry_count = 0
            max_retries = self.config.max_retries
            
            while retry_count <= max_retries:
                try:
                    # 调用API获取子类别
                    api_response = self.api_client.get_category_children(
                        parent_id=parent_category.category_id, 
                        domain=self.config.amazon_domain
                    )
                    self.progress_tracker.increment_api_calls()
                    
                    # 保存API响应
                    await self._save_api_response(api_response, f"category_{parent_category.category_id}")
                    
                    if api_response.success:
                        # 解析子类别
                        category_data_list = self.api_client.parse_categories_from_response(api_response)
                        
                        children = []
                        for cat_data in category_data_list:
                            child_category = CategoryInfo(
                                category_id=cat_data["category_id"],
                                name=cat_data["name"],
                                level=parent_category.level + 1,
                                parent_id=parent_category.category_id,
                                link=cat_data.get("link"),
                                status=CategoryFetchStatus.PENDING
                            )
                            children.append(child_category)
                            self.hierarchy.add_category(child_category)
                        
                        logger.debug(f"Found {len(children)} children for {parent_category.name}")
                        return children
                    
                    else:
                        raise Exception(f"API call failed: {api_response.error_message}")
                
                except Exception as e:
                    retry_count += 1
                    if retry_count <= max_retries:
                        wait_time = retry_count * 2  # 指数退避
                        logger.warning(f"Retry {retry_count}/{max_retries} for {parent_category.name} after {wait_time}s: {e}")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Failed to fetch children for {parent_category.name} after {max_retries} retries: {e}")
                        raise
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching children for {parent_category.name}: {e}")
            raise
    
    async def _save_api_response(self, api_response: APIResponse, filename: str):
        """保存API响应到文件"""
        try:
            raw_api_dir = CategoryFetcherConfig.get_raw_api_directory(self.run_id)
            file_path = raw_api_dir / f"{filename}.json"
            
            self.api_client.save_response_to_file(api_response, file_path)
            
        except Exception as e:
            logger.error(f"Error saving API response for {filename}: {e}")
    
    async def _rebuild_hierarchy(self):
        """重建类别层级结构（用于恢复）"""
        try:
            # 从数据库加载已存在的类别
            existing_categories = await self.repository.get_root_categories()
            
            for category in existing_categories:
                self.hierarchy.add_category(category)
                
                # 递归加载子类别
                await self._load_category_children(category)
            
            logger.info(f"Rebuilt hierarchy with {len(self.hierarchy.category_map)} categories")
            
        except Exception as e:
            logger.error(f"Error rebuilding hierarchy: {e}")
    
    async def _load_category_children(self, parent_category: CategoryInfo):
        """递归加载类别的子类别"""
        try:
            children = await self.repository.get_category_children(parent_category.category_id)
            
            for child in children:
                self.hierarchy.add_category(child)
                await self._load_category_children(child)
                
        except Exception as e:
            logger.error(f"Error loading children for {parent_category.name}: {e}")
    
    async def _finalize_run(self, success: bool, error_message: Optional[str] = None):
        """完成运行"""
        try:
            if success:
                self.progress_tracker.update_run_status(RunStatus.COMPLETED)
                self.progress_tracker.update_progress("Category fetch completed successfully")
                
                if self.request_id:
                    await self.repository.update_fetch_request_status(
                        self.request_id, 
                        "completed",
                        {
                            "total_categories": len(self.hierarchy.category_map),
                            "api_calls_made": self.progress_tracker.fetch_run.api_calls_made if self.progress_tracker.fetch_run else 0
                        }
                    )
            else:
                self.progress_tracker.update_run_status(RunStatus.FAILED)
                self.progress_tracker.update_progress(f"Category fetch failed: {error_message}")
                
                if self.request_id:
                    await self.repository.update_fetch_request_status(
                        self.request_id, 
                        "failed",
                        {"error_message": error_message}
                    )
            
            # 生成最终统计
            stats = await self.repository.get_category_statistics()
            logger.info(f"Final statistics: {stats}")
            
        except Exception as e:
            logger.error(f"Error finalizing run: {e}")
    
    def get_progress_file_path(self) -> Path:
        """获取进度文件路径"""
        return self.progress_tracker.progress_file 