from fastapi import FastAPI, Response, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Optional
from contextlib import asynccontextmanager
from config import settings
from tools import ProductQueryTool, ReviewQueryTool, get_data_files_status, test_tools
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor

# 配置日志
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# Agent 和工具集上下文将由 lifespan 管理
agent = None
init_error = None
tool_collection_context = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """在应用启动时初始化 Agent，在关闭时清理资源。"""
    global agent, init_error, tool_collection_context

    # 初始化监控
    if settings.PHOENIX_ENDPOINT:
        try:
            tracer_provider = register(
                project_name=settings.PROJECT_NAME,
                endpoint=settings.PHOENIX_ENDPOINT
            )
            SmolagentsInstrumentor().instrument(tracer_provider=tracer_provider)
            logger.info(f"Phoenix 监控已启动，项目: {settings.PROJECT_NAME}, 端点: {settings.PHOENIX_ENDPOINT}")
        except Exception as e:
            logger.error(f"Phoenix 监控初始化失败: {e}", exc_info=True)
    else:
        logger.warning("未配置 PHOENIX_ENDPOINT，Phoenix 监控未启动。")
    
    logger.info("FastAPI 应用启动，开始初始化 Agent...")
    
    try:
        from smolagents import ToolCollection,ToolCallingAgent, CodeAgent, OpenAIServerModel
        from mcp import StdioServerParameters
        
        logger.info(f"使用模型: {settings.MODEL_ID}")
        model = OpenAIServerModel(
            model_id=settings.MODEL_ID,
            api_base="https://openrouter.ai/api/v1",
            api_key=settings.API_KEY
        )
        
        logger.info("初始化工具...")
        product_tool = ProductQueryTool()
        review_tool = ReviewQueryTool()

        server_parameters = StdioServerParameters(
            command="npx",
            args=["-y", 
                  "@supabase/mcp-server-supabase@latest",
                  "--access-token",
                  settings.MCP_ACCESS_TOKEN]
        )

        logger.info("初始化 ToolCollection...")
        tool_collection_context = ToolCollection.from_mcp(server_parameters, trust_remote_code=True)
        # 手动进入上下文
        tool_collection = tool_collection_context.__enter__()

        # all_tools = [product_tool, review_tool, *tool_collection.tools]
        all_tools = [ *tool_collection.tools]

        logger.info("创建 CodeAgent...")
        agent = CodeAgent(
            tools=all_tools, 
            model=model,
            max_steps=settings.MAX_ITERATIONS,
            additional_authorized_imports = ['json']
        )

        logger.info(f"Agent 初始化成功，加载的工具: {agent.tools}")

    except Exception as e:
        init_error = str(e)
        logger.error(f"Agent 初始化失败: {e}", exc_info=True)

    yield

    logger.info("FastAPI 应用关闭，正在释放资源...")
    if tool_collection_context:
        try:
            tool_collection_context.__exit__(None, None, None)
            logger.info("工具集资源已释放。")
        except Exception as e:
            logger.error(f"释放工具集资源时出错: {e}", exc_info=True)


app = FastAPI(
    title="Leviton Agent API",
    description="基于 smolagents 的智能代理 API",
    version="1.0.0",
    lifespan=lifespan
)

# 添加 CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 辅助函数：从数据库获取 prompt
def get_prompt_from_database(prompt_id: int = 1) -> str:
    """从数据库获取 prompt 内容"""
    if not agent:
        logger.warning("Agent 未初始化，无法访问数据库")
        return None
    
    try:
        logger.info(f"正在从数据库查询 prompt (ID: {prompt_id})...")
        
        # 使用 agent 执行数据库查询
        query_sql = f"SELECT prompt FROM product_prompt WHERE id = {prompt_id} LIMIT 1;"
        result = agent.run(f"请使用MCP工具执行以下SQL查询并直接返回prompt字段的内容：{query_sql}")
        
        # 解析结果
        if result and isinstance(result, str) and len(result.strip()) > 100:
            logger.info(f"成功从数据库获取 prompt，长度: {len(result)} 字符")
            return result.strip()
        else:
            logger.warning(f"数据库查询返回的 prompt 内容无效: {result}")
            return None
            
    except Exception as e:
        logger.error(f"从数据库查询 prompt 失败: {e}")
        return None

# 辅助函数：读取 prompt（优先数据库，兜底文件）
def prepare_query_with_prompt(query: str) -> str:
    """优先从数据库读取 prompt，失败时从文件读取"""
    import os
    
    # 1. 优先尝试从数据库获取 prompt
    db_prompt = get_prompt_from_database(prompt_id=1)
    if db_prompt:
        complete_query = db_prompt + "\n\n 用户的问题如下：" + query
        logger.info(f"使用数据库 prompt，长度: {len(db_prompt)} 字符")
        return complete_query
    
    # 2. 数据库获取失败，回退到文件读取
    logger.warning("数据库获取 prompt 失败，回退到文件读取")
    
    prompt_dir = os.path.join(os.path.dirname(__file__), "prompt")
    # 定义要加载的 prompt 文件及其顺序
    prompt_files = [
        "agent-prompt-by-step.md"
    ]
    
    prompt_contents = []
    
    for file_name in prompt_files:
        prompt_file_path = os.path.join(prompt_dir, file_name)
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                prompt_contents.append(f.read())
            logger.info(f"成功读取 prompt 文件: {file_name}")
        except FileNotFoundError:
            logger.warning(f"找不到 prompt 文件: {file_name}，已跳过")
        except Exception as e:
            logger.warning(f"读取 prompt 文件 {file_name} 失败: {e}，已跳过")

    if not prompt_contents:
        logger.warning("所有 prompt 文件都读取失败，将使用原始查询")
        return query

    complete_prompt = "\n\n".join(prompt_contents)
    complete_query = complete_prompt + "\n\n 用户的问题如下：" + query
    logger.info(f"使用文件 prompt，已成功拼接 {len(prompt_contents)} 个 prompt 文件，总 prompt 长度: {len(complete_prompt)} 字符")
    return complete_query

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
        
        try:
            # 准备完整的查询（包含 prompt）
            complete_query = prepare_query_with_prompt(query)
            
            # 运行代理任务，设置超时
            logger.info("正在调用 agent.run...")
            result = await asyncio.wait_for(
                asyncio.to_thread(agent.run, complete_query),
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
        


        def is_valid_json(text: str) -> bool:
            try:
                json.loads(text)
                return True
            except json.JSONDecodeError:
                return False

        if is_valid_json(result):
            logger.info("结果成功解析为 JSON 格式！！！！")
            result = json.dumps(json.loads(result), ensure_ascii=False)
        else:
            logger.info("结果不是有效的 JSON 格式，将作为普通字符串处理")


        # 删除结果中的换行符（临时处理）
        # logger.info(f"去除换行符前 result...{result}")
        # result = result.replace("\n", "")
        # logger.info(f"去除换行符后 result...{result}")

        # 将结果分块发送
        if is_valid_json(result):
            yield f"data: {json.dumps({'status': 'streaming', 'message': str(result)}, ensure_ascii=False)}\n\n"
        elif isinstance(result, str):
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
        "available_tools": agent.tools if agent else []
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    # 检查 prompt 数据源状态
    prompt_source_status = {
        "database_available": False,
        "file_available": False,
        "current_source": "unknown"
    }
    
    # 检查数据库是否可用
    try:
        if agent:
            db_prompt = get_prompt_from_database(prompt_id=1)
            if db_prompt:
                prompt_source_status["database_available"] = True
                prompt_source_status["current_source"] = "database"
    except Exception as e:
        logger.debug(f"数据库 prompt 检查失败: {e}")
    
    # 检查文件是否可用
    try:
        import os
        prompt_file_path = os.path.join(os.path.dirname(__file__), "prompt", "agent-prompt-by-step.md")
        if os.path.exists(prompt_file_path):
            prompt_source_status["file_available"] = True
            if prompt_source_status["current_source"] == "unknown":
                prompt_source_status["current_source"] = "file"
    except Exception as e:
        logger.debug(f"文件 prompt 检查失败: {e}")
    
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "model_id": settings.MODEL_ID,
        "init_error": init_error if init_error else None,
        "data_files_status": get_data_files_status(),
        "prompt_source": prompt_source_status,
        "config": {
            "host": settings.HOST,
            "port": settings.PORT,
            "debug": settings.DEBUG,
            "max_iterations": settings.MAX_ITERATIONS,
            "agent_timeout": settings.AGENT_TIMEOUT
        }
    }

@app.get("/init-agent")
async def initialize_agent():
    """手动初始化 Agent (已弃用)"""
    return {
        "success": False,
        "message": "Agent 初始化已与应用生命周期绑定，此端点已弃用。",
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
        # 准备完整的查询（包含 prompt）
        complete_query = prepare_query_with_prompt(query)
        
        result = await asyncio.to_thread(agent.run, complete_query)
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