"""销售趋势API路由 - Sales Trend Analysis API"""

from fastapi import APIRouter, HTTPException
import logging

from .models import SalesTrendRequest, SalesTrendResponse
from .services import SalesTrendService
from backend.dashboard.decorators import log_request_response

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/sales-trend", response_model=SalesTrendResponse)
@log_request_response
async def get_sales_trend(request: SalesTrendRequest):
    """获取销售价格和趋势数据
    
    POST请求，使用JSON格式传递过滤条件：
    {
        "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
        "filters": {
            "categories": ["Light Switches"],
            "brands": ["Leviton"],
            "segments": ["Premium"],
            "extend_fields": {"is_bestseller": true}
        },
        "date_range": {
            "start_date": "2024-07-01",
            "end_date": "2025-07-01"
        },
        "asin": "B08SJ3Z8XD",
        "metric_type": "sales",
        "aggregation": "daily"
    }
    
    返回销售趋势数据，包括：
    - 时间序列销量和价格数据
    - 汇总统计信息（总销量、平均价格、增长率等）
    - 元数据信息
    """
    try:
        # 创建服务实例
        service = SalesTrendService(request.project_id)
        
        # 应用标准过滤器（categories, brands, segments, extend_fields）
        if request.filters:
            from backend.core.models.filters import ProjectFilters
            filters = ProjectFilters.from_dict(request.filters)
            if not filters.is_empty():
                service.set_project_filters(filters)
        
        # 应用业务特定参数
        if request.asin:
            service.set_target_asin(request.asin)
        
        if request.date_range:
            date_range = request.get_date_range_filter()
            service.set_date_range(date_range["start_date"], date_range["end_date"])
        
        if request.metric_type:
            service.set_metric_type(request.metric_type)
            
        if request.aggregation:
            service.set_aggregation(request.aggregation)
        
        # 获取数据
        raw_data = service.get_data()
        
        # 构建响应
        response = SalesTrendResponse(
            trend_data=raw_data['trend_data'],
            summary_stats=raw_data['summary_stats'],
            project_id=request.project_id,
            asin=request.asin,
            date_range=raw_data['date_range'],
            metric_type=request.metric_type or "sales",
            aggregation=request.aggregation or "daily",
            total_data_points=raw_data['total_data_points'],
            applied_filters=raw_data['applied_filters']
        )
        
        logger.info(f"Sales trend API returned {response.total_data_points} data points for project {request.project_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in sales trend API: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in sales trend API: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) 