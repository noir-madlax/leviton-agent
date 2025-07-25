"""Dashboard charts API routes."""

from fastapi import APIRouter, HTTPException
import logging

from .customerSatisfaction.models import CustomerSatisfactionRequest, CustomerSatisfactionResponse
from .customerSatisfaction.services import CustomerSatisfactionService

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/competitive/customer-satisfaction", response_model=CustomerSatisfactionResponse)
async def get_customer_satisfaction(request: CustomerSatisfactionRequest):
    """获取客户满意度分析数据

    分析竞争对手产品的客户满意度，基于评论数据和评分。
    返回6个默认竞争对手产品的满意度数据，按满意度分数排序。

    Args:
        request: 客户满意度分析请求，包含项目ID和筛选条件

    Returns:
        CustomerSatisfactionResponse: 包含产品满意度数据数组的响应

    Raises:
        HTTPException: 当请求处理失败时
    """
    try:
        # 初始化服务
        service = CustomerSatisfactionService(
            project_id=request.project_id,
            filters=request.filters
        )

        # 获取数据
        products_data = service.get_data()

        # 构建响应
        response = CustomerSatisfactionResponse(
            data=products_data
        )

        logger.info(f"Customer satisfaction analysis completed for project {request.project_id}: {len(response.data)} products analyzed")

        return response

    except Exception as e:
        logger.error(f"Error in customer satisfaction analysis: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")