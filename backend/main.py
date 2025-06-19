from fastapi import FastAPI, Response, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Optional, List
from contextlib import asynccontextmanager
from backend.config import settings
from agent.tools import ProductQueryTool, ReviewQueryTool, get_data_files_status, test_tools
from phoenix.otel import register
from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from backend.product_segmentation.api import router as segmentation_router

# 导入 ORM 相关模块
from agent.dependencies import get_product_prompt_service
from core.models.product_prompt import ProductPromptCreate, ProductPromptUpdate, ProductPromptResponse
from agent.services.product_prompt_service import ProductPromptService

# 配置日志
logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
logger = logging.getLogger(__name__)

# 导入爬虫模块
try:
    from scraping import ScrapingOrchestrator
    SCRAPING_AVAILABLE = True
    logger.info("爬虫模块导入成功")
except ImportError as e:
    logger.error(f"爬虫模块导入失败: {e}")
    SCRAPING_AVAILABLE = False

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

# Register Product Segmentation endpoints
app.include_router(segmentation_router, prefix="/api/segmentation", tags=["Product Segmentation"])

# 辅助函数：读取 prompt 文件并拼接查询
async def prepare_query_with_prompt(query: str) -> str:
    """准备完整的查询，包含系统提示词"""
    try:
        # 直接创建服务实例，不使用依赖注入
        from core.database.connection import get_supabase_client
        from core.repositories.product_prompt_repository import ProductPromptRepository
        from agent.services.product_prompt_service import ProductPromptService
        
        # 获取 Supabase 客户端
        supabase_client = get_supabase_client()
        
        # 创建仓库和服务实例
        repository = ProductPromptRepository(supabase_client)
        service = ProductPromptService(repository)
        
        # 获取提示词
        prefixPrompt = await service.get_prompt_by_id(1)
        
        if not prefixPrompt:
            logger.warning("未找到 ID 为 1 的提示词，使用原始查询")
            return query
            
        complete_query = prefixPrompt.prompt + "\n\n 用户的问题如下：" + query
        
        logger.info(f"已成功拼接提示词，总 prompt 长度: {len(complete_query)} 字符")
        return complete_query
        
    except Exception as e:
        logger.error(f"准备查询提示词时出错: {e}")
        logger.info("使用原始查询继续执行")
        return query

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
            complete_query = await prepare_query_with_prompt(query)
            
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
    return {
        "status": "healthy",
        "agent_ready": agent is not None,
        "model_id": settings.MODEL_ID,
        "init_error": init_error if init_error else None,
        "data_files_status": get_data_files_status(),
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
        complete_query = await prepare_query_with_prompt(query)
        
        result = await asyncio.to_thread(agent.run, complete_query)
        return {
            "status": "success",
            "query": query,
            "result": result
        }
    except Exception as e:
        logger.error(f"处理查询时出错: {e}")
        return {"error": str(e)}

# ProductPrompt CRUD API 端点
@app.get("/prompts", response_model=List[ProductPromptResponse], tags=["提示词管理"])
async def get_all_prompts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    service: ProductPromptService = Depends(get_product_prompt_service)
):
    """获取所有提示词（分页）"""
    prompts = await service.get_all_prompts(page=page, page_size=page_size)
    return prompts

@app.get("/prompts/{prompt_id}", response_model=ProductPromptResponse, tags=["提示词管理"])
async def get_prompt(
    prompt_id: int,
    service: ProductPromptService = Depends(get_product_prompt_service)
):
    """根据 ID 获取提示词"""
    prompt = await service.get_prompt_by_id(prompt_id)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在")
    return prompt

@app.post("/prompts", response_model=ProductPromptResponse, tags=["提示词管理"])
async def create_prompt(
    prompt_data: ProductPromptCreate,
    service: ProductPromptService = Depends(get_product_prompt_service)
):
    """创建新提示词"""
    prompt = await service.create_prompt(prompt_data)
    if not prompt:
        raise HTTPException(status_code=400, detail="创建提示词失败")
    return prompt

@app.put("/prompts/{prompt_id}", response_model=ProductPromptResponse, tags=["提示词管理"])
async def update_prompt(
    prompt_id: int,
    prompt_data: ProductPromptUpdate,
    service: ProductPromptService = Depends(get_product_prompt_service)
):
    """更新提示词"""
    prompt = await service.update_prompt(prompt_id, prompt_data)
    if not prompt:
        raise HTTPException(status_code=404, detail="提示词不存在或更新失败")
    return prompt

@app.delete("/prompts/{prompt_id}", tags=["提示词管理"])
async def delete_prompt(
    prompt_id: int,
    service: ProductPromptService = Depends(get_product_prompt_service)
):
    """删除提示词"""
    success = await service.delete_prompt(prompt_id)
    if not success:
        raise HTTPException(status_code=404, detail="提示词不存在或删除失败")
    return {"message": "提示词删除成功"}

@app.get("/prompts/search/{search_term}", response_model=List[ProductPromptResponse], tags=["提示词管理"])
async def search_prompts(
    search_term: str,
    search_type: str = Query("prompt", regex="^(prompt|description)$", description="搜索类型"),
    limit: int = Query(50, ge=1, le=100, description="返回数量限制"),
    service: ProductPromptService = Depends(get_product_prompt_service)
):
    """搜索提示词"""
    prompts = await service.search_prompts(search_term, search_type, limit)
    return prompts

@app.get("/prompts/recent", response_model=List[ProductPromptResponse], tags=["提示词管理"])
async def get_recent_prompts(
    limit: int = Query(10, ge=1, le=100, description="返回数量"),
    service: ProductPromptService = Depends(get_product_prompt_service)
):
    """获取最近的提示词"""
    prompts = await service.get_recent_prompts(limit)
    return prompts

# ===== 爬虫相关API接口 =====

@app.post("/api/scraping/process-url")
async def process_amazon_url(request: dict):
    """
    处理Amazon URL，启动爬虫任务
    
    Request body:
        url (str): Amazon URL
        max_products (int): 最大产品数量，默认100
        scrape_reviews (bool): 是否爬取评论，默认true
        review_coverage_months (int): 评论覆盖月数，默认6
    """
    if not SCRAPING_AVAILABLE:
        logger.error("爬虫模块不可用")
        return {"task_id": "error", "status": "failed", "error": "爬虫模块不可用"}
    
    try:
        logger.info(f"收到爬虫请求: {request}")
        
        # 解析请求参数
        url = request.get("url", "").strip()
        max_products = request.get("max_products", 100)
        scrape_reviews = request.get("scrape_reviews", True)
        review_coverage_months = request.get("review_coverage_months", 6)
        
        if not url:
            return {"task_id": "error", "status": "failed", "error": "URL 不能为空"}
        
        logger.info(f"开始处理URL: {url}, max_products: {max_products}")
        
        # 使用新的编排服务
        orchestrator = ScrapingOrchestrator()
        result = await orchestrator.process_url(
            url=url, 
            max_products=max_products,
            scrape_reviews=scrape_reviews,
            review_coverage_months=review_coverage_months
        )
        
        logger.info(f"爬虫任务完成: {result}")
        return result
        
    except ValueError as e:
        logger.error(f"参数错误: {e}")
        return {"task_id": "error", "status": "failed", "error": str(e)}
    except Exception as e:
        logger.error(f"处理爬虫请求时出错: {e}", exc_info=True)
        return {"task_id": "error", "status": "failed", "error": f"处理请求失败: {str(e)}"}

@app.post("/api/scraping/products-only")
async def scrape_products_only(request: dict):
    """
    仅爬取商品数据（不包括评论）
    
    Request body:
        url (str): Amazon URL
        max_products (int): 最大产品数量，默认100
    """
    if not SCRAPING_AVAILABLE:
        return {"error": "爬虫模块不可用"}
    
    try:
        url = request.get("url", "").strip()
        max_products = request.get("max_products", 100)
        
        orchestrator = ScrapingOrchestrator()
        result = await orchestrator.scrape_products_only(url, max_products)
        return result
        
    except Exception as e:
        logger.error(f"处理商品爬取请求时出错: {e}", exc_info=True)
        return {"error": f"处理请求失败: {str(e)}"}

@app.post("/api/scraping/reviews-only")
async def scrape_reviews_only(request: dict):
    """
    仅爬取评论数据（商品数据已存在）
    
    Request body:
        batch_id (int): 批次ID
        review_coverage_months (int): 评论覆盖月数，默认6
    """
    if not SCRAPING_AVAILABLE:
        return {"error": "爬虫模块不可用"}
    
    try:
        batch_id = request.get("batch_id")
        review_coverage_months = request.get("review_coverage_months", 6)
        
        if not batch_id:
            return {"error": "batch_id is required"}
        
        orchestrator = ScrapingOrchestrator()
        result = await orchestrator.scrape_reviews_only(batch_id, review_coverage_months)
        return result
        
    except Exception as e:
        logger.error(f"处理评论爬取请求时出错: {e}", exc_info=True)
        return {"error": f"处理请求失败: {str(e)}"}

@app.get("/api/scraping/status/{batch_id}")
async def get_scraping_status(batch_id: int):
    """
    获取爬取状态
    
    Args:
        batch_id (int): 批次ID
    """
    if not SCRAPING_AVAILABLE:
        return {"error": "爬虫模块不可用"}
    
    try:
        orchestrator = ScrapingOrchestrator()
        status = await orchestrator.get_process_status(batch_id=batch_id)
        return status
        
    except Exception as e:
        logger.error(f"获取爬取状态时出错: {e}", exc_info=True)
        return {"error": f"获取状态失败: {str(e)}"}

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