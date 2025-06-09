import asyncio
import logging
logging.basicConfig(level=logging.INFO)

async def test_agent():
    try:
        from smolagents import CodeAgent, OpenAIServerModel
        from tools import ProductQueryTool, ReviewQueryTool
        from config import settings
        
        print('开始测试 agent.run...')
        
        model = OpenAIServerModel(
            model_id='openai/gpt-4o',
            api_base='https://openrouter.ai/api/v1',
            api_key=settings.API_KEY,
        )
        
        product_tool = ProductQueryTool()
        review_tool = ReviewQueryTool()
        
        agent = CodeAgent(tools=[product_tool, review_tool], model=model)
        
        # 测试查询
        query = 'Leviton 品牌有哪些产品？'
        print(f'执行查询: {query}')
        
        result = await asyncio.to_thread(agent.run, query)
        print(f'查询结果: {result}')
        print('测试完成')
        
    except Exception as e:
        print(f'测试出错: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent()) 