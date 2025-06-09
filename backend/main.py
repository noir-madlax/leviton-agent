from fastapi import FastAPI, Response, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Optional
from config import settings
from tools import ProductQueryTool, ReviewQueryTool, get_data_files_status, test_tools

# 配置日志
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Leviton Agent API",
    description="基于 smolagents 的智能代理 API",
    version="1.0.0"
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化 Agent 变量
agent = None
init_error = None

# 延迟初始化 smolagents 的 CodeAgent
def init_agent():
    global agent, init_error
    try:
        logger.info("开始初始化 Agent...")
        from smolagents import CodeAgent, OpenAIServerModel
        
        logger.info(f"使用模型: {settings.MODEL_ID}")
        model = OpenAIServerModel(
            model_id="google/gemini-2.5-flash-preview-05-20",
            api_base="https://openrouter.ai/api/v1",
            api_key=settings.API_KEY
        )
        
        logger.info("初始化工具...")
        # search_tool = DuckDuckGoSearchTool()
        product_tool = ProductQueryTool()
        review_tool = ReviewQueryTool()
        
        logger.info("创建 CodeAgent...")
        agent = CodeAgent(
            tools=[ product_tool, review_tool], 
            model=model
            )
        
        logger.info("Agent 初始化成功，包含以下工具:")
        logger.info("- DuckDuckGoSearchTool: 网络搜索")
        logger.info("- ProductQueryTool: 商品信息查询")
        logger.info("- ReviewQueryTool: 评论和方面分析查询")
        return True
    except Exception as e:
        init_error = str(e)
        logger.error(f"Agent 初始化失败: {e}")
        return False

# FastAPI 启动事件 - 在应用启动时初始化 Agent
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的初始化操作"""
    logger.info("FastAPI 应用启动，正在初始化 Agent...")
    init_agent()

async def stream_agent_response(query: str):
    """
    运行 smolagents 代理并通过 SSE 流式输出结果
    """
    if not agent:
        if init_error:
            yield f"data: {json.dumps({'error': f'Agent 初始化失败: {init_error}'}, ensure_ascii=False)}\n\n"
        else:
            yield f"data: {json.dumps({'error': 'Agent 未初始化'}, ensure_ascii=False)}\n\n"
        return
    
    try:
        logger.info(f"开始处理查询: {query}")
        
        # 发送开始信号
        yield f"data: {json.dumps({'status': 'started', 'message': '开始处理查询...'}, ensure_ascii=False)}\n\n"
        
        # 发送调试信息
        yield f"data: {json.dumps({'status': 'debug', 'message': '准备调用 agent.run...'}, ensure_ascii=False)}\n\n"
        
        try:
            # 运行代理任务，设置超时
            logger.info("正在调用 agent.run...")
            result = await asyncio.wait_for(
                asyncio.to_thread(agent.run, query),
                timeout=settings.AGENT_TIMEOUT
            )
            logger.info(f"agent.run 执行完成，结果类型: {type(result)}")
            
            # 发送调试信息
            yield f"data: {json.dumps({'status': 'debug', 'message': f'agent.run 执行完成，结果类型: {type(result).__name__}'}, ensure_ascii=False)}\n\n"
            
        except asyncio.TimeoutError:
            logger.error(f"agent.run 执行超时 ({settings.AGENT_TIMEOUT}秒)")
            yield f"data: {json.dumps({'status': 'error', 'error': f'Agent 执行超时 ({settings.AGENT_TIMEOUT}秒)'}, ensure_ascii=False)}\n\n"
            return
        except Exception as agent_error:
            logger.error(f"agent.run 执行失败: {agent_error}")
            yield f"data: {json.dumps({'status': 'error', 'error': f'Agent 执行失败: {str(agent_error)}'}, ensure_ascii=False)}\n\n"
            return
        
        # 发送进度信息
        yield f"data: {json.dumps({'status': 'processing', 'message': '正在分析结果...'}, ensure_ascii=False)}\n\n"
        
        # 将结果分块发送
        if isinstance(result, str):
            # 按句号分割结果，更自然的分块方式
            sentences = result.split('。')
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    chunk_data = {
                        'status': 'streaming',
                        'message': sentence.strip() + ('。' if i < len(sentences) - 1 else ''),
                        'chunk_index': i
                    }
                    yield f"data: {json.dumps(chunk_data, ensure_ascii=False)}\n\n"
                    await asyncio.sleep(settings.STREAM_DELAY)  # 控制流速
        else:
            # 如果结果不是字符串，直接发送
            yield f"data: {json.dumps({'status': 'streaming', 'message': str(result)}, ensure_ascii=False)}\n\n"
        
        # 发送完成信号
        yield f"data: {json.dumps({'status': 'completed', 'message': '[DONE]'}, ensure_ascii=False)}\n\n"
        
    except Exception as e:
        logger.error(f"处理查询时出错: {e}")
        yield f"data: {json.dumps({'status': 'error', 'error': str(e)}, ensure_ascii=False)}\n\n"

@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    return {
        "message": "Leviton Agent API",
        "version": "1.0.0",
        "status": "运行中" if agent else "Agent 未初始化",
        "model_id": settings.MODEL_ID,
        "init_error": init_error if init_error else None,
        "available_tools": [
            "DuckDuckGoSearchTool - 网络搜索",
            "ProductQueryTool - 商品信息查询", 
            "ReviewQueryTool - 评论和方面分析查询"
        ] if agent else []
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "model_id": settings.MODEL_ID,
        "init_error": init_error if init_error else None,
        "data_files_status": get_data_files_status(),
        "config": {
            "host": settings.HOST,
            "port": settings.PORT,
            "debug": settings.DEBUG
        }
    }

@app.get("/init-agent")
async def initialize_agent():
    """手动初始化 Agent"""
    success = init_agent()
    return {
        "success": success,
        "agent_ready": agent is not None,
        "init_error": init_error if init_error else None
    }

@app.get("/test-tools")
async def test_tools_endpoint():
    """测试工具功能"""
    return test_tools()

@app.get("/agent-stream")
async def agent_stream(
    query: str = Query(..., description="要处理的查询内容", min_length=1)
):
    """
    SSE 端点，接收查询并流式返回 smolagents 的输出
    """
    if not query.strip():
        return Response(
            content=json.dumps({"error": "查询内容不能为空"}, ensure_ascii=False),
            status_code=400,
            media_type="application/json"
        )
    
    return StreamingResponse(
        stream_agent_response(query),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

@app.post("/agent-query")
async def agent_query(request: dict):
    """
    POST 端点，用于处理更复杂的查询请求
    """
    if not agent:
        return {"error": "Agent 未初始化", "init_error": init_error}
    
    query = request.get("query", "")
    if not query.strip():
        return {"error": "查询内容不能为空"}
    
    try:
        result = await asyncio.to_thread(agent.run, query)
        return {
            "status": "success",
            "query": query,
            "result": result
        }
    except Exception as e:
        logger.error(f"处理查询时出错: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"准备启动服务，HOST: {settings.HOST}, PORT: {settings.PORT}")
    logger.info(f"调试模式: {settings.DEBUG}")
    
    try:
        uvicorn.run(
            "main:app",
            host=settings.HOST,
            port=settings.PORT,
            reload=settings.DEBUG,
            log_level=settings.LOG_LEVEL.lower()
        )
    except KeyboardInterrupt:
        logger.info("服务被用户中断")
    except Exception as e:
        logger.error(f"启动服务失败: {e}") 