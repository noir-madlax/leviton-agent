"""
BI 分析 Agent - 专门负责商业智能分析、数据库查询和MCP工具调用
"""
import logging
from typing import Optional
from config import settings
from agent.tools import ProductQueryTool, ReviewQueryTool

logger = logging.getLogger(__name__)

class BiAgent:
    """BI 分析 Agent 类"""
    
    def __init__(self, agent_manager=None):
        self.agent = None
        self.mcp_tool_manager = None
        self.init_error = None
        self.agent_manager = agent_manager  # 引用 AgentManager 以使用通用方法
        self.chart_generation_agent = None  # 图表代码生成子 Agent
    
    async def initialize(self) -> bool:
        """初始化 BI 分析 Agent"""
        logger.info("初始化 BI 分析 Agent...")
        
        try:
            from smolagents import CodeAgent, OpenAIServerModel
            from agent.tools import SupabaseQueryTool
            
            # 创建模型实例
            model = OpenAIServerModel(
                model_id=settings.MODEL_ID,
                api_base="https://openrouter.ai/api/v1",
                api_key=settings.API_KEY,
                stream_options={"include_usage": True},
                temperature=0.3
            )
            
            logger.info("初始化 BI 分析相关工具...")
            
            # 步骤1: 初始化图表代码生成子 Agent
            logger.info("初始化图表代码生成子 Agent...")
            from agent.core.chart_generation_agent import ChartGenerationAgent
            self.chart_generation_agent = ChartGenerationAgent(agent_manager=self.agent_manager)
            chart_init_success = await self.chart_generation_agent.initialize()
            
            if not chart_init_success:
                raise Exception(f"图表代码生成子 Agent 初始化失败: {self.chart_generation_agent.get_init_error()}")
            
            # 步骤2: 初始化 Supabase MCP 工具集 - 使用新的多例模式
            # from agent.tools import create_supabase_mcp_manager
            
            # 为 BI Agent 创建独立的 MCP 配置
            # bi_mcp_config = {
            #     "access_token": settings.MCP_ACCESS_TOKEN,
            #     "project_id": "qsatkfdmgnbmohmqwvqc",  # 从 prompt 中获取的项目 ID
            #     "extra_args": []  # 可以添加额外的 BI 分析特定参数
            # }
            
            # self.mcp_tool_manager = create_supabase_mcp_manager(
            #     agent_id="bi_agent",
            #     mcp_config=bi_mcp_config
            # )
            # bi_tools = await self.mcp_tool_manager.initialize_with_preset("database_only")
            
            # 创建 BI 分析专用的 CodeAgent，管理图表生成子 Agent
            self.agent = CodeAgent(
                tools=[SupabaseQueryTool()],
                model=model,
                managed_agents=[
                    self.chart_generation_agent.get_agent()  # 管理图表代码生成子 Agent
                ],
                max_steps=10,  # 增加步数以支持复杂的 BI 分析查询
                name="bi_agent",
                description="专业的产品市场分析Agent，根据用户的产品分析需求，根据数据库中的数据信息，完成从需求设计、数据获取到图表生成的完整分析流程",
                additional_authorized_imports=['json', 'time', 'numpy', 'pandas'],
            )
            
            # 如果有 AgentManager 引用，尝试追加自定义 system_prompt
            if self.agent_manager:
                await self.agent_manager.append_custom_system_prompt(
                    agent=self.agent,
                    prompt_id=15
                )
            
            logger.info(f"BI 分析 Agent 初始化成功")
            return True
            
        except Exception as e:
            self.init_error = str(e)
            logger.error(f"BI 分析 Agent 初始化失败: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """清理 BI Agent 资源"""
        logger.info("清理 BI 分析 Agent 资源...")
        
        # 清理图表代码生成子 Agent
        if self.chart_generation_agent:
            try:
                self.chart_generation_agent.cleanup()
                logger.info("图表代码生成子 Agent 资源已释放")
            except Exception as e:
                logger.error(f"释放图表代码生成子 Agent 资源时出错: {e}", exc_info=True)
        
        # 清理 MCP 工具管理器
        if self.mcp_tool_manager:
            try:
                self.mcp_tool_manager.cleanup()
                logger.info("MCP 工具管理器资源已释放")
            except Exception as e:
                logger.error(f"释放 MCP 工具管理器资源时出错: {e}", exc_info=True)
    
    def is_ready(self) -> bool:
        """检查 BI Agent 是否准备就绪"""
        return self.agent is not None
    
    def get_agent(self):
        """获取 BI Agent 实例"""
        return self.agent
    
    def get_init_error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self.init_error
    
    async def analyze_data(self, query: str) -> str:
        """执行 BI 数据分析"""
        if not self.is_ready():
            return "BI 分析 Agent 未准备就绪"
        
        try:
            result = await self.agent.run(query)
            return result
        except Exception as e:
            logger.error(f"BI 数据分析失败: {e}", exc_info=True)
            return f"BI 数据分析出错: {str(e)}"
    
    async def generate_chart(self, chart_request: str) -> str:
        """生成图表代码（通过子 Agent）"""
        if not self.chart_generation_agent or not self.chart_generation_agent.is_ready():
            return "图表代码生成子 Agent 未准备就绪"
        
        try:
            result = await self.chart_generation_agent.generate_chart_code(chart_request)
            return result
        except Exception as e:
            logger.error(f"通过子 Agent 生成图表代码失败: {e}", exc_info=True)
            return f"图表代码生成出错: {str(e)}"
    
    def get_chart_generation_agent(self):
        """获取图表代码生成子 Agent 实例"""
        return self.chart_generation_agent