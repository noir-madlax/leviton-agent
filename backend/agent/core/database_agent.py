"""
数据库查询 Agent - 专门负责数据库查询和MCP工具调用
"""
import logging
from typing import Optional
from config import settings
from agent.tools import ProductQueryTool, ReviewQueryTool

logger = logging.getLogger(__name__)

class DatabaseAgent:
    """数据库查询 Agent 类"""
    
    def __init__(self, agent_manager=None):
        self.agent = None
        self.tool_collection_context = None
        self.init_error = None
        self.agent_manager = agent_manager  # 引用 AgentManager 以使用通用方法
    
    async def initialize(self) -> bool:
        """初始化数据库查询 Agent"""
        logger.info("初始化数据库查询 Agent...")
        
        try:
            from smolagents import ToolCollection, CodeAgent, OpenAIServerModel
            from mcp import StdioServerParameters
            
            # 创建模型实例
            model = OpenAIServerModel(
                model_id=settings.MODEL_ID,
                api_base="https://openrouter.ai/api/v1",
                api_key=settings.API_KEY,
                stream_options={"include_usage": True},
                temperature=0.3
            )
            
            logger.info("初始化数据库相关工具...")
            
            # 初始化 MCP 工具集
            server_parameters = StdioServerParameters(
                command="npx",
                args=["-y", 
                      "@supabase/mcp-server-supabase@latest",
                      "--access-token",
                      settings.MCP_ACCESS_TOKEN]
            )
            
            logger.info("初始化 MCP ToolCollection...")
            self.tool_collection_context = ToolCollection.from_mcp(server_parameters, trust_remote_code=True)
            tool_collection = self.tool_collection_context.__enter__()
            
            # 组合所有数据库相关工具
            database_tools = [*tool_collection.tools]
            
            # 创建数据库查询专用的 ToolCallingAgent
            # 使用 ToolCallingAgent 因为数据库查询是单线程任务，JSON工具调用更适合
            self.agent = CodeAgent(
                tools=database_tools,
                model=model,
                max_steps=5,  # 增加步数以支持复杂的数据库查询
                name="database_agent",
                description="专门负责数据库查询、数据检索和MCP工具调用的代理。可以查询产品信息、评论数据，执行复杂的数据库操作。",
                additional_authorized_imports=['json'],
            )
            
            # 如果有 AgentManager 引用，尝试追加自定义 system_prompt
            await self.agent_manager.append_custom_system_prompt(
                agent=self.agent,
                prompt_id=8
            )
            
            logger.info(f"数据库查询 Agent 初始化成功，加载的工具数量: {len(database_tools)}")
            return True
            
        except Exception as e:
            self.init_error = str(e)
            logger.error(f"数据库查询 Agent 初始化失败: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """清理数据库 Agent 资源"""
        logger.info("清理数据库查询 Agent 资源...")
        if self.tool_collection_context:
            try:
                self.tool_collection_context.__exit__(None, None, None)
                logger.info("MCP 工具集资源已释放")
            except Exception as e:
                logger.error(f"释放 MCP 工具集资源时出错: {e}", exc_info=True)
    
    def is_ready(self) -> bool:
        """检查数据库 Agent 是否准备就绪"""
        return self.agent is not None
    
    def get_agent(self):
        """获取数据库 Agent 实例"""
        return self.agent
    
    def get_init_error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self.init_error
    
    async def query_database(self, query: str) -> str:
        """执行数据库查询"""
        if not self.is_ready():
            return "数据库 Agent 未准备就绪"
        
        try:
            result = await self.agent.run(query)
            return result
        except Exception as e:
            logger.error(f"数据库查询失败: {e}", exc_info=True)
            return f"数据库查询出错: {str(e)}"
    
    async def reload_system_prompt(self, prompt_id: int = 8):
        """重新加载数据库 Agent 的 system_prompt
        
        Args:
            prompt_id: 要加载的 prompt ID，默认为 8
        """
        if not self.agent_manager:
            logger.warning("没有 AgentManager 引用，无法重新加载 system_prompt")
            return False
            
        return await self.agent_manager.reload_system_prompt_from_database(
            agent=self.agent,
            prompt_id=prompt_id
        ) 