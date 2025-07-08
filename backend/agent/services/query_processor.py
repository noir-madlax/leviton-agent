"""
查询处理器 - 负责处理用户查询和准备提示词，保持原有逻辑不变
"""
import logging
from typing import Optional, List
from core.database.connection import get_supabase_client
from core.repositories.product_prompt_repository import ProductPromptRepository
from agent.services.product_prompt_service import ProductPromptService

logger = logging.getLogger(__name__)

class QueryProcessor:
    """查询处理器类"""
    
    def __init__(self):
        self._service = None
    
    async def _get_service(self) -> ProductPromptService:
        """获取产品提示词服务实例"""
        if not self._service:
            supabase_client = get_supabase_client()
            repository = ProductPromptRepository(supabase_client)
            self._service = ProductPromptService(repository)
        return self._service
    
    async def prepare_query_with_prompt(
        self, 
        query: str, 
        project_id: Optional[str] = None,
        category_filters: Optional[List[str]] = None,
        brand_filters: Optional[List[str]] = None
    ) -> str:
        """准备完整的查询，包含系统提示词和上下文信息"""
        try:

            # 构建上下文信息
            context_info = self._build_context_info(project_id, category_filters, brand_filters)
            
            # 拼接完整查询：系统提示词 + 上下文信息 + 用户问题
            complete_query = context_info + "\n\n用户的问题如下：" + query  # 使用字符串连接
            
            logger.info(f"最终的 query 为: {complete_query}")
            return complete_query
            
        except Exception as e:
            logger.error(f"准备查询提示词时出错: {e}", exc_info=True)
            logger.info("使用原始查询继续执行")
            return query
    
    def _build_context_info(
        self, 
        project_id: Optional[str], 
        category_filters: Optional[List[str]], 
        brand_filters: Optional[List[str]]
    ) -> str:
        """构建上下文信息"""
        context_parts = []
        
        if project_id:
            context_parts.append(f"本次查询必须使用的 projects 表的 ID 为: {project_id}")
        
        if category_filters and len(category_filters) > 0:
            categories_str = ", ".join(category_filters)
            context_parts.append(f"本次查询必须使用的 product_wide_table 表的 category 字段限定为: {categories_str}")
        
        if brand_filters and len(brand_filters) > 0:
            brands_str = ", ".join(brand_filters)
            context_parts.append(f"需要过滤的品牌是: {brands_str}")
        
        if context_parts:
            return "\n".join(context_parts)
        else:
            return "任务上下文信息：本次任务没有特定的过滤条件"

# 全局查询处理器实例
query_processor = QueryProcessor()

def get_query_processor() -> QueryProcessor:
    """获取查询处理器实例"""
    return query_processor 