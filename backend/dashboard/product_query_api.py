"""专门用于图表点击产品查询的FastAPI路由"""

from typing import List, Optional, Dict, Any, Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from .decorators import with_dashboard_service, log_request_response
from .models import DashboardRequest, DashboardQueryOptions
from .services.product_query_service import ProductQueryService

logger = logging.getLogger(__name__)

router = APIRouter()

# ==================== 请求模型 ====================

class ProductQueryRequest(DashboardRequest):
    """
    产品查询请求模型

    继承标准的DashboardRequest，保持与现有API的一致性
    filters字段支持标准的ProjectFilters格式，同时扩展支持：
    - exclude_asins: 要排除的ASIN列表
    """

    def get_project_filters(self):
        """重写父类方法，返回增强筛选器"""
        from core.models.filters import EnhancedProjectFilters
        if not self.filters:
            return EnhancedProjectFilters.empty()
        return EnhancedProjectFilters.from_dict(self.filters)

# ==================== 响应模型 ====================

class ProductItem(BaseModel):
    """产品项模型"""
    id: str = Field(description="产品ID (ASIN)")
    name: str = Field(description="产品名称")
    brand: str = Field(description="品牌")
    category: Optional[str] = Field(description="类别")
    segment: Optional[str] = Field(description="产品段")
    
    # 价格信息
    price: float = Field(description="SKU价格")
    unitPrice: float = Field(description="单位价格")  # 保持与前端一致的命名
    
    # 销售数据
    revenue: float = Field(description="估算收入")
    volume: int = Field(description="月销量")
    
    # 评价信息
    rating: Optional[float] = Field(description="评分")
    reviews_count: Optional[int] = Field(description="评价数量")
    
    # 其他信息
    url: Optional[str] = Field(description="产品链接")
    packCount: Optional[int] = Field(description="包装数量")  # 保持与前端一致的命名

class ProductQueryResponse(BaseModel):
    """产品查询响应模型"""
    products: List[ProductItem] = Field(description="产品列表")
    total_count: int = Field(description="符合条件的总产品数")
    filtered_count: int = Field(description="当前返回的产品数")
    
    # 查询信息
    project_id: str = Field(description="项目ID")
    applied_filters: Dict[str, Any] = Field(description="实际应用的筛选条件")
    
    # 统计信息
    stats: Optional[Dict[str, Any]] = Field(description="数据统计信息")

# ==================== API端点 ====================

@router.post("/products/query", response_model=ProductQueryResponse)
@with_dashboard_service(ProductQueryService)
@log_request_response
async def query_products(
    service: ProductQueryService,
    request: ProductQueryRequest
):
    """
    根据筛选条件查询产品列表
    
    请求格式与其他Dashboard API保持一致：
    {
        "project_id": "string",
        "filters": {
            "categories": ["category1"],      // 标准筛选
            "brands": ["brand1"],             // 标准筛选
            "segments": ["segment1"],         // 标准筛选
            "extend_fields": {"field": "value"}, // 标准筛选
            "exclude_asins": ["ASIN1"]       // 扩展筛选：排除的ASIN
        },
        "options": {
            "limit": 50,                     // 查询选项：返回数量
            "offset": 0,                     // 查询选项：分页偏移
            "sort_by": "revenue",            // 查询选项：排序字段
            "sort_order": "desc"             // 查询选项：排序方向
        }
    }
    """
    try:
        # 执行查询
        result = service.query_products_enhanced(request.get_query_options())
        
        # 构建响应
        response = ProductQueryResponse(
            products=result['products'],
            total_count=result['total_count'],
            filtered_count=len(result['products']),
            project_id=request.project_id,
            applied_filters=result['applied_filters'],
            stats=result.get('stats')
        )
        
        logger.info(f"Product query returned {len(result['products'])} products for project {request.project_id}")
        return response
        
    except Exception as e:
        logger.error(f"Error in product query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{project_id}/quick-stats")
async def get_quick_product_stats(project_id: str):
    """
    获取产品快速统计信息
    
    用于前端了解数据分布，辅助筛选条件设置
    """
    try:
        service = ProductQueryService(project_id)
        stats = service.get_quick_statistics()
        
        return {
            "project_id": project_id,
            "stats": stats
        }
        
    except Exception as e:
        logger.error(f"Error getting quick product stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
