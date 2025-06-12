import asyncio
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)

async def test_agent():
    try:
        from smolagents import ToolCollection,CodeAgent, OpenAIServerModel
        from tools import ProductQueryTool, ReviewQueryTool
        from config import settings
        from mcp import StdioServerParameters
        
        print('开始测试 agent.run...')
        
        model = OpenAIServerModel(
            model_id='openai/gpt-4o',
            api_base='https://openrouter.ai/api/v1',
            api_key=settings.API_KEY,
        )
        
        mcp_access_token = os.getenv("MCP_ACCESS_TOKEN")
        if not mcp_access_token:
            raise ValueError("MCP_ACCESS_TOKEN not found in .env file")

        server_parameters = StdioServerParameters(
            command="npx",
            args=["-y", 
                  "@supabase/mcp-server-supabase@latest",
                  "--access-token",
                  mcp_access_token]
        )
        
        tool_collection = ToolCollection.from_mcp(server_parameters, trust_remote_code=True)
        agent = CodeAgent(tools=[ *tool_collection.tools], model=model, max_steps=settings.MAX_ITERATIONS)
        # 测试查询
        query = "supabase数据库中有哪些表."
        result = agent.run(query)
        # result = asyncio.to_thread(agent.run, query)
        print(f'查询结果: {result}')
        print('测试完成')

        
    except Exception as e:
        print(f'测试出错: {e}')
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_agent()) 