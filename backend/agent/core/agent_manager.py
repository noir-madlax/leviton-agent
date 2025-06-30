"""
多 Agent 管理器 - 负责多 Agent 系统的初始化、配置和生命周期管理
采用 Hugging Face smolagents 多 Agent 架构模式
"""
import logging
from typing import Optional
from config import settings
from agent.validators.chart_validator import check_reasoning_and_plot
from agent.core.database_agent import DatabaseAgent
from agent.core.chart_generation_agent import ChartGenerationAgent

# 导入HTTP请求拦截器（导入时自动激活网络请求监控）
from agent.monitor.http_interceptor import create_interceptor

logger = logging.getLogger(__name__)

# 创建HTTP拦截器实例，只监控请求（避免日志过多）
http_interceptor = create_interceptor(log_requests=False, 
                                      log_responses=False,
                                      max_body_length=12000)

class AgentManager:
    """多 Agent 管理器类"""
    
    def __init__(self):
        self.manager_agent = None  # 管理 Agent
        self.database_agent = None  # 数据库查询 Agent
        self.chart_generation_agent = None  # 图表代码生成 Agent
        self.init_error = None
    
    async def initialize_agent(self) -> bool:
        """初始化多 Agent 系统"""
        logger.info("FastAPI 应用启动，开始初始化多 Agent 系统...")
        
        try:
            from smolagents import CodeAgent, OpenAIServerModel, ToolCollection
            from mcp import StdioServerParameters
            
            logger.info(f"使用模型: {settings.MODEL_ID}")
            model = OpenAIServerModel(
                model_id=settings.MODEL_ID,
                api_base="https://openrouter.ai/api/v1",
                api_key=settings.API_KEY,
                stream_options={"include_usage": True},
                temperature=0.3
            )
            
            # 步骤1: 初始化数据库查询 Agent
            logger.info("初始化数据库查询 Agent...")
            self.database_agent = DatabaseAgent(agent_manager=self)  # 传递自身引用
            database_init_success = await self.database_agent.initialize()
            
            if not database_init_success:
                raise Exception(f"数据库 Agent 初始化失败: {self.database_agent.get_init_error()}")
            
            # 步骤2: 初始化图表代码生成 Agent
            logger.info("初始化图表代码生成 Agent...")
            self.chart_generation_agent = ChartGenerationAgent(agent_manager=self)  # 传递自身引用
            chart_init_success = await self.chart_generation_agent.initialize()
            
            if not chart_init_success:
                raise Exception(f"图表代码生成 Agent 初始化失败: {self.chart_generation_agent.get_init_error()}")
            
            # 步骤3: 创建管理 Agent（类似 HuggingFace demo 中的 manager_agent）

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

            logger.info("创建管理 Agent...")  
            self.manager_agent = CodeAgent(
                tools=database_tools, 
                model=model,
                # stream_outputs=True,
                managed_agents=[
                    # self.database_agent.get_agent()  # 管理数据库 Agent
                    self.chart_generation_agent.get_agent()  # 管理图表代码生成 Agent
                ],
                max_steps=settings.MAX_ITERATIONS,
                additional_authorized_imports=['json', 'time', 'numpy', 'pandas'],
                verbosity_level= 3,
                # final_answer_checks=[check_reasoning_and_plot]
            )
            
            # 追加自定义 system_prompt
            logger.info("追加自定义 system_prompt...")
            await self.append_custom_system_prompt(
                agent=self.manager_agent,
                prompt_id=12
            )

            logger.info("多 Agent 系统初始化成功")
            logger.info(f"- 管理 Agent: {type(self.manager_agent).__name__}")
            logger.info(f"- 数据库查询 Agent: {type(self.database_agent.get_agent()).__name__}")
            logger.info(f"- 图表代码生成 Agent: {type(self.chart_generation_agent.get_agent()).__name__}")
            
            # 打印整体 Agent 结构
            logger.info("多 Agent 系统结构:")
            self.manager_agent.visualize()
            
            return True

        except Exception as e:
            self.init_error = str(e)
            logger.error(f"多 Agent 系统初始化失败: {e}", exc_info=True)
            return False
    
    def _process_prompt_content(self, content: str) -> str:
        """智能处理 prompt 内容，保留代码示例但避免解析冲突"""
        try:
            import re
            
            # 首先替换双大括号，防止 smolagent 将其当成变量
            processed = content.replace('{{', '{ {').replace('}}', '} }')
            
            logger.info("已智能处理 prompt 内容，保护代码示例和双大括号")
            return processed
            
        except Exception as e:
            logger.warning(f"智能处理 prompt 内容时出错: {e}，使用原始内容")
            return content
    
    async def append_custom_system_prompt(self, agent, prompt_id: int):
        """通用方法：从数据库获取指定 ID 的 prompt 并追加到指定 agent 的 system_prompt
        
        Args:
            agent: 要更新 system_prompt 的 agent 实例
            prompt_id: 要获取的 prompt 记录 ID
            additional_instructions: 额外的指令文本（可选）
        """
        try:
            # 导入必要的模块
            from core.database.connection import get_supabase_client
            from core.repositories.product_prompt_repository import ProductPromptRepository
            from agent.services.product_prompt_service import ProductPromptService
            
            # 获取 Supabase 客户端
            supabase_client = get_supabase_client()
            
            # 创建仓库和服务实例
            repository = ProductPromptRepository(supabase_client)
            service = ProductPromptService(repository)
            
            # 获取指定 ID 的 prompt
            prompt_record = await service.get_prompt_by_id(prompt_id)
            
            if prompt_record and prompt_record.prompt:
                # 智能处理 prompt 内容，避免脚本解析错误
                processed_prompt = self._process_prompt_content(prompt_record.prompt)
                
                logger.info(f"获取到 ID {prompt_id} 的 system_prompt，长度: {len(processed_prompt)} 字符")

                # 更新指定 agent 的 system_prompt
                original_prompt = agent.prompt_templates["system_prompt"]
                
                # 组合最终的 prompt
                final_prompt = original_prompt + "\n\n" + processed_prompt
                
                # 追加自定义 prompt
                agent.prompt_templates["system_prompt"] = final_prompt
                
                logger.info(f"已成功追加 ID {prompt_id} 的 prompt 到 agent，总长度: {len(final_prompt)} 字符")
                logger.info(f"追加后的 prompt: {final_prompt}")
                return True
            else:
                logger.warning(f"未找到 ID {prompt_id} 的 prompt 或内容为空")
                return False
                
        except Exception as e:
            logger.error(f"追加自定义 system_prompt 失败: {e}", exc_info=True)
            return False
    
    def cleanup(self):
        """清理多 Agent 系统资源"""
        logger.info("FastAPI 应用关闭，正在释放多 Agent 系统资源...")
        if self.database_agent:
            try:
                self.database_agent.cleanup()
                logger.info("数据库 Agent 资源已释放")
            except Exception as e:
                logger.error(f"释放数据库 Agent 资源时出错: {e}", exc_info=True)
        
        if self.chart_generation_agent:
            try:
                self.chart_generation_agent.cleanup()
                logger.info("图表代码生成 Agent 资源已释放")
            except Exception as e:
                logger.error(f"释放图表代码生成 Agent 资源时出错: {e}", exc_info=True)
    
    def is_ready(self) -> bool:
        """检查多 Agent 系统是否准备就绪"""
        return (self.manager_agent is not None and 
                self.database_agent is not None and 
                self.database_agent.is_ready() and
                self.chart_generation_agent is not None and
                self.chart_generation_agent.is_ready())
    
    def get_agent(self):
        """获取管理 Agent 实例（对外接口保持兼容）"""
        return self.manager_agent
    
    def get_manager_agent(self):
        """获取管理 Agent 实例"""
        return self.manager_agent
    
    def get_database_agent(self):
        """获取数据库查询 Agent 实例"""
        return self.database_agent
    
    def get_chart_generation_agent(self):
        """获取图表代码生成 Agent 实例"""
        return self.chart_generation_agent
    
    def get_init_error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self.init_error
    
    def get_current_system_prompt(self) -> str:
        """获取管理 Agent 当前的 system_prompt"""
        if self.manager_agent:
            return self.manager_agent.prompt_templates["system_prompt"]
        return ""
    
    def update_system_prompt(self, new_prompt: str):
        """动态更新管理 Agent 的 system_prompt"""
        if self.manager_agent:
            self.manager_agent.prompt_templates["system_prompt"] = new_prompt
            logger.info("管理 Agent 的 system_prompt 已更新")
        else:
            logger.warning("管理 Agent 未初始化，无法更新 system_prompt")
    
    async def reload_system_prompt_from_database(self, agent=None, prompt_id: int = 1):
        """重新从数据库加载指定 ID 的 prompt 并更新指定 Agent 的 system_prompt
        
        Args:
            agent: 要更新的 agent 实例，默认为管理 Agent
            prompt_id: 要加载的 prompt ID，默认为 1
        """
        target_agent = agent or self.manager_agent
        
        if not target_agent:
            logger.warning("目标 Agent 未初始化，无法重新加载 system_prompt")
            return False
            
        try:
            # 重置为原始的 system_prompt
            from smolagents import CodeAgent, ToolCallingAgent
            
            # 根据 agent 类型创建临时实例获取默认 prompt
            if isinstance(target_agent, type(CodeAgent(tools=[], model=None))):
                temp_agent = CodeAgent(tools=[], model=None)
            else:
                temp_agent = ToolCallingAgent(tools=[], model=None)
                
            original_prompt = temp_agent.prompt_templates["system_prompt"]
            target_agent.prompt_templates["system_prompt"] = original_prompt
            
            # 重新追加自定义内容
            await self.append_custom_system_prompt(target_agent, prompt_id)
                
            logger.info(f"已重新从数据库加载并更新 Agent 的 system_prompt (prompt_id: {prompt_id})")
            return True
            
        except Exception as e:
            logger.error(f"重新加载 system_prompt 失败: {e}", exc_info=True)
            return False
    
    async def run_query(self, query: str) -> str:
        """运行查询（对外提供的统一接口）"""
        if not self.is_ready():
            return "多 Agent 系统未准备就绪"
        
        try:
            result = await self.manager_agent.run(query)
            return result
        except Exception as e:
            logger.error(f"查询执行失败: {e}", exc_info=True)
            return f"查询执行出错: {str(e)}"

# 全局 Agent 管理器实例
agent_manager = AgentManager()

def get_agent_manager() -> AgentManager:
    """获取 Agent 管理器实例"""
    return agent_manager 