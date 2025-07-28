"""
Agent 核心模块 - 包含 Agent 管理器和监控功能
"""

from .agent_manager import AgentManager, get_agent_manager
# from .extend_fields_agent import ExtendFieldsAgent  # 暂时注释掉，不启用扩展字段 Agent
from ..monitor import initialize_phoenix_monitoring

__all__ = [
    'AgentManager',
    'get_agent_manager',
    # 'ExtendFieldsAgent',  # 暂时注释掉，不启用扩展字段 Agent
    'initialize_phoenix_monitoring'
] 