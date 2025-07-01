"""Amazon Category Fetch Orchestrator - Main Coordinator"""

import asyncio
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
import sys
sys.path.insert(0, str(current_dir))

# 添加项目根目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from core.database.connection import get_supabase_service_client

# 直接导入本地模块
from models import FetchConfig, RunStatus
from category_config import CategoryFetcherConfig
from category_repository import CategoryRepository
from category_fetcher import CategoryFetcher
from progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class CategoryFetchOrchestrator:
    """Amazon类别获取编排器"""
    
    def __init__(self):
        """初始化编排器"""
        supabase_client = get_supabase_service_client()
        self.repository = CategoryRepository(supabase_client)
        
    async def start_new_fetch(self, config: Optional[FetchConfig] = None) -> Dict[str, Any]:
        """
        开始新的获取任务
        
        Args:
            config: 获取配置，如果为None则使用默认配置
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            if config is None:
                config = FetchConfig()
            
            # 创建获取器
            fetcher = CategoryFetcher(config)
            
            # 开始获取
            result = await fetcher.start_fetch()
            
            if result["success"]:
                return {
                    "success": True,
                    "message": "Category fetch started successfully",
                    "run_id": result["run_id"],
                    "config": {
                        "domain": config.amazon_domain,
                        "target_category": config.target_category,
                        "max_depth": config.max_depth,
                        "api_delay": config.api_delay_seconds
                    }
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unknown error occurred")
                }
                
        except Exception as e:
            logger.error(f"Error starting new fetch: {e}")
            return {"success": False, "error": str(e)}
    
    async def resume_fetch(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        恢复获取任务
        
        Args:
            run_id: 运行ID，如果为None则恢复最新的运行
            
        Returns:
            Dict[str, Any]: 操作结果
        """
        try:
            # 如果没有指定run_id，查找最新的运行
            if run_id is None:
                run_id = self._find_latest_run()
                if run_id is None:
                    return {"success": False, "error": "No existing runs found to resume"}
            
            # 加载运行配置
            config = await self._load_run_config(run_id)
            if config is None:
                return {"success": False, "error": f"Could not load configuration for run {run_id}"}
            
            # 创建获取器并恢复
            fetcher = CategoryFetcher(config)
            result = await fetcher.resume_fetch(run_id)
            
            if result["success"]:
                return {
                    "success": True,
                    "message": f"Resumed fetch for run {run_id}",
                    "run_id": run_id
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Failed to resume fetch")
                }
                
        except Exception as e:
            logger.error(f"Error resuming fetch: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_run_status(self, run_id: Optional[str] = None) -> Dict[str, Any]:
        """
        获取运行状态
        
        Args:
            run_id: 运行ID，如果为None则获取最新运行的状态
            
        Returns:
            Dict[str, Any]: 运行状态
        """
        try:
            # 如果没有指定run_id，查找最新的运行
            if run_id is None:
                run_id = self._find_latest_run()
                if run_id is None:
                    return {"success": False, "error": "No runs found"}
            
            # 加载进度跟踪器
            tracker = ProgressTracker(run_id)
            if not tracker.load_existing_run():
                return {"success": False, "error": f"Could not load run {run_id}"}
            
            # 获取当前快照
            snapshot = tracker.get_current_snapshot()
            
            return {
                "success": True,
                "run_id": run_id,
                "status": snapshot
            }
            
        except Exception as e:
            logger.error(f"Error getting run status: {e}")
            return {"success": False, "error": str(e)}
    
    async def list_runs(self) -> Dict[str, Any]:
        """
        列出所有运行
        
        Returns:
            Dict[str, Any]: 运行列表
        """
        try:
            runs_dir = CategoryFetcherConfig.RUNS_DIR
            if not runs_dir.exists():
                return {"success": True, "runs": []}
            
            runs = []
            for run_dir in runs_dir.iterdir():
                if run_dir.is_dir():
                    run_info = await self._get_run_info(run_dir.name)
                    if run_info:
                        runs.append(run_info)
            
            # 按开始时间排序（最新的在前）
            runs.sort(key=lambda x: x.get("started_at", ""), reverse=True)
            
            return {"success": True, "runs": runs}
            
        except Exception as e:
            logger.error(f"Error listing runs: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_category_statistics(self) -> Dict[str, Any]:
        """
        获取类别统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            stats = await self.repository.get_category_statistics()
            return {"success": True, "statistics": stats}
            
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}")
            return {"success": False, "error": str(e)}
    
    async def test_api_connection(self) -> Dict[str, Any]:
        """
        测试API连接
        
        Returns:
            Dict[str, Any]: 连接测试结果
        """
        try:
            from api_client import RainforestCategoryAPI
            
            api_client = RainforestCategoryAPI()
            success = api_client.test_connection()
            
            return {
                "success": success,
                "message": "API connection successful" if success else "API connection failed"
            }
            
        except Exception as e:
            logger.error(f"Error testing API connection: {e}")
            return {"success": False, "error": str(e)}
    
    def _generate_run_id(self, domain: str) -> str:
        """
        生成运行ID
        
        Args:
            domain: 亚马逊域名
            
        Returns:
            str: 运行ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_short = domain.replace("amazon.", "").replace(".com", "").replace(".co.", "")
        return f"run_{domain_short}_{timestamp}"
    
    def _find_latest_run(self) -> Optional[str]:
        """
        查找最新的运行
        
        Returns:
            Optional[str]: 最新运行的ID，如果没有则返回None
        """
        try:
            runs_dir = CategoryFetcherConfig.RUNS_DIR
            if not runs_dir.exists():
                return None
            
            # 获取所有运行目录，按修改时间排序
            run_dirs = [d for d in runs_dir.iterdir() if d.is_dir()]
            if not run_dirs:
                return None
            
            latest_run = max(run_dirs, key=lambda d: d.stat().st_mtime)
            return latest_run.name
            
        except Exception as e:
            logger.error(f"Error finding latest run: {e}")
            return None
    
    async def _load_run_config(self, run_id: str) -> Optional[FetchConfig]:
        """
        加载运行配置
        
        Args:
            run_id: 运行ID
            
        Returns:
            Optional[FetchConfig]: 配置对象，如果失败则返回None
        """
        try:
            config_file = CategoryFetcherConfig.get_config_file_path(run_id)
            if not config_file.exists():
                return None
            
            import json
            with open(config_file, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
            
            # 从保存的数据重建FetchConfig
            fetch_run_data = config_data.get("fetch_run", {})
            config_dict = fetch_run_data.get("config", {})
            
            return FetchConfig(
                amazon_domain=config_dict.get("amazon_domain", CategoryFetcherConfig.DEFAULT_DOMAIN),
                api_delay_seconds=config_dict.get("api_delay_seconds", CategoryFetcherConfig.DEFAULT_API_DELAY),
                max_retries=config_dict.get("max_retries", CategoryFetcherConfig.DEFAULT_MAX_RETRIES),
                max_depth=config_dict.get("max_depth", CategoryFetcherConfig.DEFAULT_MAX_DEPTH),
                skip_existing=config_dict.get("skip_existing", CategoryFetcherConfig.DEFAULT_SKIP_EXISTING),
                target_category=config_dict.get("target_category")
            )
            
        except Exception as e:
            logger.error(f"Error loading run config for {run_id}: {e}")
            return None
    
    async def _get_run_info(self, run_id: str) -> Optional[Dict[str, Any]]:
        """
        获取运行信息摘要
        
        Args:
            run_id: 运行ID
            
        Returns:
            Optional[Dict[str, Any]]: 运行信息，如果失败则返回None
        """
        try:
            config = await self._load_run_config(run_id)
            if not config:
                return None
            
            run_dir = CategoryFetcherConfig.get_run_directory(run_id)
            progress_file = CategoryFetcherConfig.get_progress_file_path(run_id)
            
            # 获取基本信息
            run_info = {
                "run_id": run_id,
                "domain": config.amazon_domain,
                "target_category": config.target_category,
                "created_at": datetime.fromtimestamp(run_dir.stat().st_ctime).isoformat(),
                "modified_at": datetime.fromtimestamp(run_dir.stat().st_mtime).isoformat(),
                "has_progress": progress_file.exists()
            }
            
            # 如果有进度文件，尝试解析状态
            if progress_file.exists():
                try:
                    tracker = ProgressTracker(run_id)
                    if tracker.load_existing_run() and tracker.fetch_run:
                        run_info.update({
                            "status": tracker.fetch_run.status.value,
                            "started_at": tracker.fetch_run.started_at.isoformat(),
                            "total_categories": tracker.fetch_run.total_categories,
                            "processed_categories": tracker.fetch_run.processed_categories,
                            "failed_categories": tracker.fetch_run.failed_categories,
                            "api_calls": tracker.fetch_run.api_calls_made
                        })
                        
                        if tracker.fetch_run.completed_at:
                            run_info["completed_at"] = tracker.fetch_run.completed_at.isoformat()
                            run_info["duration_seconds"] = tracker.fetch_run.duration_seconds
                        
                except Exception as e:
                    logger.debug(f"Could not parse progress for {run_id}: {e}")
            
            return run_info
            
        except Exception as e:
            logger.error(f"Error getting run info for {run_id}: {e}")
            return None 