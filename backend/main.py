from fastapi import FastAPI, Response, Query, Depends, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import logging
from typing import Optional, List
from contextlib import asynccontextmanager
from config import settings
from agent.tools import get_data_files_status, test_tools
from product_segment.api import router as segmentation_router

# 导入重构后的 agent 模块
from agent.core.agent_manager import get_agent_manager
from agent.monitor import initialize_phoenix_monitoring
from agent.streaming.stream_handler import stream_agent_response
from agent.services.query_processor import get_query_processor
from agent.services.request_handler import get_request_handler
from agent.services.request_models import AgentStreamRequest

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

@asynccontextmanager
async def lifespan(app: FastAPI):
    """在应用启动时初始化 Agent，在关闭时清理资源。"""
    
    # 初始化Phoenix监控
    initialize_phoenix_monitoring()
    
    # 初始化 Agent
    agent_manager = get_agent_manager()
    await agent_manager.initialize_agent()

    yield

    # 清理资源
    agent_manager.cleanup()


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

# Register all API routers
from projects.api import router as projects_router
from dashboard.api import router as dashboard_router
from data_transformation.api import router as data_transformation_router
from review_analysis.api import router as review_analysis_router
from categories.api import router as categories_router

app.include_router(segmentation_router, prefix="/api/segmentation", tags=["Product Segmentation"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Projects"])
app.include_router(dashboard_router, prefix="/api/v1/dashboard", tags=["Dashboard"])
app.include_router(data_transformation_router, tags=["Data Transformation"])
app.include_router(review_analysis_router, prefix="/api/v1", tags=["Review Analysis"])
app.include_router(categories_router, prefix="/api/v1/categories", tags=["Categories"])

@app.get("/")
async def root():
    """根路径，返回 API 信息"""
    agent_manager = get_agent_manager()
    return {
        "message": "Leviton Agent API",
        "version": "1.0.0",
        "status": "运行中" if agent_manager.is_ready() else "Agent 未初始化",
        "model_id": settings.MODEL_ID,
        "init_error": agent_manager.get_init_error(),
        "available_tools": agent_manager.get_agent().tools if agent_manager.is_ready() else []
    }

@app.get("/health")
async def health_check():
    """健康检查端点"""
    agent_manager = get_agent_manager()
    return {
        "status": "healthy",
        "agent_ready": agent_manager.is_ready(),
        "model_id": settings.MODEL_ID,
        "init_error": agent_manager.get_init_error(),
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
    agent_manager = get_agent_manager()
    return {
        "success": False,
        "message": "Agent 初始化已与应用生命周期绑定，此端点已弃用。",
        "agent_ready": agent_manager.is_ready(),
        "init_error": agent_manager.get_init_error()
    }

@app.get("/test-tools")
async def test_tools_endpoint():
    """测试工具功能"""
    return test_tools()

@app.post("/agent/stream")
async def agent_stream_post(request: AgentStreamRequest):
    """
    POST SSE 端点，接收 JSON 格式的查询并流式返回 smolagents 的输出
    支持复杂的过滤器配置
    """
    # 获取请求处理器
    request_handler = get_request_handler()
    
    # 处理流式请求
    return StreamingResponse(
        request_handler.handle_stream_request(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )

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