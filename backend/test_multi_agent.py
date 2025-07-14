"""
测试多 Agent 架构
"""
import asyncio
import logging
import os
import sys

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agent.core.agent_manager import AgentManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_multi_agent_system():
    """测试多 Agent 系统"""
    print("🚀 开始测试多 Agent 系统...")
    
    # 创建 Agent 管理器
    agent_manager = AgentManager()
    
    try:
        # 初始化多 Agent 系统
        print("📡 初始化多 Agent 系统...")
        success = await agent_manager.initialize_agent()
        
        if not success:
            print(f"❌ 初始化失败: {agent_manager.get_init_error()}")
            return
        
        print("✅ 多 Agent 系统初始化成功!")
        
        # 检查系统状态
        print(f"🔍 系统准备状态: {agent_manager.is_ready()}")
        print(f"🎯 管理 Agent: {type(agent_manager.get_manager_agent()).__name__}")
        print(f"💾 BI 分析 Agent: {type(agent_manager.get_bi_agent().get_agent()).__name__}")
        
        # 测试简单查询
        print("\n📋 测试简单查询...")
        test_query = "你好，请告诉我你的身份和能力"
        result = await agent_manager.run_query(test_query)
        print(f"📨 查询结果: {result[:200]}..." if len(result) > 200 else f"📨 查询结果: {result}")
        
        # 测试数据库相关查询（如果可能）
        print("\n🗄️ 测试数据库查询委托...")
        db_query = "请查询一下数据库中有什么表格"
        db_result = await agent_manager.run_query(db_query)
        print(f"💽 数据库查询结果: {db_result[:300]}..." if len(db_result) > 300 else f"💽 数据库查询结果: {db_result}")
        
        # 测试通用 system_prompt 方法
        print("\n🔧 测试通用 system_prompt 功能...")
        # 为数据库 Agent 重新加载 system_prompt (ID=2)
        bi_agent = agent_manager.get_bi_agent()
        reload_result = await bi_agent.reload_system_prompt(prompt_id=2)
        print(f"🔄 BI 分析 Agent system_prompt 重新加载结果: {reload_result}")
        
        # 为管理 Agent 重新加载 system_prompt (ID=1)
        manager_reload_result = await agent_manager.reload_system_prompt_from_database(prompt_id=1)
        print(f"🔄 管理 Agent system_prompt 重新加载结果: {manager_reload_result}")
        
    except Exception as e:
        print(f"❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 清理资源
        print("\n🧹 清理资源...")
        agent_manager.cleanup()
        print("✅ 测试完成!")

if __name__ == "__main__":
    asyncio.run(test_multi_agent_system()) 