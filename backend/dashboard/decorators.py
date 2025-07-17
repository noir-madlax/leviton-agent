"""Dashboard API 装饰器模块"""

from functools import wraps
from typing import Callable, Type, Any
from fastapi import HTTPException
import logging

from .models import DashboardRequest
from .services.base_service import BaseDashboardService

logger = logging.getLogger(__name__)


def with_dashboard_service(service_class: Type[BaseDashboardService]):
    """
    装饰器：自动处理 Dashboard 过滤器和服务创建

    使用方式：
    @with_dashboard_service(BrandAnalysisService)
    async def get_brand_analysis(service: BrandAnalysisService, request: DashboardRequest):
        # 业务逻辑
        return service.get_data()
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: DashboardRequest, **kwargs) -> Any:
            try:
                # 特殊处理 CompetitorAnalysisService，它需要额外的参数
                from .models import CompetitorAnalysisRequest
                if hasattr(request, 'selected_asins') and isinstance(request, CompetitorAnalysisRequest):
                    # CompetitorAnalysisService 需要在初始化时传入 selected_asins
                    service = service_class(request.project_id, selected_asins=request.selected_asins)
                else:
                    # 普通服务只需要 project_id
                    service = service_class(request.project_id)

                # 应用过滤器
                filters = request.get_project_filters()
                if not filters.is_empty():
                    service.set_project_filters(filters)

                # 调用原始函数，传入service和request
                return await func(service=service, request=request, **kwargs)

            except ValueError as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))

        return wrapper
    return decorator


def with_service_and_options(service_class: Type[BaseDashboardService]):
    """
    装饰器：处理服务创建和查询选项
    
    适用于需要处理查询选项（如分页、排序）的接口
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(request: DashboardRequest, **kwargs) -> Any:
            try:
                # 创建服务实例
                service = service_class(request.project_id)
                
                # 应用过滤器
                filters = request.get_project_filters()
                if not filters.is_empty():
                    service.set_project_filters(filters)
                
                # 获取查询选项
                options = request.get_query_options()
                
                # 调用原始函数
                return await func(service=service, request=request, options=options, **kwargs)
                
            except ValueError as e:
                logger.error(f"Validation error in {func.__name__}: {e}")
                raise HTTPException(status_code=400, detail=str(e))
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail=str(e))
        
        return wrapper
    return decorator


def log_request_response(func: Callable):
    """
    装饰器：记录请求和响应日志
    """
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Any:
        # 查找request参数
        request = None
        for arg in args:
            if isinstance(arg, DashboardRequest):
                request = arg
                break
        
        if not request:
            request = kwargs.get('request')
        
        if request:
            logger.info(f"API {func.__name__} called for project {request.project_id}")
            if request.filters:
                logger.debug(f"Filters applied: {request.filters}")
        
        try:
            result = await func(*args, **kwargs)
            logger.info(f"API {func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"API {func.__name__} failed: {e}")
            raise
    
    return wrapper
