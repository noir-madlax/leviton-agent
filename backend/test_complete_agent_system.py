"""
测试完整的多 Agent 系统（包含新的图表代码生成 Agent）
"""
import asyncio
import logging
from agent.core.agent_manager import AgentManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_complete_agent_system():
    """测试完整的多 Agent 系统"""
    logger.info("开始测试完整的多 Agent 系统...")
    
    # 创建 Agent 管理器
    agent_manager = AgentManager()
    
    # 初始化系统
    logger.info("初始化多 Agent 系统...")
    init_success = await agent_manager.initialize_agent()
    
    if not init_success:
        logger.error(f"多 Agent 系统初始化失败: {agent_manager.get_init_error()}")
        return
    
    logger.info("多 Agent 系统初始化成功")
    
    # 检查各个 Agent 是否准备就绪
    logger.info(f"系统准备状态: {agent_manager.is_ready()}")
    
    # 获取各个 Agent 实例
    manager_agent = agent_manager.get_manager_agent()
    bi_agent = agent_manager.get_bi_agent()
    chart_generation_agent = agent_manager.get_chart_generation_agent()
    
    logger.info("Agent 实例检查:")
    logger.info(f"- 管理 Agent: {manager_agent is not None}")
    logger.info(f"- BI 分析 Agent: {bi_agent is not None and bi_agent.is_ready()}")
    logger.info(f"- 图表代码生成 Agent: {chart_generation_agent is not None and chart_generation_agent.is_ready()}")
    
    # 测试系统查询（通过管理 Agent）
    test_query = """
    你好，我是一个多Agent系统测试。
    请简单介绍一下你能做什么，以及你管理的其他Agent的功能。
    """
    
    logger.info("发送测试查询...")
    try:
        result = await agent_manager.run_query(test_query)
        logger.info("查询结果:")
        logger.info("=" * 50)
        print(result)
        logger.info("=" * 50)
    except Exception as e:
        logger.error(f"查询失败: {e}")
    
    # 清理资源
    logger.info("清理系统资源...")
    agent_manager.cleanup()
    logger.info("测试完成")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_complete_agent_system()) 