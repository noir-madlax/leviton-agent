"""
Agent 管理器 - 负责 Agent 的初始化、配置和生命周期管理
"""
import logging
from typing import Optional
from config import settings
from agent.tools import ProductQueryTool, ReviewQueryTool
from agent.validators.chart_validator import check_reasoning_and_plot

logger = logging.getLogger(__name__)

class AgentManager:
    """Agent 管理器类"""
    
    def __init__(self):
        self.agent = None
        self.init_error = None
        self.tool_collection_context = None
    
    async def initialize_agent(self) -> bool:
        """初始化 Agent - 保持原有逻辑不变"""
        logger.info("FastAPI 应用启动，开始初始化 Agent...")
        
        try:
            from smolagents import ToolCollection, ToolCallingAgent, CodeAgent, OpenAIServerModel
            from mcp import StdioServerParameters
            
            logger.info(f"使用模型: {settings.MODEL_ID}")
            model = OpenAIServerModel(
                model_id=settings.MODEL_ID,
                api_base="https://openrouter.ai/api/v1",
                api_key=settings.API_KEY
            )
            
            logger.info("初始化工具...")
            product_tool = ProductQueryTool()
            review_tool = ReviewQueryTool()

            server_parameters = StdioServerParameters(
                command="npx",
                args=["-y", 
                      "@supabase/mcp-server-supabase@latest",
                      "--access-token",
                      settings.MCP_ACCESS_TOKEN]
            )

            logger.info("初始化 ToolCollection...")
            self.tool_collection_context = ToolCollection.from_mcp(server_parameters, trust_remote_code=True)
            # 手动进入上下文
            tool_collection = self.tool_collection_context.__enter__()

            # all_tools = [product_tool, review_tool, *tool_collection.tools]
            all_tools = [ *tool_collection.tools]

            logger.info("创建 CodeAgent...")
            self.agent = CodeAgent(
                tools=all_tools, 
                model=model,
                max_steps=settings.MAX_ITERATIONS,
                additional_authorized_imports = ['json'],
                final_answer_checks=[check_reasoning_and_plot]
            )

            logger.info(f"Agent 初始化成功，加载的工具: {self.agent.tools}")
            return True

        except Exception as e:
            self.init_error = str(e)
            logger.error(f"Agent 初始化失败: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """清理资源 - 保持原有逻辑不变"""
        logger.info("FastAPI 应用关闭，正在释放资源...")
        if self.tool_collection_context:
            try:
                self.tool_collection_context.__exit__(None, None, None)
                logger.info("工具集资源已释放。")
            except Exception as e:
                logger.error(f"释放工具集资源时出错: {e}", exc_info=True)
    
    def is_ready(self) -> bool:
        """检查 Agent 是否准备就绪"""
        return self.agent is not None
    
    def get_agent(self):
        """获取 Agent 实例"""
        return self.agent
    
    def get_init_error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self.init_error

# 全局 Agent 管理器实例
agent_manager = AgentManager()

def get_agent_manager() -> AgentManager:
    """获取 Agent 管理器实例"""
    return agent_manager 