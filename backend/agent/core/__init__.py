"""
Agent 核心模块 - 包含 Agent 管理器和监控功能
"""

from .agent_manager import AgentManager, get_agent_manager
from ..monitor import initialize_phoenix_monitoring

__all__ = [
    'AgentManager',
    'get_agent_manager', 
    'initialize_phoenix_monitoring'
] 