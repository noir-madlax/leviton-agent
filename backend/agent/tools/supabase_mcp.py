"""
Supabase MCP 工具管理器 - 负责初始化、筛选和管理 Supabase MCP 工具
支持多例模式，每个 Agent 可以有独立的 MCP 连接配置
"""
import logging
from typing import List, Optional, Dict, Any
from config import settings

logger = logging.getLogger(__name__)

class SupabaseMCPToolManager:
    """Supabase MCP 工具管理器类 - 多例模式"""
    
    def __init__(self, agent_id: str, mcp_config: Optional[Dict[str, Any]] = None):
        """
        初始化 MCP 工具管理器
        
        Args:
            agent_id: Agent 标识符，用于日志和调试
            mcp_config: MCP 连接配置，包含以下可选参数：
                - command: 启动命令，默认 "npx"
                - base_args: 基础参数列表，默认 ["-y", "@supabase/mcp-server-supabase@latest"]
                - access_token: 访问令牌，默认使用 settings.MCP_ACCESS_TOKEN
                - project_id: Supabase 项目 ID（可选），将使用 --project-ref=<value> 格式
                - read_only: 是否启用只读模式，默认 True
                - extra_args: 额外参数列表，默认 []
        """
        self.agent_id = agent_id
        self.mcp_config = mcp_config or {}
        self.tool_collection_context = None
        self.tools = []
        self.init_error = None
        
        # 可配置的工具筛选设置
        self.tool_filter_mode = "all"  # "all", "whitelist", "blacklist", "category"
        self.allowed_tools = []
        self.blocked_tools = []
        self.allowed_categories = []
        
        logger.info(f"创建 Agent '{agent_id}' 的 MCP 工具管理器实例")
    
    def _get_server_parameters(self):
        """根据配置生成 MCP 服务器参数"""
        from mcp import StdioServerParameters
        import os
        
        # 默认配置
        command = self.mcp_config.get("command", "npx")
        base_args = self.mcp_config.get("base_args", ["-y", "@supabase/mcp-server-supabase@latest"])
        access_token = self.mcp_config.get("access_token", settings.MCP_ACCESS_TOKEN)
        
        # 构建参数列表
        args = list(base_args)  # 复制基础参数
        
        # 添加项目 ID（如果指定）- 使用正确的格式 --project-ref=value
        project_id = self.mcp_config.get("project_id")
        if project_id:
            args.append(f"--project-ref={project_id}")
        
        # 添加只读模式（推荐）
        if self.mcp_config.get("read_only", True):
            args.append("--read-only")
        
        # 添加额外参数
        extra_args = self.mcp_config.get("extra_args", [])
        args.extend(extra_args)
        
        # 设置环境变量而不是命令行参数
        env = {
            "SUPABASE_ACCESS_TOKEN": access_token
        }
        
        logger.info(f"Agent '{self.agent_id}' MCP 服务器参数: {command} {' '.join(args[:3])}...")
        
        return StdioServerParameters(command=command, args=args, env=env)
    
    def configure_tool_filter(self, 
                            mode: str = "all",
                            allowed_tools: List[str] = None,
                            blocked_tools: List[str] = None,
                            allowed_categories: List[str] = None):
        """配置工具筛选规则
        
        Args:
            mode: 筛选模式 - "all"(所有), "whitelist"(白名单), "blacklist"(黑名单), "category"(按分类)
            allowed_tools: 允许的工具名称列表（白名单模式）
            blocked_tools: 禁用的工具名称列表（黑名单模式）  
            allowed_categories: 允许的工具分类列表（分类模式）
        """
        self.tool_filter_mode = mode
        self.allowed_tools = allowed_tools or []
        self.blocked_tools = blocked_tools or []
        self.allowed_categories = allowed_categories or []
        
        logger.info(f"Agent '{self.agent_id}' 工具筛选配置已更新: mode={mode}")
        if allowed_tools:
            logger.info(f"Agent '{self.agent_id}' 允许的工具: {allowed_tools}")
        if blocked_tools:
            logger.info(f"Agent '{self.agent_id}' 禁用的工具: {blocked_tools}")
        if allowed_categories:
            logger.info(f"Agent '{self.agent_id}' 允许的分类: {allowed_categories}")
    
    def get_default_tool_categories(self) -> Dict[str, List[str]]:
        """获取默认的工具分类定义"""
        return {
            "database_query": [
                "execute_sql", "list_tables", "get_table_schema", 
                "list_columns", "describe_table", "get_table_info"
            ],
            "project_management": [
                "get_project_config", "list_projects", "create_project",
                "update_project", "delete_project"
            ],
            "logs_and_monitoring": [
                "get_logs", "get_function_logs", "get_api_logs",
                "get_realtime_logs", "get_storage_logs"
            ],
            "schema_management": [
                "create_table", "alter_table", "drop_table",
                "create_index", "drop_index"
            ],
            "auth_management": [
                "list_users", "create_user", "update_user", 
                "delete_user", "get_user_by_id"
            ],
            "storage_management": [
                "list_buckets", "create_bucket", "delete_bucket",
                "upload_file", "download_file", "delete_file"
            ]
        }
    
    def _should_include_tool(self, tool) -> bool:
        """判断是否应该包含指定工具"""
        tool_name = getattr(tool, 'name', str(tool))
        
        if self.tool_filter_mode == "all":
            return True
        elif self.tool_filter_mode == "whitelist":
            return tool_name in self.allowed_tools
        elif self.tool_filter_mode == "blacklist":
            return tool_name not in self.blocked_tools
        elif self.tool_filter_mode == "category":
            # 检查工具是否在允许的分类中
            categories = self.get_default_tool_categories()
            for category in self.allowed_categories:
                if category in categories and tool_name in categories[category]:
                    return True
            return False
        else:
            logger.warning(f"Agent '{self.agent_id}' 未知的工具筛选模式: {self.tool_filter_mode}, 使用所有工具")
            return True
    
    def _filter_tools(self, all_tools) -> List:
        """根据配置筛选工具"""
        if self.tool_filter_mode == "all":
            filtered_tools = list(all_tools)
        else:
            filtered_tools = [
                tool for tool in all_tools 
                if self._should_include_tool(tool)
            ]
        
        logger.info(f"Agent '{self.agent_id}' 工具筛选结果: 从 {len(all_tools)} 个工具中选择了 {len(filtered_tools)} 个")
        
        # 打印选中的工具名称
        selected_tool_names = [getattr(tool, 'name', str(tool)) for tool in filtered_tools]
        logger.info(f"Agent '{self.agent_id}' 已选择的工具: {selected_tool_names}")
        
        return filtered_tools
    
    async def initialize_mcp_tools(self) -> bool:
        """初始化 Supabase MCP 工具集"""
        logger.info(f"开始为 Agent '{self.agent_id}' 初始化 MCP 工具集...")
        
        try:
            from smolagents import ToolCollection
            
            # 获取配置化的服务器参数
            server_parameters = self._get_server_parameters()
            
            logger.info(f"Agent '{self.agent_id}' 正在连接 MCP 服务器...")
            self.tool_collection_context = ToolCollection.from_mcp(
                server_parameters, 
                trust_remote_code=True
            )
            tool_collection = self.tool_collection_context.__enter__()
            
            # 应用工具筛选
            self.tools = self._filter_tools(tool_collection.tools)
            
            logger.info(f"Agent '{self.agent_id}' MCP 工具集初始化成功，可用工具数量: {len(self.tools)}")
            return True
            
        except Exception as e:
            self.init_error = str(e)
            logger.error(f"Agent '{self.agent_id}' MCP 工具集初始化失败: {e}", exc_info=True)
            return False
    
    def get_tools(self) -> List:
        """获取筛选后的工具列表"""
        return self.tools
    
    def get_tool_names(self) -> List[str]:
        """获取工具名称列表"""
        return [getattr(tool, 'name', str(tool)) for tool in self.tools]
    
    def get_tool_info(self) -> List[Dict[str, Any]]:
        """获取工具详细信息列表，用于调试和分析"""
        tools_info = []
        for tool in self.tools:
            tool_info = {
                "name": getattr(tool, 'name', 'Unknown'),
                "description": getattr(tool, 'description', 'No description'),
                "parameters": getattr(tool, 'parameters', {}),
            }
            tools_info.append(tool_info)
        return tools_info
    
    def print_tool_info(self):
        """打印所有工具信息，用于调试"""
        tools_info = self.get_tool_info()
        logger.info(f"Agent '{self.agent_id}' 当前可用的 MCP 工具:")
        for i, tool in enumerate(tools_info, 1):
            logger.info(f"{i}. {tool['name']}: {tool['description']}")
    
    def is_initialized(self) -> bool:
        """检查工具是否已初始化"""
        return len(self.tools) > 0 and self.tool_collection_context is not None
    
    def get_init_error(self) -> Optional[str]:
        """获取初始化错误信息"""
        return self.init_error
    
    async def initialize_with_preset(self, preset_name: str, debug: bool = True) -> List:
        """使用预设配置一键初始化 MCP 工具
        
        Args:
            preset_name: 预设名称，支持的值：
                - "safe_read_only": 安全只读模式
                - "database_only": 仅数据库操作
                - "full_database_management": 完整数据库管理
                - "project_management_only": 仅项目管理
                - "exclude_destructive": 排除破坏性操作
                - "all": 所有工具
            debug: 是否打印调试信息
            
        Returns:
            List: 筛选后的工具列表
            
        Raises:
            Exception: 当预设名称不存在或初始化失败时
        """
        logger.info(f"开始使用预设 '{preset_name}' 为 Agent '{self.agent_id}' 初始化 MCP 工具...")
        
        # 预设配置映射
        preset_mapping = {
            "safe_read_only": MCPToolPresets.safe_read_only,
            "database_only": MCPToolPresets.database_only,
            "full_database_management": MCPToolPresets.full_database_management,
            "project_management_only": MCPToolPresets.project_management_only,
            "exclude_destructive": MCPToolPresets.exclude_destructive,
            "all": lambda: {"mode": "all"}
        }
        
        # 检查预设是否存在
        if preset_name not in preset_mapping:
            available_presets = list(preset_mapping.keys())
            raise ValueError(f"未知的预设名称 '{preset_name}'。可用预设: {available_presets}")
        
        # 获取预设配置
        preset_func = preset_mapping[preset_name]
        preset_config = preset_func()
        
        # 应用配置
        self.configure_tool_filter(**preset_config)
        
        # 初始化工具
        success = await self.initialize_mcp_tools()
        if not success:
            raise Exception(f"Agent '{self.agent_id}' MCP 工具初始化失败: {self.get_init_error()}")
        
        # 可选的调试信息
        if debug:
            self.print_tool_info()
        
        logger.info(f"✅ Agent '{self.agent_id}' 预设 '{preset_name}' 初始化完成，可用工具数量: {len(self.tools)}")
        return self.tools
    
    def cleanup(self):
        """清理 MCP 工具集资源"""
        logger.info(f"正在清理 Agent '{self.agent_id}' 的 MCP 工具集资源...")
        if self.tool_collection_context:
            try:
                self.tool_collection_context.__exit__(None, None, None)
                logger.info(f"Agent '{self.agent_id}' MCP 工具集资源已释放")
            except Exception as e:
                logger.error(f"Agent '{self.agent_id}' 释放 MCP 工具集资源时出错: {e}", exc_info=True)
        
        # 重置状态
        self.tools = []
        self.tool_collection_context = None


# 预定义的常用工具配置
class MCPToolPresets:
    """MCP 工具预设配置"""
    
    @staticmethod
    def database_only():
        """只包含数据库查询相关工具"""
        return {
            "mode": "category",
            "allowed_categories": ["database_query"]
        }
    
    @staticmethod
    def safe_read_only():
        """只包含安全的只读工具"""
        return {
            "mode": "whitelist",
            "allowed_tools": [
                "execute_sql",      # SQL查询（需要确保只读）
                "list_tables",      # 列出表
                "get_table_schema", # 获取表结构
                "list_columns",     # 列出字段
                "get_project_config" # 获取项目配置
            ]
        }
    
    @staticmethod
    def full_database_management():
        """包含完整的数据库管理工具"""
        return {
            "mode": "category", 
            "allowed_categories": ["database_query", "schema_management"]
        }
    
    @staticmethod
    def project_management_only():
        """只包含项目管理工具"""
        return {
            "mode": "category",
            "allowed_categories": ["project_management"]
        }
    
    @staticmethod
    def exclude_destructive():
        """排除破坏性操作工具"""
        return {
            "mode": "blacklist",
            "blocked_tools": [
                "drop_table", "delete_project", "delete_user",
                "drop_index", "delete_bucket", "delete_file"
            ]
        }


# 工厂函数
def create_supabase_mcp_manager(agent_id: str, mcp_config: Optional[Dict[str, Any]] = None) -> SupabaseMCPToolManager:
    """创建 Supabase MCP 工具管理器实例
    
    Args:
        agent_id: Agent 标识符
        mcp_config: MCP 连接配置
        
    Returns:
        SupabaseMCPToolManager: 工具管理器实例
    """
    return SupabaseMCPToolManager(agent_id, mcp_config)

# 兼容性函数（保持向后兼容）
def get_supabase_mcp_manager(agent_id: str = "default", mcp_config: Optional[Dict[str, Any]] = None) -> SupabaseMCPToolManager:
    """获取 Supabase MCP 工具管理器实例（兼容性函数）
    
    注意：这个函数每次调用都会创建新实例，不再是单例模式
    
    Args:
        agent_id: Agent 标识符，默认为 "default"
        mcp_config: MCP 连接配置
        
    Returns:
        SupabaseMCPToolManager: 工具管理器实例
    """
    logger.warning("get_supabase_mcp_manager() 已废弃，建议使用 create_supabase_mcp_manager()")
    return create_supabase_mcp_manager(agent_id, mcp_config) 