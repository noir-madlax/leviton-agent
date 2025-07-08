"""
Agent 请求处理服务
"""
import logging
from typing import AsyncGenerator, Dict, Any
from agent.services.request_models import AgentStreamRequest, AgentQueryContext
from agent.services.query_processor import get_query_processor
from agent.streaming.stream_handler import stream_agent_response

logger = logging.getLogger(__name__)


class AgentRequestHandler:
    """Agent 请求处理器"""
    
    def __init__(self):
        self.query_processor = get_query_processor()
    
    async def handle_stream_request(self, request: AgentStreamRequest) -> AsyncGenerator[str, None]:
        """处理流式请求"""
        try:
            # 记录请求信息
            logger.info("=" * 80)
            logger.info("🚀 [AGENT-REQUEST-HANDLER] 接收到新的流式请求")
            logger.info(f"📊 Project ID: {request.project_id}")
            logger.info(f"🔍 Category Filters: {request.filters.categories}")
            logger.info(f"🏷️ Brand Filters: {request.filters.brands}")
            logger.info(f"📝 Query: {request.query[:100]}{'...' if len(request.query) > 100 else ''}")
            logger.info("=" * 80)
            
            # 验证请求
            if not request.query.strip():
                logger.error("查询内容为空")
                yield "data: " + '{"status": "error", "message": "查询内容不能为空"}' + "\n\n"
                return
            
            # 准备查询上下文
            query_context = self._prepare_query_context(request)
            
            # 使用查询处理器准备完整查询
            enhanced_query = await self.query_processor.prepare_query_with_prompt(
                query=request.query,
                project_id=request.project_id,
                category_filters=request.filters.categories,
                brand_filters=request.filters.brands
            )
            
            logger.info(f"📝 Enhanced Query 长度: {len(enhanced_query)} 字符")
            
            async for chunk in stream_agent_response(
                query=enhanced_query
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"处理流式请求时出错: {e}", exc_info=True)
            error_response = {
                "status": "error",
                "message": f"处理请求时发生错误: {str(e)}"
            }
            yield f"data: {error_response}\n\n"
    
    def _prepare_query_context(self, request: AgentStreamRequest) -> AgentQueryContext:
        """准备查询上下文"""
        return AgentQueryContext(
            original_query=request.query,
            project_id=request.project_id,
            category_filters=request.filters.categories,
            brand_filters=request.filters.brands,
            additional_context={
                "date_range": request.filters.date_range,
                "price_range": request.filters.price_range
            }
        )
    
    def _validate_request(self, request: AgentStreamRequest) -> Dict[str, Any]:
        """验证请求参数"""
        validation_result = {
            "valid": True,
            "errors": []
        }
        
        # 验证查询内容
        if not request.query or not request.query.strip():
            validation_result["valid"] = False
            validation_result["errors"].append("查询内容不能为空")
        
        # 验证项目ID格式（如果需要）
        if request.project_id and len(request.project_id) < 3:
            validation_result["valid"] = False
            validation_result["errors"].append("项目ID格式不正确")
        
        # 验证过滤器
        if request.filters.categories and len(request.filters.categories) > 50:
            validation_result["valid"] = False
            validation_result["errors"].append("类别过滤器数量过多")
        
        return validation_result


# 全局请求处理器实例
request_handler = AgentRequestHandler()

def get_request_handler() -> AgentRequestHandler:
    """获取请求处理器实例"""
    return request_handler 