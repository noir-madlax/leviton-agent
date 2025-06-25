"""
测试图表代码生成 Agent 的简单脚本
"""
import asyncio
import logging
from agent.core.chart_generation_agent import ChartGenerationAgent

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_chart_generation_agent():
    """测试图表代码生成 Agent"""
    logger.info("开始测试图表代码生成 Agent...")
    
    # 创建图表代码生成 Agent
    chart_agent = ChartGenerationAgent()
    
    # 初始化 Agent
    init_success = await chart_agent.initialize()
    
    if not init_success:
        logger.error(f"图表代码生成 Agent 初始化失败: {chart_agent.get_init_error()}")
        return
    
    logger.info("图表代码生成 Agent 初始化成功")
    
    # 测试生成简单的图表代码
    test_request = """
    请生成一个使用 Chart.js 的柱状图代码，展示以下数据：
    - 标签: ['苹果', '香蕉', '橙子', '葡萄']
    - 数据: [12, 19, 3, 5]
    - 标题: "水果销量统计"
    
    请生成完整的 HTML 和 JavaScript 代码。
    """
    
    logger.info("发送测试请求...")
    result = await chart_agent.generate_chart_code(test_request)
    
    logger.info("收到结果:")
    logger.info("=" * 50)
    print(result)
    logger.info("=" * 50)
    
    # 清理资源
    chart_agent.cleanup()
    logger.info("测试完成")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_chart_generation_agent()) 