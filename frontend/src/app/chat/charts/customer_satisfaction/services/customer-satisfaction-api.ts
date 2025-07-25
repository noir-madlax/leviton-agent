// Customer Satisfaction API Service

import { ChartApiBase } from '../../shared/services/chart-api-base'
import type { 
  CustomerSatisfactionResponse, 
  CustomerSatisfactionFilters, 
  CustomerSatisfactionRequest 
} from '../types/customer-satisfaction.types'

class CustomerSatisfactionApi extends ChartApiBase {
  constructor() {
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    super(baseUrl)
  }

  /**
   * 获取客户满意度数据
   * @param projectId 项目ID
   * @param filters 过滤条件
   * @returns 客户满意度数据
   */
  async getCustomerSatisfactionData(
    projectId: string,
    filters?: CustomerSatisfactionFilters
  ): Promise<CustomerSatisfactionResponse> {
    const requestBody: CustomerSatisfactionRequest = {
      project_id: projectId,
      filters: filters || {}
    }

    return this.post<CustomerSatisfactionResponse>('/api/v1/dashboard/charts/competitive/customer-satisfaction', requestBody)
  }
}

export const customerSatisfactionApi = new CustomerSatisfactionApi()
