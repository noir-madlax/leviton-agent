"""
测试 system_prompt 追加功能的脚本
"""
import asyncio
import logging
from agent.core.agent_manager import get_agent_manager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_system_prompt():
    """测试 system_prompt 追加功能"""
    agent_manager = get_agent_manager()
    
    try:
        # 初始化 agent
        logger.info("开始初始化 Agent...")
        success = await agent_manager.initialize_agent()
        
        if success:
            logger.info("Agent 初始化成功")
            
            # 获取当前的 system_prompt
            current_prompt = agent_manager.get_current_system_prompt()
            logger.info(f"当前 system_prompt 长度: {len(current_prompt)} 字符")
            
            # 显示前500个字符作为预览
            logger.info(f"System prompt 预览:\n{current_prompt[:500]}...")
            
            # 测试重新加载功能
            logger.info("测试重新加载 system_prompt...")
            await agent_manager.reload_system_prompt_from_database()
            
            # 再次获取并比较
            updated_prompt = agent_manager.get_current_system_prompt()
            logger.info(f"更新后 system_prompt 长度: {len(updated_prompt)} 字符")
            
        else:
            init_error = agent_manager.get_init_error()
            logger.error(f"Agent 初始化失败: {init_error}")
            
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}", exc_info=True)
    finally:
        # 清理资源
        agent_manager.cleanup()

if __name__ == "__main__":
    asyncio.run(test_system_prompt()) 