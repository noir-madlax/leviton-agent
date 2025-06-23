"""
查询处理器 - 负责处理用户查询和准备提示词，保持原有逻辑不变
"""
import logging
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
    
    async def prepare_query_with_prompt(self, query: str) -> str:
        """准备完整的查询，包含系统提示词 - 保持原有逻辑不变"""
        try:
            # 直接创建服务实例，不使用依赖注入
            from core.database.connection import get_supabase_client
            from core.repositories.product_prompt_repository import ProductPromptRepository
            from agent.services.product_prompt_service import ProductPromptService
            
            # 获取 Supabase 客户端
            supabase_client = get_supabase_client()
            
            # 创建仓库和服务实例
            repository = ProductPromptRepository(supabase_client)
            service = ProductPromptService(repository)
            
            # 获取提示词
            prefixPrompt = await service.get_prompt_by_id(5)
            
            if not prefixPrompt:
                logger.warning("未找到 ID 为 1 的提示词，使用原始查询")
                return query
                
            complete_query = prefixPrompt.prompt + "\n\n 用户的问题如下：" + query
            
            logger.info(f"已成功拼接提示词，总 prompt 长度: {len(complete_query)} 字符")
            return complete_query
            
        except Exception as e:
            logger.error(f"准备查询提示词时出错: {e}")
            logger.info("使用原始查询继续执行")
            return query

# 全局查询处理器实例
query_processor = QueryProcessor()

def get_query_processor() -> QueryProcessor:
    """获取查询处理器实例"""
    return query_processor 