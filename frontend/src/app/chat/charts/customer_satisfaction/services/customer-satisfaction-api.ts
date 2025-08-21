// Customer Satisfaction API Service

import { ChartApiBase } from '../../shared/services/chart-api-base'
import type {
  CustomerSatisfactionResponse,
  CustomerSatisfactionFilters,
  CustomerSatisfactionRequest,
  ProductSatisfactionData
} from '../types/customer-satisfaction.types'

// 默认竞争对手 ASINs 常量
const DEFAULT_COMPETITOR_ASINS = [
  'B00NG0ELL0',  // Leviton DSL06 - Mid-tier brand representative
  'B0BVKZLT3B',  // Leviton D215S - Mid-tier brand representative
  'B0BVKYKKRK',  // Leviton D26HD - Mid-tier brand representative
  'B0BSHKS26L',  // Lutron Caseta Diva - Mid-tier brand representative
  'B085D8M2MR',  // Lutron Diva - Mid-tier brand representative
  'B01EZV35QU',  // TP Link Switch
]

// 新接口的请求类型
interface CompetitorSummaryRequest {
  project_id: string
  selected_asins: string[]
}

// 新接口的响应类型
interface CompetitorSummaryProduct {
  asin: string
  product_title: string
  rating?: number
  brand?: string
  product_url?: string
  list_price?: number
  unique_reviews_count: number
  additional_metrics?: {
    sentiment_distribution?: {
      positive: number
      negative: number
      neutral: number
    }
    category_counts?: Record<string, number>
    // 保持向后兼容的旧字段
    positive_aspects?: number
    negative_aspects?: number
    neutral_aspects?: number
    unique_categories?: number
    total_aspects?: number
  }
}

interface CompetitorSummaryData {
  products: CompetitorSummaryProduct[]
  total_products: number
  selected_asins: string[]
}

interface CompetitorSummaryResponse {
  status: string
  message?: string
  timestamp: string
  data: CompetitorSummaryData
  // 兼容直接返回 products 的格式
  products?: CompetitorSummaryProduct[]
  total_products?: number
  selected_asins?: string[]
}

class CustomerSatisfactionApi extends ChartApiBase {
  constructor() {
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    super(baseUrl)
  }

  /**
   * 获取客户满意度数据
   * @param projectId 项目ID
   * @param filters 过滤条件（暂时不使用，保持接口兼容性）
   * @returns 客户满意度数据
   */
  async getCustomerSatisfactionData(
    projectId: string,
    filters?: CustomerSatisfactionFilters
  ): Promise<CustomerSatisfactionResponse> {
    const requestBody: CompetitorSummaryRequest = {
      project_id: projectId,
      selected_asins: DEFAULT_COMPETITOR_ASINS
    }

    // 调用新的竞争对手分析接口
    const response = await this.post<CompetitorSummaryResponse>('/api/v1/dashboard/charts/competitor-analysis/summary', requestBody)

    // 将新接口的数据转换为原有格式
    return this.transformToCustomerSatisfactionResponse(response)
  }

  /**
   * 将竞争对手分析响应转换为客户满意度响应格式
   */
  private transformToCustomerSatisfactionResponse(
    competitorResponse: CompetitorSummaryResponse
  ): CustomerSatisfactionResponse {
    // 检查响应数据结构
    const products = competitorResponse.data?.products || competitorResponse.products || []

    const transformedProducts: ProductSatisfactionData[] = products.map(product => ({
      asin: product.asin,
      name: this.truncateProductTitle(product.product_title),
      full_title: product.product_title,
      brand: product.brand || 'Unknown',
      total_reviews: product.unique_reviews_count || 0,
      average_rating: product.rating,
      satisfaction_score: this.calculateSatisfactionScore(product.additional_metrics),
      price_usd: product.list_price,
      product_url: product.product_url,
      thumbnail_url: undefined // 新接口暂时没有缩略图
    }))

    return {
      status: 'success',
      message: 'Customer satisfaction data retrieved successfully',
      timestamp: new Date().toISOString(),
      data: transformedProducts
    }
  }

  /**
   * 计算满意度分数
   * 基于 sentiment_distribution 中的正面和负面情感比例
   */
  private calculateSatisfactionScore(additionalMetrics?: CompetitorSummaryProduct['additional_metrics']): number {
    if (!additionalMetrics?.sentiment_distribution) {
      // 如果没有情感分布数据，返回默认值 90%
      return 90
    }

    const { positive, negative, neutral } = additionalMetrics.sentiment_distribution
    const total = positive + negative + neutral

    if (total === 0) {
      // 如果没有数据，返回默认值 90%
      return 90
    }

    // 计算满意度分数：正面情感占比 * 100
    // 可以考虑不同的计算方式，比如：
    // 1. 纯正面占比：positive / total * 100
    // 2. 正面减负面占比：(positive - negative) / total * 100 + 50
    // 3. 正面占有效情感比例：positive / (positive + negative) * 100

    // 这里使用方式1：纯正面占比
    const satisfactionScore = (positive / total) * 100

    // 确保分数在 0-100 范围内
    return Math.max(0, Math.min(100, Math.round(satisfactionScore * 10) / 10))
  }

  /**
   * 截断产品标题以适应显示
   */
  private truncateProductTitle(title: string, maxLength: number = 50): string {
    if (title.length <= maxLength) return title
    return title.substring(0, maxLength) + '...'
  }
}

export const customerSatisfactionApi = new CustomerSatisfactionApi()
