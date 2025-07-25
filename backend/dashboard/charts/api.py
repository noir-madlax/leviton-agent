"""Dashboard charts API routes."""

from fastapi import APIRouter, HTTPException
import logging

from .customerSatisfaction.models import CustomerSatisfactionRequest, CustomerSatisfactionResponse
from .customerSatisfaction.services import CustomerSatisfactionService
from .competitorAnalysis.models import (
    CompetitorSummaryRequest, CompetitorSummaryResponse,
    CompetitorMatrixViewRequest, CompetitorMatrixViewResponse
)
from .competitorAnalysis.service import CompetitorAnalysisChartService

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


@router.post("/competitor-analysis/summary", response_model=CompetitorSummaryResponse)
async def get_competitor_summary(request: CompetitorSummaryRequest):
    """Get competitor analysis summary data.
    
    Args:
        request: Competitor summary request with project_id and selected_asins
        
    Returns:
        CompetitorSummaryResponse: Competitor summary data
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        service = CompetitorAnalysisChartService(
            project_id=request.project_id,
            filters=request.filters,
            date_range=request.date_range
        )
        data = await service.get_competitor_summary(request.selected_asins)
        response = CompetitorSummaryResponse(data=data)
        
        logger.info(f"Competitor summary analysis completed for project {request.project_id}: {len(response.data.products)} products")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in competitor summary: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in competitor summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/competitor-analysis/matrix-view", response_model=CompetitorMatrixViewResponse)
async def get_competitor_matrix_view(request: CompetitorMatrixViewRequest):
    """Get competitor analysis matrix view data.
    
    Args:
        request: Competitor matrix view request with project_id, selected_asins, aspect_type, and options
        
    Returns:
        CompetitorMatrixViewResponse: Competitor matrix view data
        
    Raises:
        HTTPException: Error response for validation or system errors
    """
    try:
        service = CompetitorAnalysisChartService(
            project_id=request.project_id,
            filters=request.filters,
            date_range=request.date_range
        )
        
        # Convert options to dict for service
        options_dict = request.options.model_dump()
        data = await service.get_matrix_view_data(
            request.selected_asins, 
            request.aspect_type, 
            options_dict
        )
        response = CompetitorMatrixViewResponse(data=data)
        
        logger.info(f"Competitor matrix view analysis completed for project {request.project_id}: {len(response.data.aspect_categories)} categories")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in competitor matrix view: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in competitor matrix view: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")