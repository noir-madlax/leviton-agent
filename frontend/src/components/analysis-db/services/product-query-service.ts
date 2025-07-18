/**
 * 产品查询服务 - 用于图表点击时获取精确匹配的产品数据
 */

export interface ProductFilterCriteria {
  // 标准筛选条件
  categories?: string[]
  brands?: string[]
  segments?: string[]
  extend_fields?: Record<string, any>
  exclude_asins?: string[]
}

export interface ProductQueryOptions {
  limit?: number
  offset?: number
  sort_by?: 'price' | 'revenue' | 'volume' | 'rating' | 'reviews_count'
  sort_order?: 'asc' | 'desc'
}

export interface ProductItem {
  id: string
  name: string
  brand: string
  category?: string
  segment?: string
  price: number
  unitPrice: number
  revenue: number
  volume: number
  rating?: number
  reviews_count?: number
  url?: string
  packCount?: number
}

export interface ProductQueryResponse {
  products: ProductItem[]
  total_count: number
  filtered_count: number
  project_id: string
  applied_filters: ProductFilterCriteria
  stats?: {
    total_products: number
    price_range?: {
      min: number
      max: number
      avg: number
    }
    revenue_range?: {
      min: number
      max: number
      total: number
    }
    volume_range?: {
      min: number
      max: number
      total: number
    }
  }
}

export class ProductQueryService {
  private baseUrl: string

  constructor() {
    this.baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  }

  /**
   * 查询产品列表
   */
  async queryProducts(
    projectId: string,
    filters: ProductFilterCriteria,
    options?: ProductQueryOptions
  ): Promise<ProductQueryResponse> {
    const response = await fetch(`${this.baseUrl}/api/v1/dashboard/products/query`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        project_id: projectId,
        filters: filters,
        options: options || {
          limit: 100,
          sort_by: 'revenue',
          sort_order: 'desc'
        }
      })
    })

    if (!response.ok) {
      throw new Error(`Product query failed: ${response.status}`)
    }

    return response.json()
  }

  /**
   * 获取产品快速统计信息
   */
  async getQuickStats(projectId: string): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/v1/dashboard/products/${projectId}/quick-stats`)

    if (!response.ok) {
      throw new Error(`Quick stats failed: ${response.status}`)
    }

    return response.json()
  }

  /**
   * 根据图表点击条件查询产品 - 小提琴图点击
   */
  async queryByViolinClick(
    projectId: string,
    category: string
  ): Promise<ProductItem[]> {
    const result = await this.queryProducts(projectId, {
      categories: [category]
    })

    return result.products
  }

  /**
   * 根据图表点击条件查询产品 - 品牌小提琴图点击
   */
  async queryByBrandViolinClick(
    projectId: string,
    brand: string,
    category?: string
  ): Promise<ProductItem[]> {
    const filters: ProductFilterCriteria = {
      brands: [brand]
    }

    if (category) {
      filters.categories = [category]
    }

    const result = await this.queryProducts(projectId, filters)
    return result.products
  }

  /**
   * 根据图表点击条件查询产品 - 多段小提琴图点击
   */
  async queryByMultiSegmentViolinClick(
    projectId: string,
    segment: string
  ): Promise<ProductItem[]> {
    const result = await this.queryProducts(projectId, {
      segments: [segment]
    })

    return result.products
  }

  /**
   * 根据图表点击条件查询产品 - 柱状图点击
   */
  async queryByBarClick(
    projectId: string,
    segment: string
  ): Promise<ProductItem[]> {
    const result = await this.queryProducts(projectId, {
      segments: [segment]
    })

    return result.products
  }

  /**
   * 根据图表点击条件查询产品 - 散点图点击（单个产品）
   */
  async queryByScatterClick(
    projectId: string,
    productId: string
  ): Promise<ProductItem[]> {
    const result = await this.queryProducts(projectId, {
      // 通过extend_fields或其他方式查找特定产品
      // 这里可能需要根据实际数据结构调整
    }, {
      limit: 1
    })
    
    // 如果需要精确匹配特定产品，可能需要在结果中进一步筛选
    return result.products.filter(p => p.id === productId)
  }



  /**
   * 组合多个筛选条件查询产品
   */
  async queryByMultipleFilters(
    projectId: string,
    filters: ProductFilterCriteria,
    options?: ProductQueryOptions
  ): Promise<ProductItem[]> {
    const result = await this.queryProducts(projectId, filters, options)
    return result.products
  }
}

// 创建单例实例
export const productQueryService = new ProductQueryService()

// 便捷的导出函数
export const queryProductsByViolinClick = productQueryService.queryByViolinClick.bind(productQueryService)
export const queryProductsByBrandViolinClick = productQueryService.queryByBrandViolinClick.bind(productQueryService)
export const queryProductsByMultiSegmentViolinClick = productQueryService.queryByMultiSegmentViolinClick.bind(productQueryService)
export const queryProductsByBarClick = productQueryService.queryByBarClick.bind(productQueryService)
export const queryProductsByScatterClick = productQueryService.queryByScatterClick.bind(productQueryService)
export const queryProductsByMultipleFilters = productQueryService.queryByMultipleFilters.bind(productQueryService)
