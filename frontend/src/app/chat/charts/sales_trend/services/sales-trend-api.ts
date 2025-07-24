// Sales Trend API Service

import { ChartApiBase } from '../../shared/services/chart-api-base'
import type { 
  SalesTrendData, 
  SalesTrendFilters, 
  SalesTrendRequest 
} from '../types/sales-trend.types'

class SalesTrendApi extends ChartApiBase {
  constructor() {
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    super(baseUrl)
  }

  /**
   * 获取销售趋势数据
   * @param projectId 项目ID
   * @param filters 过滤条件
   * @param dateRange 日期范围
   * @returns 销售趋势数据
   */
  async getSalesTrendData(
    projectId: string,
    filters?: SalesTrendFilters,
    dateRange?: { start_date: string; end_date: string }
  ): Promise<SalesTrendData> {
    const requestBody: SalesTrendRequest = {
      project_id: projectId,
      filters: filters || {},
      // 默认时间范围为2024-07-01到2025-06-30,目前写死销售趋势数据的12个月的范围
      date_range: dateRange || {
        start_date: "2024-07-01",
        end_date: "2025-06-30"
      },
      aggregation: "monthly"
    }

    return this.post<SalesTrendData>('/api/v1/dashboard/sales-trend', requestBody)
  }
}

export const salesTrendApi = new SalesTrendApi() 