"""Category Repository - Database Operations"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from supabase import Client

# 添加当前目录到Python路径
current_dir = Path(__file__).parent
import sys
sys.path.insert(0, str(current_dir))

from models import CategoryInfo, FetchRun, RunStatus, CategoryFetchStatus


logger = logging.getLogger(__name__)


class CategoryRepository:
    """类别数据库操作仓库"""
    
    def __init__(self, supabase_client: Client):
        """
        初始化仓库
        
        Args:
            supabase_client: Supabase客户端
        """
        self.client = supabase_client
    
    async def category_exists(self, category_id: str) -> bool:
        """
        检查类别是否已存在
        
        Args:
            category_id: 类别ID
            
        Returns:
            bool: 类别是否存在
        """
        try:
            result = self.client.table('amazon_categories')\
                .select('id')\
                .eq('category_id', category_id)\
                .execute()
            
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking if category {category_id} exists: {e}")
            return False
    
    async def save_category(self, category: CategoryInfo, domain: str = "amazon.com") -> bool:
        """
        保存类别到数据库
        
        Args:
            category: 类别信息
            domain: 亚马逊域名
            
        Returns:
            bool: 保存是否成功
        """
        try:
            # 构建类别的完整路径
            full_path = await self._build_full_path(category)
            
            category_data = {
                "category_id": category.category_id,
                "name": category.name,
                "parent_category_id": category.parent_id,
                "level": category.level,
                "full_path": full_path,
                "link": category.link
            }
            
            # 使用upsert操作，如果已存在则更新，否则插入
            result = self.client.table('amazon_categories')\
                .upsert(category_data, on_conflict='category_id')\
                .execute()
            
            if result.data:
                logger.debug(f"Successfully saved category: {category.category_id}")
                return True
            else:
                logger.error(f"Failed to save category: {category.category_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error saving category {category.category_id}: {e}")
            return False
    
    async def save_categories_batch(self, categories: List[CategoryInfo], domain: str = "amazon.com") -> Tuple[int, int]:
        """
        批量保存类别
        
        Args:
            categories: 类别列表
            domain: 亚马逊域名
            
        Returns:
            Tuple[int, int]: (成功数量, 失败数量)
        """
        if not categories:
            return 0, 0
        
        success_count = 0
        failed_count = 0
        
        try:
            # 准备批量数据
            batch_data = []
            for category in categories:
                full_path = await self._build_full_path(category)
                category_data = {
                    "category_id": category.category_id,
                    "name": category.name,
                    "parent_category_id": category.parent_id,
                    "level": category.level,
                    "full_path": full_path,
                    "link": category.link
                }
                batch_data.append(category_data)
            
            # 批量插入
            result = self.client.table('amazon_categories')\
                .upsert(batch_data, on_conflict='category_id')\
                .execute()
            
            if result.data:
                success_count = len(result.data)
                logger.info(f"Successfully saved {success_count} categories in batch")
            else:
                failed_count = len(categories)
                logger.error(f"Failed to save batch of {len(categories)} categories")
                
        except Exception as e:
            logger.error(f"Error in batch save: {e}")
            failed_count = len(categories)
        
        return success_count, failed_count
    
    async def get_category_children(self, parent_id: str) -> List[CategoryInfo]:
        """
        获取指定类别的子类别
        
        Args:
            parent_id: 父类别ID
            
        Returns:
            List[CategoryInfo]: 子类别列表
        """
        try:
            result = self.client.table('amazon_categories')\
                .select('*')\
                .eq('parent_category_id', parent_id)\
                .execute()
            
            categories = []
            for row in result.data:
                category = CategoryInfo(
                    category_id=row['category_id'],
                    name=row['name'],
                    level=row['level'],
                    parent_id=row['parent_category_id'],
                    link=row.get('link'),
                    status=CategoryFetchStatus.COMPLETED
                )
                categories.append(category)
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting children for category {parent_id}: {e}")
            return []
    
    async def get_root_categories(self) -> List[CategoryInfo]:
        """
        获取根级别类别
        
        Returns:
            List[CategoryInfo]: 根类别列表
        """
        try:
            result = self.client.table('amazon_categories')\
                .select('*')\
                .is_('parent_category_id', 'null')\
                .execute()
            
            categories = []
            for row in result.data:
                category = CategoryInfo(
                    category_id=row['category_id'],
                    name=row['name'],
                    level=row['level'] or 1,
                    parent_id=None,
                    link=row.get('link'),
                    status=CategoryFetchStatus.COMPLETED
                )
                categories.append(category)
            
            return categories
            
        except Exception as e:
            logger.error(f"Error getting root categories: {e}")
            return []
    
    async def create_fetch_request(self, run_id: str, config_data: Dict[str, Any]) -> Optional[int]:
        """
        创建类别获取请求记录
        
        Args:
            run_id: 运行ID
            config_data: 配置数据
            
        Returns:
            Optional[int]: 请求ID或None
        """
        try:
            request_data = {
                "request_type": "category_fetch",
                "amazon_domain": config_data.get("domain", "amazon.com"),
                "status": "pending",
                "request_parameters": {
                    "run_id": run_id,
                    "fetch_config": config_data
                },
                "request_metadata": {
                    "run_id": run_id,
                    "created_by": "category_fetcher"
                }
            }
            
            result = self.client.table('scraping_requests')\
                .insert(request_data)\
                .execute()
            
            if result.data and len(result.data) > 0:
                request_id = result.data[0]['id']
                logger.info(f"Created fetch request with ID: {request_id}")
                return request_id
            else:
                logger.error("Failed to create fetch request")
                return None
                
        except Exception as e:
            logger.error(f"Error creating fetch request: {e}")
            return None
    
    async def update_fetch_request_status(self, request_id: int, status: str, 
                                        additional_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        更新获取请求状态
        
        Args:
            request_id: 请求ID
            status: 新状态
            additional_data: 额外数据
            
        Returns:
            bool: 更新是否成功
        """
        try:
            update_data = {
                "status": status,
                "updated_at": datetime.utcnow().isoformat()
            }
            
            if additional_data:
                update_data.update(additional_data)
            
            result = self.client.table('scraping_requests')\
                .update(update_data)\
                .eq('id', request_id)\
                .execute()
            
            if result.data:
                logger.debug(f"Updated fetch request {request_id} status to {status}")
                return True
            else:
                logger.error(f"Failed to update fetch request {request_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error updating fetch request {request_id}: {e}")
            return False
    
    async def get_category_statistics(self) -> Dict[str, Any]:
        """
        获取类别统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            # 总类别数
            total_result = self.client.table('amazon_categories')\
                .select('id', count='exact')\
                .execute()
            total_categories = total_result.count or 0
            
            # 按级别统计
            level_result = self.client.table('amazon_categories')\
                .select('level')\
                .execute()
            
            level_stats = {}
            for row in level_result.data:
                level = row.get('level', 0)
                level_stats[level] = level_stats.get(level, 0) + 1
            
            # 根类别数
            root_result = self.client.table('amazon_categories')\
                .select('id', count='exact')\
                .is_('parent_category_id', 'null')\
                .execute()
            root_categories = root_result.count or 0
            
            return {
                "total_categories": total_categories,
                "root_categories": root_categories,
                "categories_by_level": level_stats,
                "max_level": max(level_stats.keys()) if level_stats else 0
            }
            
        except Exception as e:
            logger.error(f"Error getting category statistics: {e}")
            return {}
    
    async def _build_full_path(self, category: CategoryInfo) -> str:
        """
        构建类别的完整路径
        
        Args:
            category: 类别信息
            
        Returns:
            str: 完整路径
        """
        if not category.parent_id:
            return category.name
        
        try:
            # 递归获取父类别路径
            parent_result = self.client.table('amazon_categories')\
                .select('name, parent_category_id')\
                .eq('category_id', category.parent_id)\
                .execute()
            
            if parent_result.data:
                parent_data = parent_result.data[0]
                parent_category = CategoryInfo(
                    category_id=category.parent_id,
                    name=parent_data['name'],
                    level=category.level - 1,
                    parent_id=parent_data.get('parent_category_id')
                )
                parent_path = await self._build_full_path(parent_category)
                return f"{parent_path} > {category.name}"
            else:
                return category.name
                
        except Exception as e:
            logger.error(f"Error building full path for category {category.category_id}: {e}")
            return category.name 