"""
类别导入服务
负责将类别信息导入到amazon_categories表
"""
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Set

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

# 添加backend目录到Python路径
backend_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_root))

from core.database.connection import get_supabase_client

logger = logging.getLogger(__name__)

class CategoryImporter:
    """类别导入服务"""
    
    def __init__(self):
        self.supabase = get_supabase_client()
        self.existing_categories = set()
    
    async def get_existing_categories(self) -> Set[str]:
        """获取已存在的类别ID"""
        try:
            result = self.supabase.table('amazon_categories').select('category_id').execute()
            if result.data:
                return {row['category_id'] for row in result.data}
            return set()
        except Exception as e:
            logger.error(f"获取已存在类别时出错: {e}")
            return set()
    
    async def batch_insert_categories(self, categories: List[Dict[str, Any]]) -> int:
        """批量插入类别数据"""
        if not categories:
            return 0
        
        try:
            # 获取已存在的类别ID
            existing_ids = await self.get_existing_categories()
            
            # 过滤掉已存在的类别
            new_categories = [
                cat for cat in categories 
                if cat['category_id'] not in existing_ids
            ]
            
            if not new_categories:
                logger.info("没有新的类别需要插入")
                return 0
            
            # 批量插入（使用upsert避免重复键冲突）
            result = self.supabase.table('amazon_categories').upsert(
                new_categories, 
                on_conflict='category_id'
            ).execute()
            
            if result.data:
                inserted_count = len(result.data)
                logger.info(f"成功处理 {inserted_count} 个类别（新增或更新）")
                return inserted_count
            else:
                logger.error("插入类别失败")
                return 0
                
        except Exception as e:
            logger.error(f"批量插入类别时出错: {e}")
            return 0
    
    def deduplicate_categories(self, categories: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        去重类别数据，并确保 `categories` 字段的数据优先。
        """
        # 使用字典来去重，后来的会覆盖先来的
        # `categories` 数组中的数据是在 `category_information` 之后添加到列表中的，
        # 因此，不反转列表，就可以让 `categories` 的数据覆盖 `category_information` 的数据。
        unique_categories_dict = {
            cat['category_id']: cat 
            for cat in categories  # 移除 reversed()
            if cat.get('category_id')
        }
        
        unique_list = list(unique_categories_dict.values())
        logger.debug(f"去重完成: {len(categories)} -> {len(unique_list)}")
        return unique_list 