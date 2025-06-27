"""
图表代码生成 Agent - 专门负责生成前端 JavaScript 绘制图表的代码
"""
import logging
from typing import Optional
from config import settings

logger = logging.getLogger(__name__)

class ChartGenerationAgent:
    """图表代码生成 Agent 类"""
    
    def __init__(self, agent_manager=None):
        self.agent = None
        self.init_error = None
        self.agent_manager = agent_manager  # 引用 AgentManager 以使用通用方法
    
    async def initialize(self) -> bool:
        """初始化图表代码生成 Agent"""
        logger.info("初始化图表代码生成 Agent...")
        
        try:
            from smolagents import ToolCallingAgent, OpenAIServerModel
            
            # 创建模型实例
            model = OpenAIServerModel(
                model_id=settings.MODEL_ID,
                api_base="https://openrouter.ai/api/v1",
                api_key=settings.API_KEY,
                stream_options={"include_usage": True},
                temperature=0.3
            )
            
            logger.info("初始化图表代码生成相关工具...")
            
            # 创建图表代码生成专用的 CodeAgent
            # 使用 CodeAgent 因为需要生成和执行 JavaScript 代码
            self.agent = ToolCallingAgent(
                tools=[],  # 图表生成主要依赖代码生成能力，不需要外部工具
                model=model,
                max_steps=2,  # 适中的步数，专注于代码生成
                name="chart_generation_agent",
                description="专门负责生成前端 JavaScript 图表代码的代理。可以根据数据生成各种类型的图表代码，包括 Recharts 图表库的代码。"
            )
            
            # 如果有 AgentManager 引用，尝试追加自定义 system_prompt
            if self.agent_manager:
                await self.agent_manager.append_custom_system_prompt(
                    agent=self.agent,
                    prompt_id=9  # 为图表生成 Agent 使用专用的 prompt ID
                )
            
            logger.info(f"图表代码生成 Agent 初始化成功")
            return True
            
        except Exception as e:
            self.init_error = str(e)
            logger.error(f"图表代码生成 Agent 初始化失败: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """清理图表代码生成 Agent 资源"""
        logger.info("清理图表代码生成 Agent 资源...")
        # CodeAgent 通常不需要特殊的资源清理
        pass
    
    def is_ready(self) -> bool:
        """检查图表代码生成 Agent 是否准备就绪"""
        return self.agent is not None
    
    def get_agent(self):
        """获取图表代码生成 Agent 实例"""
        return self.agent
    
    def get_init_error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self.init_error
    
    async def generate_chart_code(self, chart_request: str) -> str:
        """生成图表代码"""
        if not self.is_ready():
            return "图表代码生成 Agent 未准备就绪"
        
        try:
            result = await self.agent.run(chart_request)
            return result
        except Exception as e:
            logger.error(f"图表代码生成失败: {e}", exc_info=True)
            return f"图表代码生成出错: {str(e)}"
    
    async def reload_system_prompt(self, prompt_id: int = 9):
        """重新加载图表代码生成 Agent 的 system_prompt
        
        Args:
            prompt_id: 要加载的 prompt ID，默认为 9
        """
        if not self.agent_manager:
            logger.warning("没有 AgentManager 引用，无法重新加载 system_prompt")
            return False
            
        return await self.agent_manager.reload_system_prompt_from_database(
            agent=self.agent,
            prompt_id=prompt_id
        ) 