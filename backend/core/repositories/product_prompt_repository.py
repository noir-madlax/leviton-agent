from typing import List, Optional, Dict, Any
from supabase import Client
from core.models.product_prompt import ProductPrompt, ProductPromptCreate, ProductPromptUpdate
from pydantic import ValidationError
import logging

logger = logging.getLogger(__name__)

class ProductPromptRepository:
    """ProductPrompt 数据访问层"""
    
    def __init__(self, supabase_client: Client):
        self.client = supabase_client
        self.table_name = "product_prompt"
    
    async def get_by_id(self, prompt_id: int) -> Optional[ProductPrompt]:
        """根据 ID 获取 ProductPrompt"""
        try:
            response = self.client.table(self.table_name).select("*").eq("id", prompt_id).execute()
            
            if response.data and len(response.data) > 0:
                return ProductPrompt(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"获取 ProductPrompt ID {prompt_id} 失败: {e}")
            return None
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ProductPrompt]:
        """获取所有 ProductPrompt（分页）"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .order("created_at", desc=True)
                .range(skip, skip + limit - 1)
                .execute()
            )
            
            return [ProductPrompt(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"获取 ProductPrompt 列表失败: {e}")
            return []
    
    async def create(self, product_prompt: ProductPromptCreate) -> Optional[ProductPrompt]:
        """创建新的 ProductPrompt"""
        try:
            data = product_prompt.model_dump(exclude_unset=True)
            response = self.client.table(self.table_name).insert(data).execute()
            
            if response.data and len(response.data) > 0:
                return ProductPrompt(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"创建 ProductPrompt 失败: {e}")
            return None
    
    async def update(self, prompt_id: int, product_prompt: ProductPromptUpdate) -> Optional[ProductPrompt]:
        """更新 ProductPrompt"""
        try:
            data = product_prompt.model_dump(exclude_unset=True)
            if not data:  # 如果没有要更新的字段
                return await self.get_by_id(prompt_id)
                
            response = (
                self.client.table(self.table_name)
                .update(data)
                .eq("id", prompt_id)
                .execute()
            )
            
            if response.data and len(response.data) > 0:
                return ProductPrompt(**response.data[0])
            return None
            
        except Exception as e:
            logger.error(f"更新 ProductPrompt ID {prompt_id} 失败: {e}")
            return None
    
    async def delete(self, prompt_id: int) -> bool:
        """删除 ProductPrompt"""
        try:
            response = self.client.table(self.table_name).delete().eq("id", prompt_id).execute()
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"删除 ProductPrompt ID {prompt_id} 失败: {e}")
            return False
    
    async def search_by_prompt(self, search_term: str, limit: int = 50) -> List[ProductPrompt]:
        """根据提示词内容搜索"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .ilike("prompt", f"%{search_term}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return [ProductPrompt(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"搜索 ProductPrompt 失败: {e}")
            return []
    
    async def search_by_description(self, search_term: str, limit: int = 50) -> List[ProductPrompt]:
        """根据描述内容搜索"""
        try:
            response = (
                self.client.table(self.table_name)
                .select("*")
                .ilike("description", f"%{search_term}%")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            
            return [ProductPrompt(**item) for item in response.data]
            
        except Exception as e:
            logger.error(f"搜索 ProductPrompt 描述失败: {e}")
            return [] 