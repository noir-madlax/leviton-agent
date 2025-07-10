"""
扩展字段管理 Agent - 专门负责创建和计算项目的动态扩展字段
"""
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

class ExtendFieldsAgent:
    """扩展字段管理 Agent 类"""
    
    def __init__(self, agent_manager=None):
        self.agent = None
        self.mcp_tool_manager = None
        self.init_error = None
        self.agent_manager = agent_manager  # 引用 AgentManager 以使用通用方法
    
    async def initialize(self) -> bool:
        """初始化扩展字段管理 Agent"""
        logger.info("初始化扩展字段管理 Agent...")
        
        try:
            from smolagents import CodeAgent, OpenAIServerModel
            
            # 创建模型实例
            model = OpenAIServerModel(
                model_id=settings.MODEL_ID,
                api_base="https://openrouter.ai/api/v1",
                api_key=settings.API_KEY,
                stream_options={"include_usage": True},
                temperature=0.3
            )
            
            logger.info("初始化扩展字段管理相关工具...")
            
            # 初始化 Supabase MCP 工具集
            from agent.tools import get_supabase_mcp_manager
            
            self.mcp_tool_manager = get_supabase_mcp_manager()
            database_tools = await self.mcp_tool_manager.initialize_with_preset("database_only")
            
            # 创建扩展字段管理专用的 CodeAgent
            # 使用 CodeAgent 因为需要执行复杂的SQL操作
            self.agent = CodeAgent(
                tools=database_tools,
                model=model,
                max_steps=5,  # 足够的步数支持复杂的字段创建和计算
                name="extend_fields_agent",
                description="专门负责动态过滤字段创建与计算代理。可以根据业务需求设计字段，执行SQL计算，并存储结果到扩展数据表。",
                additional_authorized_imports=['json', 'uuid'],
            )
            
            # 如果有 AgentManager 引用，尝试追加自定义 system_prompt
            if self.agent_manager:
                await self.agent_manager.append_custom_system_prompt(
                    agent=self.agent,
                    prompt_id=14  # 为扩展字段管理 Agent 使用专用的 prompt ID
                )
            
            logger.info(f"扩展字段管理 Agent 初始化成功，加载的工具数量: {len(database_tools)}")
            return True
            
        except Exception as e:
            self.init_error = str(e)
            logger.error(f"扩展字段管理 Agent 初始化失败: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """清理扩展字段管理 Agent 资源"""
        logger.info("清理扩展字段管理 Agent 资源...")
        if self.mcp_tool_manager:
            try:
                self.mcp_tool_manager.cleanup()
                logger.info("MCP 工具管理器资源已释放")
            except Exception as e:
                logger.error(f"释放 MCP 工具管理器资源时出错: {e}", exc_info=True)
    
    def is_ready(self) -> bool:
        """检查扩展字段管理 Agent 是否准备就绪"""
        return self.agent is not None
    
    def get_agent(self):
        """获取扩展字段管理 Agent 实例"""
        return self.agent
    
    def get_init_error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self.init_error
    
    async def create_extend_field(self, request: str) -> str:
        """创建扩展字段"""
        if not self.is_ready():
            return "扩展字段管理 Agent 未准备就绪"
        
        try:
            result = await self.agent.run(request)
            return result
        except Exception as e:
            logger.error(f"扩展字段创建失败: {e}", exc_info=True)
            return f"扩展字段创建出错: {str(e)}"
    
    async def reload_system_prompt(self, prompt_id: int = 14):
        """重新加载扩展字段管理 Agent 的 system_prompt
        
        Args:
            prompt_id: 要加载的 prompt ID，默认为 14
        """
        if not self.agent_manager:
            logger.warning("没有 AgentManager 引用，无法重新加载 system_prompt")
            return False
            
        return await self.agent_manager.reload_system_prompt_from_database(
            agent=self.agent,
            prompt_id=prompt_id
        ) 