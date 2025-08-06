import { supabase } from '@/lib/supabase'
import { ExtendFieldDefinition, ProjectFilters, DEFAULT_FILTERS, FilterDefaultsResponse } from '../types/filters'
import { filterStateManager } from '../stores'
import type { ChartFilterState } from '../stores'
import { CHART_NAMES } from '../constants'

// TAM Market Share API 相关接口
export interface TAMData {
  total_market_revenue: number
  total_market_volume: number
  total_products: number
  currency: string
}

export interface BrandShareData {
  brand: string
  revenue: number
  volume: number
  product_count: number
  market_share_percentage: number
  rank: number
}

export interface CategoryMarketShare {
  category: string
  total_revenue: number
  total_volume: number
  total_products: number
  brand_shares: BrandShareData[]
}

export interface TAMMarketShareMetadata {
  filtered_asins_count: number
  total_categories: number
  total_brands: number
  calculation_timestamp: string
}

export interface TAMMarketShareResponse {
  tam_data: TAMData
  market_share_by_category: CategoryMarketShare[]
  metadata: TAMMarketShareMetadata
}

export interface ProductData {
  platform_id: string
  title: string
  brand: string
  price_usd: number
  past_year_volume: number | null
  past_year_revenue: number | null
  category: string
  product_segment: string
  pack_count: number
  unit_price_calculated: number
  reviews_count: number
  rating: number | null
  product_url: string | null
}

// Project相关接口
export interface Project {
  id: string
  project_name: string
  company_name?: string
  user_name?: string
  description?: string
  selected_categories: string[]
  selected_sources: string[]
  selected_brands: string[]
  selected_product_asins: string[]  // 新增：ASIN列表
  top_sales_count?: number
  total_products: number
  total_brands: number
  total_reviews: number
  avg_monthly_sales: number
  created_at: string
  updated_at: string
  status: string
  overall_status?: string  // New simplified status field for frontend display
}

// 新增数据确认页面相关接口
export interface DataConfirmationFilters {
  categories: string[]
  sources: string[]
  brands: string[]
  topSalesCount?: number
}

export interface DataConfirmationStats {
  totalProducts: number
  totalBrands: number
  totalReviews: number
  avgMonthlySales: number
  sources: Array<{
    name: string
    count: number
    percentage: number
  }>
  categories: Array<{
    name: string
    count: number
    percentage: number
  }>
  brands: Array<{
    name: string
    count: number
    percentage: number
  }>
}

// 数据确认功能的产品数据类型
export interface DataConfirmationProduct {
  platform_id: string
  title: string
  brand: string
  price_usd: number
  past_year_volume: number | null
  past_year_revenue: number | null
  category: string
  product_segment: string
  pack_count: number
  unit_price_calculated: number
  reviews_count: number
  rating: number | null
  product_url: string | null
  source: string
}

export interface DataConfirmationData {
  availableCategories: string[]
  availableSources: string[]
  availableBrands: string[]
  stats: DataConfirmationStats
  topProducts: DataConfirmationProduct[]
}

export interface BrandCategoryData {
  brand: string
  categories: Record<string, { revenue: number; volume: number; product_count: number }>
  dimmerRevenue: number
  switchRevenue: number
  dimmerVolume: number
  switchVolume: number
}

export interface ProductAnalysisData {
  priceVsRevenue: Array<{
    category: string
    products: Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>
  }>
  topProducts: Array<{
    category: string
    products: Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>
  }>
}

// 通用的 Dashboard API 调用函数
async function callDashboardAPI(endpoint: string, projectId: string, options: {
  categoryFilters?: string[]
  packagingTypeFilters?: string[]
  segmentFilters?: string[]
  extendFields?: Record<string, any>
  selectedAsins?: string[]
  metricType?: string
} = {}) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

  const requestBody: any = {
    project_id: projectId,
    filters: {
      ...(options.categoryFilters && options.categoryFilters.length > 0 && { categories: options.categoryFilters }),
      ...(options.packagingTypeFilters && options.packagingTypeFilters.length > 0 && { brands: options.packagingTypeFilters }),
      ...(options.segmentFilters && options.segmentFilters.length > 0 && { segments: options.segmentFilters }),
      ...(options.extendFields && Object.keys(options.extendFields).length > 0 && { extend_fields: options.extendFields })
    }
  }

  // 添加特殊参数
  if (options.selectedAsins) {
    requestBody.selected_asins = options.selectedAsins
  }
  if (options.metricType) {
    requestBody.metric_type = options.metricType
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  })

  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`)
  }

  const jsonResult = await response.json()
  return jsonResult
}

export class DatabaseService {

  // 🆕 从过滤器状态管理器获取过滤器参数 - 直接返回 API 需要的结构
  private getFiltersFromState(chartName: string): {
    filters: {
      categories: string[]
      brands: string[]
      segments: string[]
      extend_fields: Record<string, any>
    }
    timeframe: { period: string }
  } {
    const chartState = filterStateManager.getChartFilters(chartName)

    if (!chartState) {
      console.log(`🔍 [DATABASE-SERVICE] No filter state found for ${chartName}, using empty defaults`)
      return {
        filters: {
          categories: [],
          brands: [],
          segments: [],
          extend_fields: {}
        },
          timeframe: { period: '' } // 🔧 不设置硬编码默认值
      }
    }

    const result = {
      filters: {
        categories: chartState.filters.categories || [],
        brands: chartState.filters.brands || [],
        segments: chartState.filters.segments || [],
        extend_fields: chartState.filters.extend_fields || {}
      },
      timeframe: { period: chartState.timeframe?.period || '' } // 🔧 移除硬编码的 'year' 默认值
    }

    console.log(`🔍 [DATABASE-SERVICE] Retrieved filters for ${chartName}:`, result)
    return result
  }

  // 🆕 将 ProjectFilters 转换为 ChartFilterState 格式
  private convertProjectFiltersToChartState(filters: ProjectFilters): ChartFilterState {
    return {
      filters: {
        categories: filters.categories || [],
        brands: filters.brands || [],
        segments: filters.segments || [],
        extend_fields: filters.extend_fields || {}
      },
      timeframe: {
        period: filters.time_period || 'year'
      },
      metadata: {
        lastUpdated: Date.now(),
        appliedAt: Date.now()
      }
    }
  }

  // 🆕 同步 ProjectFilters 到过滤器状态管理器
  syncProjectFiltersToState(chartName: string, filters: ProjectFilters): void {
    const chartState = this.convertProjectFiltersToChartState(filters)
    filterStateManager.updateChartFilters(chartName, chartState)
    console.log(`🔄 [DATABASE-SERVICE] Synced ProjectFilters to state for ${chartName}`)
  }

  // 🆕 使用过滤器状态管理器获取项目概览数据
  async getProjectOverviewWithFilters(projectId: string, chartName: string = 'project') {
    const filters = this.getFiltersFromState(chartName)

    console.log(`🔍 [DATABASE-SERVICE] Getting project overview for ${chartName} with filters:`, filters)

    // 调用现有的 getProjectOverview 方法，使用正确的参数顺序
    return this.getProjectOverview(
      projectId,
      filters.filters.categories,
      filters.filters.brands,
      filters.filters.segments,
      filters.filters.extend_fields
    )
  }



  // 🔑 Get TAM Market Share data - 自动从过滤器状态管理器获取过滤器
  async getTAMMarketShareData(projectId: string, chartName: string = CHART_NAMES.MARKET_SHARE_ANALYSIS): Promise<TAMMarketShareResponse> {
    try {
      // 🆕 从过滤器状态管理器获取过滤器数据
      const filters = this.getFiltersFromState(chartName)

      console.log(`🔍 [DATABASE-SERVICE] Getting TAM data with filters from state manager:`, filters)

      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

      const requestBody = {
        project_id: projectId,
        ...filters  // 🎯 直接展开 getFiltersFromState 的结果
      }

      console.log('🔍 Calling TAM Market Share API:', requestBody)

      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/market-analysis/tam-market-share`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`TAM Market Share API call failed: ${response.status}`)
      }

      const result: TAMMarketShareResponse = await response.json()
      console.log('📊 TAM Market Share API response:', result)
      
      return result
    } catch (error) {
      console.error('Error fetching TAM Market Share data:', error)
      throw error
    }
  }

  // 🔑 Get brand category revenue data with project filtering via backend API
  async getBrandCategoryRevenueByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    brandCategoryRevenue: BrandCategoryData[]
    segmentNames: string[]
    segmentColors: string[]
  }> {
    try {
      const result = await callDashboardAPI('brand-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })

      return {
        brandCategoryRevenue: result.data || [],           // Backend returns all brands in 'data' field
        segmentNames: result.segmentNames || [],           // Backend returns 'segmentNames' field
        segmentColors: result.segmentColors || []          // Backend returns 'segmentColors' field
      }
    } catch (error) {
      console.error('Error fetching brand category revenue by project:', error)
      throw error
    }
  }

  // 🔑 Get product analysis data with project filtering via backend API
  async getProductAnalysisDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    priceVsRevenue: ProductAnalysisData['priceVsRevenue']
    topProducts: {
      segments: Record<string, any[]>
      dimmerSwitches: any[]
      lightSwitches: any[]
    }
    segmentSummary: Record<string, {
      totalRevenue: number
      totalVolume: number
      productCount: number
      avgPrice: number
      topBrand: string
    }>
    segmentNames: string[]
    segmentColors: string[]
  }> {
    try {
      const result = await callDashboardAPI('product-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      // If backend returns enhanced format, use it directly
      if (result.segmentNames && result.segmentColors && result.segmentSummary) {
        return {
          priceVsRevenue: result.priceVsRevenue || [],
          topProducts: result.topProducts || { segments: {}, dimmerSwitches: [], lightSwitches: [] },
          segmentSummary: result.segmentSummary || {},
          segmentNames: result.segmentNames || [],
          segmentColors: result.segmentColors || []
        }
      }
      
      // Fallback: Convert legacy format to expected format
      const segments: Record<string, any[]> = {}
      const segmentNames: string[] = []
      
      // Extract segments from topProducts
      result.topProducts?.forEach((category: any) => {
        if (category.category && category.products) {
          segments[category.category] = category.products
          if (!segmentNames.includes(category.category)) {
            segmentNames.push(category.category)
          }
        }
      })
      
      // Generate segment summary from available data
      const segmentSummary: Record<string, any> = {}
      Object.keys(segments).forEach(segment => {
        const products = segments[segment] || []
        segmentSummary[segment] = {
          totalRevenue: products.reduce((sum: number, p: any) => sum + (p.revenue || 0), 0),
          totalVolume: products.reduce((sum: number, p: any) => sum + (p.volume || 0), 0),
          productCount: products.length,
          avgPrice: products.length > 0 ? products.reduce((sum: number, p: any) => sum + (p.price || 0), 0) / products.length : 0,
          topBrand: products.length > 0 ? products[0].brand || 'N/A' : 'N/A'
        }
      })
      
      return {
        priceVsRevenue: result.priceVsRevenue || [],
        topProducts: {
          segments,
          dimmerSwitches: segments['Dimmer Switches'] || [],
          lightSwitches: segments['Light Switches'] || []
        },
        segmentSummary,
        segmentNames,
        segmentColors: ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"].slice(0, segmentNames.length)
      }
    } catch (error) {
      console.error('Error fetching product analysis data by project:', error)
      throw error
    }
  }

  // 🔑 Get pricing analysis data with project filtering via backend API
  async getPricingAnalysisDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    priceDistribution: Array<{
      category: string
      skuPrices: number[]
      unitPrices: number[]
      productCount: number
      stats: {
        sku: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
        unit: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
      }
    }>
    brandPriceDistribution: Array<{
      category: string
      brands: Array<{
        name: string
        skuPrices: number[]
        unitPrices: number[]
      }>
    }>
  }> {
    try {
      const result = await callDashboardAPI('pricing-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })

      return result
    } catch (error) {
      console.error('Error fetching pricing analysis data by project:', error)
      throw error
    }
  }

  // 🔑 Get market insights data with project filtering via backend API
  async getMarketInsightsDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    segmentRevenue: {
      segments?: Array<{
        segment: string
        revenue: number
        volume: number
        products: number
      }>
      segmentNames?: string[]
      dimmerSwitches: Array<{
        segment: string
        revenue: number
        volume: number
        products: number
      }>
      lightSwitches: Array<{
        segment: string
        revenue: number
        volume: number
        products: number
      }>
    }
  }> {
    try {
      const result = await callDashboardAPI('market-insights', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })

      return result
    } catch (error) {
      console.error('Error fetching market insights data by project:', error)
      throw error
    }
  }

  // 🔑 Get package preference data with project filtering via backend API
  async getPackagePreferenceDataByProject(projectId: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>, metricType?: string): Promise<{
    sameProductComparison: Array<{
      productName: string
      packSize: string
      packCount: number
      salesVolume: number
      price: number
      unitPrice: number
    }>
    packageDistribution: Array<{
      name: string
      packSize: string
      value: number
      salesRevenue: number
      count: number
      percentage: number
    }>
    segmentDistributions: Record<string, Array<{
      name: string
      packSize: string
      value: number
      salesRevenue: number
      count: number
      percentage: number
    }>>
    segmentNames: string[]
    segmentColors: string[]
    dimmerSwitches: Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
      salesRevenue: number
    }>
    lightSwitches: Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
      salesRevenue: number
    }>
  }> {
    try {
      const callParams = {
        categoryFilters,
        packagingTypeFilters: brandFilters,
        segmentFilters,
        extendFields,
        metricType
      }
      const result = await callDashboardAPI('package-preference', projectId, callParams)

      return result
    } catch (error) {
      console.error('Error fetching package preference data by project:', error)
      throw error
    }
  }

  // 🔑 Get review insights data with project filtering via backend API
  async getReviewInsightsDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    painPoints: Array<{
      aspect: string
      category: string
      severity: number
      frequency: number
      impactedProducts: number
      type: 'Physical' | 'Performance' | 'Usability'
      // Enhanced fields from new table structure
      categoryDefinition?: string
      totalMentions?: number
      negativeRate?: number
    }>
    customerLikes: Array<{
      feature: string
      category: string
      frequency: number
      satisfactionLevel: 'High' | 'Medium' | 'Low'
      // Enhanced fields from new table structure
      categoryDefinition?: string
      totalMentions?: number
      positiveRate?: number
    }>
    allUseCases: Array<{
      useCase: string
      productAttribute: string
      satisfactionRate: number
      mentionCount: number
      positiveCount: number
      negativeCount: number
      // Enhanced fields from new table structure
      categoryDefinition?: string
      productCount?: number
    }>
    underservedUseCases: Array<{
      useCase: string
      productAttribute: string
      gapLevel: number
      mentionCount: number
      // Enhanced fields from new table structure
      categoryDefinition?: string
      productCount?: number
    }>
    totalUseMentions: number
  }> {
    try {
      const result = await callDashboardAPI('review-insights', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })

      return result
    } catch (error) {
      console.error('Error fetching review insights data by project:', error)
      throw error
    }
  }

  // 🔑 Get competitor matrix view data via new API
  async getCompetitorMatrixViewData(
    projectId: string,
    selectedAsins: string[],
    aspectType: 'phy_perf' | 'use' = 'phy_perf'
  ): Promise<{
    status: string
    message?: string
    timestamp: string
    data: {
      aspect_categories: Array<{
        category_id: number
        category_name: string
        definition: string
      }>
      product_aspect_data: Array<{
        asin: string
        aspect_data: Array<{
          category_pk: number
          mentions: number
          reviews: number
          sentiment_counts: {
            positive: number
            negative: number
            neutral: number
          }
        }>
      }>
      selected_asins: string[]
      aspect_type: string
      total_categories: number
    }
  }> {
    try {
      const requestBody = {
        project_id: projectId,
        selected_asins: selectedAsins,
        aspect_type: aspectType,
        options: {
          sort_by: "mentions",
          sort_direction: "desc",
          max_categories: 10
        }
      }

      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/competitor-analysis/matrix-view`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Error fetching competitor matrix view data:', error)
      throw error
    }
  }

  // 🔑 Get reviews for specific category and product
  async getCompetitorReviews(
    projectId: string,
    categoryId: number,
    productId: string,
    limit: number = 100,
    offset: number = 0,
    sortBy: 'review_id' | 'date' | 'rating' | 'sentiment' = 'review_id',
    sortOrder: 'asc' | 'desc' = 'desc'
  ): Promise<{
    status: string
    message?: string
    timestamp: string
    data: {
      reviews: Array<{
        review_id: string
        review_title: string
        review_text: string
        rating: number
        verified: boolean
        review_date: string
        aspects: Array<{
          aspect_description: string
          sentiment: string
          aspect_type: string
        }>
        category_name: string
        category_definition: string
        aspect_type: string
      }>
      total_reviews: number
      project_id: string
      category_id: number
      product_id: string
      category_info: {
        category_pk: number
        name: string
        definition: string
        aspect_type: string
        stage: string
      }
      pagination: {
        limit: number
        offset: number
        has_more: boolean
      }
    }
  }> {
    try {
      const requestBody = {
        project_id: projectId,
        selected_asins: [productId], // 包装成数组格式
        category_id: categoryId,
        product_id: productId,
        limit: limit,
        offset: offset,
        sort_by: sortBy,
        sort_order: sortOrder
      }

      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/competitor-analysis/reviews`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Error fetching competitor reviews:', error)
      throw error
    }
  }

  // 🔑 Get competitor analysis data with project filtering via backend API
  async getCompetitorAnalysisDataByProject(projectId: string, categoryFilters?: string[], selectedAsins?: string, packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    targetProducts: string[]
    matrixData: Array<{
      product: string
      category: string
      categoryType: 'Physical' | 'Performance'
      mentions: number
      satisfactionRate: number
      positiveCount: number
      negativeCount: number
      totalReviews: number
    }>
    productTotalReviews: Record<string, number>
    useCaseData: {
      targetProducts: string[]
      matrixData: Array<{
        product: string
        useCase: string
        mentions: number
        satisfactionRate: number
        gapLevel: number
      }>
    }
    reviewContent?: Record<string, Array<{
      id: string
      productId: string
      text: string
      sentiment: 'positive' | 'negative' | 'neutral'
      category: string
      aspect: string
      rating: number
      verified: boolean
      date: string
      brand: string
    }>>
  }> {
    try {
      const result = await callDashboardAPI('competitor-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields,
        selectedAsins: selectedAsins ? selectedAsins.split(',') : undefined
      })

      return result
    } catch (error) {
      console.error('Error fetching competitor analysis data by project:', error)
      throw error
    }
  }

  // 🔑 Get reviews for a specific matrix cell (product-category combination)
  async getCompetitorCellReviews(
    projectId: string, 
    productAsin: string, 
    categoryName: string, 
    limit: number = 50, 
    offset: number = 0
  ): Promise<{
    reviews: Array<{
      id: string
      productId: string
      text: string
      sentiment: 'positive' | 'negative' | 'neutral'
      category: string
      aspect: string
      rating: number
      verified: boolean
      date: string
      brand: string
    }>
    product_asin: string
    category_name: string
    total_returned: number
    limit: number
    offset: number
  }> {
    try {
      const response = await fetch(`/api/dashboard/competitor-analysis/${projectId}/cell-reviews?product_asin=${encodeURIComponent(productAsin)}&category_name=${encodeURIComponent(categoryName)}&limit=${limit}&offset=${offset}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      return result
    } catch (error) {
      console.error('Error fetching competitor cell reviews:', error)
      throw error
    }
  }

  // 🔑 Get all review data for project filtering via backend API
  async getAllReviewDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<Record<string, Array<{
    id: string
    productId: string
    text: string
    sentiment: 'positive' | 'negative' | 'neutral'
    category: string
    aspect: string
    rating: number
    verified: boolean
    date: string
    brand: string
  }>>> {
    try {
      const result = await callDashboardAPI('all-review-data', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })

      return result.data || {}
    } catch (error) {
      console.error('Error fetching all review data by project:', error)
      throw error
    }
  }

  // 🔑 Get top categories data for review analysis
  async getTopCategoriesData(
    projectId: string,
    aspectType: 'phy_perf' | 'use' = 'phy_perf',
    options?: {
      sortBy?: 'negative_mentions' | 'positive_mentions' | 'total_mentions' | 'positive_ratio'
      sortDirection?: 'desc' | 'asc'
      maxCategories?: number
      minMentions?: number
      minPositiveMentions?: number
    },
    filters?: {
      categories?: string[]
      brands?: string[]
      segments?: string[]
      extend_fields?: Record<string, any>
      asins?: string[]
    }
  ): Promise<{
    status: string
    message?: string
    timestamp: string
    data: {
      categories: Array<{
        category_id: number
        category_name: string
        definition: string
        aspect_type: string
        total_mentions: number
        positive_mentions: number
        negative_mentions: number
        neutral_mentions: number
        total_reviews: number
        positive_reviews: number
        negative_reviews: number
        positive_ratio: number
      }>
      total_categories: number
      summary_stats: {
        total_categories: number
        total_mentions: number
        total_reviews: number
        total_positive_mentions: number
        total_negative_mentions: number
        overall_positive_ratio: number
      }
    }
  }> {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

      const requestBody = {
        project_id: projectId,
        filters: filters || {},
        options: {
          aspect_type: aspectType,
          sort_by: options?.sortBy || 'negative_mentions',
          sort_direction: options?.sortDirection || 'desc',
          max_categories: options?.maxCategories || 10,
          min_mentions: options?.minMentions || 5,
          min_positive_mentions: options?.minPositiveMentions || 2,
          ...options
        }
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/review-analysis/top-categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Error fetching top categories data:', error)
      throw error
    }
  }

  // � Get reviews by category for detailed view
  async getReviewsByCategory(
    projectId: string,
    categoryId: number,
    options?: {
      limit?: number
      offset?: number
      sortBy?: 'review_id' | 'rating' | 'review_date'
      sortOrder?: 'desc' | 'asc'
    },
    filters?: {
      categories?: string[]
      brands?: string[]
      segments?: string[]
      extend_fields?: Record<string, any>
      asins?: string[]
    }
  ): Promise<{
    status: string
    message?: string
    timestamp: string
    data: {
      reviews: Array<{
        review_id: number
        product_id: string
        review_text: string
        rating: number
        verified: boolean
        review_date: string
        brand: string
        sentiment: 'positive' | 'negative' | 'neutral'
        category_name: string
        category_definition: string
        aspects?: Array<{
          aspect_description: string
          sentiment: string
          aspect_type: string
        }>
      }>
      total_count: number
      category_info: {
        category_id: number
        category_name: string
        definition: string
      }
      pagination: {
        limit: number
        offset: number
        has_more: boolean
      }
    }
  }> {
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

      const requestBody = {
        project_id: projectId,
        category_id: categoryId,
        filters: filters || {},
        limit: options?.limit || 10,
        offset: options?.offset || 0,
        sort_by: options?.sortBy || 'review_id',
        sort_order: options?.sortOrder || 'desc'
      }

      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/review-analysis/reviews-by-category`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }

      const result = await response.json()
      return result
    } catch (error) {
      console.error('Error fetching reviews by category:', error)
      throw error
    }
  }

  // �📋 Data Confirmation 功能 - 保留直接Supabase访问
  async getDataConfirmationData(filters?: DataConfirmationFilters): Promise<DataConfirmationData> {
    try {
      // 构建查询条件
      let query = supabase
        .from('product_wide_table')
        .select(`
          platform_id,
          title,
          brand,
          category,
          source,
          past_year_volume,
          past_year_revenue,
          reviews_count,
          price_usd,
          product_segment,
          pack_count,
          unit_price_calculated,
          rating,
          product_url
        `)
        .eq('source', 'amazon')
        .neq('category', null)
        .neq('brand', null)

      // 应用筛选条件
      if (filters?.categories && filters.categories.length > 0) {
        query = query.in('category', filters.categories)
      }
      if (filters?.sources && filters.sources.length > 0) {
        query = query.in('source', filters.sources)
      }
      if (filters?.brands && filters.brands.length > 0) {
        query = query.in('brand', filters.brands)
      }

      // 先获取所有可用选项
      const { data: allData, error: allError } = await supabase
        .from('product_wide_table')
        .select('category, source, brand')
        .not('category', 'is', null)
        .not('brand', 'is', null)

      if (allError) {
        console.error('Error fetching all data options:', allError)
        throw allError
      }

      const availableCategories = [...new Set(allData.map(item => item.category))].sort()
      const availableSources = [...new Set(allData.map(item => item.source))].sort()
      const availableBrands = [...new Set(allData.map(item => item.brand))].sort()

      // 获取筛选后的数据
      const { data, error } = await query

      if (error) {
        console.error('Error fetching filtered data:', error)
        throw error
      }

      // 按销量排序
      const sortedProducts = (data as DataConfirmationProduct[])
        .filter((item: DataConfirmationProduct) => item.past_year_volume !== null)
        .sort((a: DataConfirmationProduct, b: DataConfirmationProduct) => (b.past_year_volume || 0) - (a.past_year_volume || 0))

      // 应用topSalesCount筛选到实际统计数据中
      const finalProducts = filters?.topSalesCount && filters.topSalesCount < data.length
        ? sortedProducts.slice(0, filters.topSalesCount)
        : (data as DataConfirmationProduct[])

      // 计算统计信息 - 基于最终筛选后的产品
      const totalProducts = finalProducts.length
      const totalBrands = new Set(finalProducts.map((item: DataConfirmationProduct) => item.brand)).size
      const totalReviews = finalProducts.reduce((sum: number, item: DataConfirmationProduct) => sum + (item.reviews_count || 0), 0)
      const avgMonthlySales = finalProducts
        .filter((item: DataConfirmationProduct) => item.past_year_volume !== null)
        .reduce((sum: number, item: DataConfirmationProduct, _, arr: DataConfirmationProduct[]) => sum + (item.past_year_volume || 0) / arr.length, 0)

      // 按来源统计 - 基于最终筛选结果
      const sourceStats = availableSources.map(source => {
        const count = finalProducts.filter((item: DataConfirmationProduct) => item.source === source).length
        return {
          name: source,
          count,
          percentage: totalProducts > 0 ? Math.round((count / totalProducts) * 100) : 0
        }
      }).filter(stat => stat.count > 0)

      // 按类别统计 - 基于最终筛选结果
      const categoryStats = availableCategories.map(category => {
        const count = finalProducts.filter((item: DataConfirmationProduct) => item.category === category).length
        return {
          name: category,
          count,
          percentage: totalProducts > 0 ? Math.round((count / totalProducts) * 100) : 0
        }
      }).filter(stat => stat.count > 0)

      // 按品牌统计（取前10个）- 基于最终筛选结果
      const brandCounts = finalProducts.reduce((acc: Record<string, number>, item: DataConfirmationProduct) => {
        acc[item.brand] = (acc[item.brand] || 0) + 1
        return acc
      }, {} as Record<string, number>)

      const brandStats = Object.entries(brandCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, 10)
        .map(([brand, count]) => ({
          name: brand,
          count,
          percentage: totalProducts > 0 ? Math.round((count / totalProducts) * 100) : 0
        }))

      const stats: DataConfirmationStats = {
        totalProducts,
        totalBrands,
        totalReviews,
        avgMonthlySales,
        sources: sourceStats,
        categories: categoryStats,
        brands: brandStats
      }

      // topProducts用于预览，取前几个
      const topProducts = sortedProducts.slice(0, Math.min(50, finalProducts.length))

      return {
        availableCategories,
        availableSources,
        availableBrands,
        stats,
        topProducts
      }
    } catch (error) {
      console.error('Error in getDataConfirmationData:', error)
      return {
        availableCategories: [],
        availableSources: [],
        availableBrands: [],
        stats: {
          totalProducts: 0,
          totalBrands: 0,
          totalReviews: 0,
          avgMonthlySales: 0,
          sources: [],
          categories: [],
          brands: []
        },
        topProducts: []
      }
    }
  }

  // 🏗️ Project管理相关方法 - 保留直接Supabase访问
  async saveProject(project: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<Project> {
    try {
      const { data, error } = await supabase
        .from('projects')
        .insert([project])
        .select()
        .single()

      if (error) throw error
      return data
    } catch (error) {
      console.error('Failed to save project:', error)
      throw error
    }
  }

  async updateProject(id: string, updates: Partial<Project>): Promise<Project> {
    try {
      const { data, error } = await supabase
        .from('projects')
        .update(updates)
        .eq('id', id)
        .select()
        .single()

      if (error) throw error
      return data
    } catch (error) {
      console.error('Failed to update project:', error)
      throw error
    }
  }

  async getProjects(userUid?: string): Promise<Project[]> {
    try {
      // First try to use backend API
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      
      // Build URL with user UID parameter if provided
      let url = `${API_BASE_URL}/api/v1/projects/`
      if (userUid) {
        url += `?user_uid=${encodeURIComponent(userUid)}`
      }
      
      console.log('🔍 [PROJECTS API] Fetching projects with user UID:', userUid)
      
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data || []
    } catch (error) {
      console.warn('Backend API not available, falling back to direct Supabase access:', error)
      
      // Fallback to direct Supabase access
      try {
        const { data, error: supabaseError } = await supabase
          .from('projects')
          .select('*')
          .eq('status', 'active')
          .order('created_at', { ascending: false })

        if (supabaseError) {
          console.error('Supabase error:', supabaseError)
          throw supabaseError
        }

        if (!data) {
          return []
        }

        // Process data to match the expected format
        const projects = data.map(project => {
          // Ensure required fields have default values
          const processedProject = {
            ...project,
            total_products: project.total_products || 0,
            total_brands: project.total_brands || 0,
            total_reviews: project.total_reviews || 0,
            avg_monthly_sales: project.avg_monthly_sales || 0.0,
            selected_categories: project.selected_categories || [],
            selected_sources: project.selected_sources || [],
            selected_brands: project.selected_brands || [],
            selected_product_asins: project.selected_product_asins || [],
          }
          return processedProject
        })

        return projects
      } catch (fallbackError) {
        console.error('Failed to get projects via Supabase fallback:', fallbackError)
        throw fallbackError
      }
    }
  }

  async getProject(id: string): Promise<Project | null> {
    try {
      // First try to use backend API
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/${id}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        if (response.status === 404) {
          return null
        }
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.warn('Backend API not available, falling back to direct Supabase access:', error)
      
      // Fallback to direct Supabase access
      try {
        const { data, error: supabaseError } = await supabase
          .from('projects')
          .select('*')
          .eq('id', id)
          .eq('status', 'active')
          .single()

        if (supabaseError) {
          console.error('Supabase error:', supabaseError)
          if (supabaseError.code === 'PGRST116') {
            // No rows returned
            return null
          }
          throw supabaseError
        }

        if (!data) {
          return null
        }

        // Process data to match the expected format
        const processedProject = {
          ...data,
          total_products: data.total_products || 0,
          total_brands: data.total_brands || 0,
          total_reviews: data.total_reviews || 0,
          avg_monthly_sales: data.avg_monthly_sales || 0.0,
          selected_categories: data.selected_categories || [],
          selected_sources: data.selected_sources || [],
          selected_brands: data.selected_brands || [],
          selected_product_asins: data.selected_product_asins || [],
        }

        return processedProject
      } catch (fallbackError) {
        console.error('Failed to get project via Supabase fallback:', fallbackError)
        return null
      }
    }
  }

  // 🔑 Get project overview data with optional filters
  async getProjectOverview(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    project_name: string
    created_at: string
    stats: {
      total_products: number
      total_brands: number
      total_reviews: number
      segment_count: number
    }
    distributions: {
      sources: Array<{
        name: string
        count: number
        percentage: number
      }>
      categories: Array<{
        name: string
        count: number
        percentage: number
      }>
    }
    available_categories: {
      flat_categories: string[]
      hierarchical_categories: Array<{
        parent_category: string
        parent_count: number
        children: Array<{
          category: string
          count: number
          percentage: number
        }>
      }>
      total_products: number
    }
  }> {
    try {
      console.log('🔍 [PROJECT OVERVIEW] Fetching with filters:', { categoryFilters, packagingTypeFilters, segmentFilters, extendFields })

      const result = await callDashboardAPI('project-overview', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })

      return result
    } catch (error) {
      console.error('Error fetching project overview:', error)
      throw error
    }
  }

  // 🔑 Get project segments
  async getProjectSegments(projectId: string): Promise<string[]> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/project-segments?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      return result.segments || []
    } catch (error) {
      console.error('Error fetching project segments:', error)
      return []
    }
  }

  // 🔑 Get available ASINs with product info for competitor selection
  async getAvailableAsins(projectId?: string): Promise<Array<{
    platform_id: string
    title: string
    brand: string
    price_usd: number
    reviews_count: number
    category: string
    monthly_sales_volume?: number
    product_url?: string
  }>> {
    if (projectId) {
      // Use project-specific method to get products with correct review counts
      const projectProducts = await this.getProjectProductsByReviewCount(projectId);
      return projectProducts.map(product => ({
        platform_id: product.platform_id,
        title: product.title,
        brand: product.brand,
        price_usd: product.price_usd,
        reviews_count: product.actual_review_count, // Use actual review count from project
        category: product.category,
        product_url: product.product_url
      }));
    } else {
      // Fallback to original logic for backwards compatibility
      const { data: products, error } = await supabase
        .from('product_wide_table')
        .select('platform_id, title, brand, price_usd, reviews_count, category, product_url')

      if (error) throw error
      return products || []
    }
  }

  // 🔑 Get project selected products ranked by analysis review count
  async getProjectProductsByReviewCount(projectId: string): Promise<Array<{
    platform_id: string
    title: string
    brand: string
    price_usd: number
    reviews_count: number
    actual_review_count: number
    category: string
    product_url?: string
    rating?: number | null
  }>> {
    const { data: projectData, error: projectError } = await supabase
      .from('projects')
      .select('selected_product_asins')
      .eq('id', projectId)
      .single()

    if (projectError) throw projectError
    if (!projectData?.selected_product_asins || projectData.selected_product_asins.length === 0) {
      return []
    }

    const selectedAsins = projectData.selected_product_asins as string[]

    // Get product details
    const { data: products, error: productsError } = await supabase
      .from('product_wide_table')
      .select('platform_id, title, brand, price_usd, reviews_count, category, product_url, rating')
      .in('platform_id', selectedAsins)

    if (productsError) throw productsError

    // Get analysis review counts for each product
    const productsWithCounts = await Promise.all(
      (products || []).map(async (product) => {
        // Get analysis review count from review_analysis_aspects and review_analysis_aspect_occurrences
        const { data: aspectsData } = await supabase
          .from('review_analysis_aspects')
          .select('aspect_pk')
          .eq('project_id', projectId)
          .eq('product_id', product.platform_id)

        let analysisReviewCount = 0
        if (aspectsData && aspectsData.length > 0) {
          const aspectPks = aspectsData.map(item => item.aspect_pk)
          
          // Get unique review_ids from aspect_occurrences
          const { data: occurrencesData } = await supabase
            .from('review_analysis_aspect_occurrences')
            .select('review_id')
            .in('aspect_pk', aspectPks)

          if (occurrencesData) {
            const uniqueReviewIds = new Set(occurrencesData.map(item => item.review_id))
            analysisReviewCount = uniqueReviewIds.size
          }
        }

        return {
          ...product,
          actual_review_count: analysisReviewCount // Use analysis review count as actual_review_count
        }
      })
    )

    return productsWithCounts.sort((a, b) => b.actual_review_count - a.actual_review_count)
  }

  // 🔑 Get project extend fields
  async getProjectExtendFields(projectId: string): Promise<ExtendFieldDefinition[]> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/extend-fields`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const result = await response.json()
      return result.extend_fields || []
    } catch (error) {
      console.error('Error fetching project extend fields:', error)
      return []
    }
  }

  // 🔑 Get project filter defaults
  async getProjectFilterDefaults(projectId: string): Promise<ProjectFilters> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      console.log(`🔍 [DatabaseService] Fetching filter defaults for project: ${projectId}`)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/filter-defaults`)
      
      if (!response.ok) {
        console.warn(`⚠️ [DatabaseService] Failed to fetch filter defaults: HTTP ${response.status}`)
        return DEFAULT_FILTERS
      }
      
      const result = await response.json()
      let filters = result.filters || DEFAULT_FILTERS
      
      // 🔧 Set default values for Smart Capability: select both Non-Smart and Smart by default
      if (!filters.extend_fields) {
        filters.extend_fields = {}
      }
      
      if (!filters.extend_fields.smart_capability) {
        filters.extend_fields.smart_capability = ['Non-Smart', 'Smart']
        console.log(`🔧 [DatabaseService] Set Smart Capability default values: ['Non-Smart', 'Smart']`)
      }
      
      console.log(`✅ [DatabaseService] Retrieved filter defaults:`, filters)
      return filters
      
    } catch (error) {
      console.error('❌ [DatabaseService] Error fetching project filter defaults:', error)
      // 🔧 Also set Smart Capability defaults in error fallback
      const defaultFilters = { ...DEFAULT_FILTERS }
      defaultFilters.extend_fields.smart_capability = ['Non-Smart', 'Smart']
      console.log(`🔧 [DatabaseService] Set Smart Capability default values in fallback: ['Non-Smart', 'Smart']`)
      return defaultFilters
    }
  }

  /**
   * 🆕 获取项目过滤器默认配置（新版API）
   */
  async getProjectFilterDefaultsNew(projectId: string): Promise<FilterDefaultsResponse> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      console.log('🔍 [FILTER-DEFAULTS] Fetching filter defaults for project:', projectId)
      
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/filter-defaults`, {
        method: 'GET',
        headers: {
          'accept': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: FilterDefaultsResponse = await response.json()
      
      console.log('🔍 [FILTER-DEFAULTS] Raw API response:', data)
      
      return data
    } catch (error) {
      console.error('🚨 [FILTER-DEFAULTS] Error fetching filter defaults:', error)
      throw error
    }
  }
}

export const databaseService = new DatabaseService() 