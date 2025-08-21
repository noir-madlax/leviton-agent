"""ASIN过滤服务 - 提供公共的数据过滤方法"""

import logging
from typing import List

from .chain_filter import build_filtered_sql
from ..base_models import BaseRequestModel

logger = logging.getLogger(__name__)


class FilteredDataService:
    """过滤数据服务 - 提供公共的数据过滤方法
    
    这个服务类提供统一的ASIN过滤功能，所有图表服务都应该使用这个类
    来获取过滤后的ASIN列表，确保过滤逻辑的一致性。
    """
    
    def __init__(self, supabase_client):
        """初始化服务
        
        Args:
            supabase_client: Supabase客户端实例
        """
        self.supabase = supabase_client
    
    def get_filtered_asins(self, request: BaseRequestModel) -> List[str]:
        """获取过滤后的ASIN列表

        这是一个公共方法，所有图表服务都可以使用它来获取过滤后的ASIN列表。

        Args:
            request: 基础请求模型，包含project_id和filters

        Returns:
            List[str]: 过滤后的ASIN列表

        Raises:
            ValueError: 当project_id为空时
            Exception: 当SQL执行失败时

        Example:
            ```python
            from dashboard.charts.filters.asin_filter_service import FilteredDataService
            from dashboard.charts.base_models import BaseRequestModel
            from core.database.connection import get_supabase_client

            supabase_client = get_supabase_client()
            filter_service = FilteredDataService(supabase_client)

            request = BaseRequestModel(
                project_id="d2c02b80-4c82-44cc-8093-56708a7883f7",
                filters={"categories": ["Dimmer Switches"], "brands": ["Leviton"]}
            )
            filtered_asins = filter_service.get_filtered_asins(request)
            ```
        """
        try:
            # 验证project_id
            if not request.project_id:
                raise ValueError("project_id is required")

            # 构建SQL查询
            sql = build_filtered_sql(request.project_id, request.filters)

            logger.info(f"Executing filtered query for project {request.project_id}")
            logger.debug(f"SQL: {sql}")

            # 执行查询
            result = self.supabase.rpc('execute_safe_query', {
                'query_text': sql
            }).execute()

            if result.data is None:
                logger.warning("Query returned None data")
                return []

            # 调试：打印返回的数据结构
            if result.data:
                logger.info(f"Query returned {len(result.data)} rows")
                logger.info(f"First row keys: {list(result.data[0].keys()) if result.data else 'No data'}")
                logger.info(f"First row sample: {result.data[0] if result.data else 'No data'}")
            else:
                logger.info("Query returned empty result")
                return []

            # 提取ASIN列表 - 处理Supabase RPC返回的数据结构
            asins = []
            for row in result.data:
                # Supabase execute_safe_query 返回的数据结构是 {"result": {...}}
                if 'result' in row and isinstance(row['result'], dict):
                    result_data = row['result']
                    if 'platform_id' in result_data:
                        asins.append(result_data['platform_id'])
                    else:
                        logger.error(f"platform_id field not found in result data. Available fields: {list(result_data.keys())}")
                        raise KeyError(f"platform_id field not found in result data. Available fields: {list(result_data.keys())}")
                else:
                    # 如果不是预期的结构，打印调试信息
                    logger.error(f"Unexpected row structure. Row: {row}")
                    raise KeyError(f"Unexpected row structure. Expected 'result' field but got: {list(row.keys())}")

            logger.info(f"Query executed successfully, returned {len(asins)} ASINs")
            return asins

        except Exception as e:
            logger.error(f"Error executing filtered query: {e}")
            raise Exception(f"Failed to execute filtered query: {str(e)}")


def get_filtered_asins(supabase_client, request: BaseRequestModel) -> List[str]:
    """便捷函数：获取过滤后的ASIN列表

    这是一个全局便捷函数，可以直接调用而无需实例化FilteredDataService。

    Args:
        supabase_client: Supabase客户端实例
        request: 基础请求模型，包含project_id和filters

    Returns:
        List[str]: 过滤后的ASIN列表

    Example:
        ```python
        from dashboard.charts.filters.asin_filter_service import get_filtered_asins
        from dashboard.charts.base_models import BaseRequestModel
        from core.database.connection import get_supabase_client

        supabase_client = get_supabase_client()
        request = BaseRequestModel(
            project_id="d2c02b80-4c82-44cc-8093-56708a7883f7",
            filters={"categories": ["Dimmer Switches"], "brands": ["Leviton"]}
        )
        filtered_asins = get_filtered_asins(supabase_client, request)
        ```
    """
    service = FilteredDataService(supabase_client)
    return service.get_filtered_asins(request)
