"""Common base service for chart modules.

Provides shared querying utilities for chart services that operate with a
provided Supabase client instead of project-scoped base services.
"""

import logging
from typing import List
from datetime import datetime

from dashboard.models import MonthlySalesRecord, MonthlySalesAggregate
from dashboard.utils.timeframe_mapper import TimeframeFieldMapper

logger = logging.getLogger(__name__)


class ChartsBaseService:
    """Base class for chart services using a provided Supabase client.

    This avoids coupling to project-scoped services and offers shared
    utilities like timeframe-based monthly sales querying.
    """

    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def query_monthly_sales_with_timeframe(self, asins: List[str], timeframe) -> List[MonthlySalesRecord]:
        """Query monthly sales records by timeframe for given ASINs.

        Args:
            asins: List of ASINs to query
            timeframe: Timeframe model used to compute start/end dates

        Returns:
            List of MonthlySalesRecord
        """
        try:
            start_date, end_date = TimeframeFieldMapper.get_date_range(timeframe)

            all_sales_data: List[MonthlySalesRecord] = []
            page = 0
            page_size = 1000

            while True:
                range_from = page * page_size
                range_to = range_from + page_size - 1

                query = (
                    self.supabase
                    .table('product_sales_history_monthly')
                    .select('platform_id, year_month, total_units_sold, average_price, total_revenue')
                    .in_('platform_id', asins)
                    .eq('platform_source', 'amazon')
                )

                if start_date:
                    start_month = datetime.strptime(start_date, '%Y-%m-%d').replace(day=1).date()
                    query = query.gte('year_month', start_month.isoformat())

                if end_date:
                    end_month = datetime.strptime(end_date, '%Y-%m-%d').replace(day=1).date()
                    query = query.lte('year_month', end_month.isoformat())

                query = query.order('year_month', desc=False).range(range_from, range_to)
                result = query.execute()

                if not result.data:
                    break

                for row in (result.data or []):
                    all_sales_data.append(MonthlySalesRecord(**row))

                if len(result.data) < page_size:
                    break

                page += 1

            logger.info(f"Monthly sales data: {len(all_sales_data)} records found")
            return all_sales_data

        except Exception as e:
            logger.error(f"Error querying monthly sales with timeframe: {e}")
            return []

    def query_monthly_sales_aggregate_with_timeframe(self, asins: List[str], timeframe) -> List[MonthlySalesAggregate]:
        """按 ASIN 聚合的 timeframe 月度销售汇总。

        直接在数据库侧聚合 sum(total_units_sold), sum(total_revenue)，减少传输与内存聚合开销。

        Returns: List[MonthlySalesAggregate]
        """
        try:
            if not asins:
                return []

            start_date, end_date = TimeframeFieldMapper.get_date_range(timeframe)

            # 规范化月份边界
            start_month = datetime.strptime(start_date, '%Y-%m-%d').replace(day=1).date().isoformat() if start_date else None
            end_month = datetime.strptime(end_date, '%Y-%m-%d').replace(day=1).date().isoformat() if end_date else None

            # 安全拼接 IN 列表（转义单引号）
            def esc(val: str) -> str:
                return val.replace("'", "''")
            asin_list_sql = ",".join([f"'{esc(a)}'" for a in asins])

            where_clauses = ["platform_source = 'amazon'", f"platform_id IN ({asin_list_sql})"]
            if start_month:
                where_clauses.append(f"year_month >= '{start_month}'")
            if end_month:
                where_clauses.append(f"year_month <= '{end_month}'")
            where_sql = " AND ".join(where_clauses)

            sql = f"""
                SELECT
                  platform_id,
                  COALESCE(SUM(total_units_sold), 0) AS total_units_sold,
                  COALESCE(SUM(total_revenue), 0) AS total_revenue
                FROM product_sales_history_monthly
                WHERE {where_sql}
                GROUP BY platform_id
            """.strip()

            # 通过通用 RPC 执行 SQL
            response = self.supabase.rpc('execute_safe_query', {'query_text': sql}).execute()

            rows = getattr(response, 'data', None) or []
            payloads = []
            for row in rows:
                payload = row.get('result') if isinstance(row, dict) and 'result' in row else row
                if payload and payload.get('platform_id'):
                    payloads.append(payload)

            aggregates: List[MonthlySalesAggregate] = [
                MonthlySalesAggregate(**payload) for payload in payloads
            ]

            logger.info(f"Monthly aggregate data via SQL: {len(aggregates)} ASINs aggregated")
            return aggregates
        except Exception as e:
            logger.error(f"Error aggregating monthly sales with timeframe (SQL): {e}")
            return []


