from typing import List, Optional
from ..repositories.product_prompt_repository import ProductPromptRepository
from ..models.product_prompt import ProductPrompt, ProductPromptCreate, ProductPromptUpdate
import logging

logger = logging.getLogger(__name__)

class ProductPromptService:
    """ProductPrompt 业务逻辑层"""
    
    def __init__(self, repository: ProductPromptRepository):
        self.repository = repository
    
    async def get_prompt_by_id(self, prompt_id: int) -> Optional[ProductPrompt]:
        """根据 ID 获取提示词"""
        if prompt_id <= 0:
            logger.warning(f"无效的提示词 ID: {prompt_id}")
            return None
        
        return await self.repository.get_by_id(prompt_id)
    
    async def get_all_prompts(self, page: int = 1, page_size: int = 20) -> List[ProductPrompt]:
        """获取所有提示词（分页）"""
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
            
        skip = (page - 1) * page_size
        return await self.repository.get_all(skip=skip, limit=page_size)
    
    async def create_prompt(self, prompt_data: ProductPromptCreate) -> Optional[ProductPrompt]:
        """创建新提示词"""
        # 业务验证
        if not prompt_data.prompt and not prompt_data.description:
            logger.warning("提示词和描述都为空，拒绝创建")
            return None
        
        if prompt_data.prompt and len(prompt_data.prompt.strip()) == 0:
            prompt_data.prompt = None
            
        if prompt_data.description and len(prompt_data.description.strip()) == 0:
            prompt_data.description = None
        
        return await self.repository.create(prompt_data)
    
    async def update_prompt(self, prompt_id: int, prompt_data: ProductPromptUpdate) -> Optional[ProductPrompt]:
        """更新提示词"""
        if prompt_id <= 0:
            logger.warning(f"无效的提示词 ID: {prompt_id}")
            return None
        
        # 检查提示词是否存在
        existing_prompt = await self.repository.get_by_id(prompt_id)
        if not existing_prompt:
            logger.warning(f"提示词 ID {prompt_id} 不存在")
            return None
        
        # 清理空字符串
        if prompt_data.prompt is not None and len(prompt_data.prompt.strip()) == 0:
            prompt_data.prompt = None
            
        if prompt_data.description is not None and len(prompt_data.description.strip()) == 0:
            prompt_data.description = None
        
        return await self.repository.update(prompt_id, prompt_data)
    
    async def delete_prompt(self, prompt_id: int) -> bool:
        """删除提示词"""
        if prompt_id <= 0:
            logger.warning(f"无效的提示词 ID: {prompt_id}")
            return False
        
        # 检查提示词是否存在
        existing_prompt = await self.repository.get_by_id(prompt_id)
        if not existing_prompt:
            logger.warning(f"提示词 ID {prompt_id} 不存在")
            return False
        
        return await self.repository.delete(prompt_id)
    
    async def search_prompts(self, search_term: str, search_type: str = "prompt", limit: int = 50) -> List[ProductPrompt]:
        """搜索提示词"""
        if not search_term or len(search_term.strip()) == 0:
            return []
        
        search_term = search_term.strip()
        
        if search_type == "description":
            return await self.repository.search_by_description(search_term, limit)
        else:  # 默认搜索 prompt 字段
            return await self.repository.search_by_prompt(search_term, limit)
    
    async def get_recent_prompts(self, limit: int = 10) -> List[ProductPrompt]:
        """获取最近的提示词"""
        if limit < 1 or limit > 100:
            limit = 10
        
        return await self.repository.get_all(skip=0, limit=limit) 