import { supabase } from '@/lib/supabase'

export interface ProductData {
  platform_id: string
  title: string
  brand: string
  price_usd: number
  monthly_sales_volume: number | null
  estimated_revenue: number | null
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
  category: string
  source: string
  monthly_sales_volume: number | null
  estimated_revenue: number | null
  reviews_count: number
  price_usd: number
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
  segments: Record<string, { revenue: number; volume: number }>
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

export class DatabaseService {
  
  // 🔑 Get brand category revenue data with project filtering via backend API
  async getBrandCategoryRevenueByProject(projectId: string): Promise<{
    brandCategoryRevenue: BrandCategoryData[]
    segmentNames: string[]
    segmentColors: string[]
  }> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/brand-analysis?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      const result = await response.json()
      return {
        brandCategoryRevenue: result.data || [],
        segmentNames: result.segmentNames || [],
        segmentColors: result.segmentColors || []
      }
    } catch (error) {
      console.error('Error fetching brand category revenue by project:', error)
      throw error
    }
  }

  // 🔑 Get product analysis data with project filtering via backend API
  async getProductAnalysisDataByProject(projectId: string): Promise<{
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/product-analysis?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      const result = await response.json()
      
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
  async getPricingAnalysisDataByProject(projectId: string): Promise<{
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/pricing-analysis?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      const result = await response.json()
      return {
        priceDistribution: result.priceDistribution || [],
        brandPriceDistribution: result.brandPriceDistribution || []
      }
    } catch (error) {
      console.error('Error fetching pricing analysis data by project:', error)
      throw error
    }
  }

  // 🔑 Get market insights data with project filtering via backend API
  async getMarketInsightsDataByProject(projectId: string): Promise<{
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/market-insights?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      const result = await response.json()
      
      // Return the enhanced format that supports both new and legacy formats
      return {
        segmentRevenue: {
          segments: result.segmentRevenue?.segments || [],
          segmentNames: result.segmentRevenue?.segmentNames || [],
          dimmerSwitches: result.segmentRevenue?.dimmerSwitches || [],
          lightSwitches: result.segmentRevenue?.lightSwitches || []
        }
      }
    } catch (error) {
      console.error('Error fetching market insights data by project:', error)
      throw error
    }
  }

  // 🔑 Get package preference data with project filtering via backend API
  async getPackagePreferenceDataByProject(projectId: string): Promise<{
    sameProductComparison: Array<{
      productName: string
      packSize: string
      packCount: number
      salesVolume: number
      price: number
      unitPrice: number
    }>
    packageDistribution: Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
    }>
    segmentDistributions?: Record<string, Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
      salesRevenue: number
    }>>
    segmentNames?: string[]
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/package-preference?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      const result = await response.json()
      return {
        sameProductComparison: result.sameProductComparison || [],
        packageDistribution: result.packageDistribution || [],
        segmentDistributions: result.segmentDistributions || {},
        segmentNames: result.segmentNames || [],
        dimmerSwitches: result.dimmerSwitches || [],
        lightSwitches: result.lightSwitches || []
      }
    } catch (error) {
      console.error('Error fetching package preference data by project:', error)
      throw error
    }
  }

  // 🔑 Get review insights data with project filtering via backend API
  async getReviewInsightsDataByProject(projectId: string): Promise<{
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
    underservedUseCases: Array<{
      useCase: string
      productAttribute: string
      gapLevel: number
      mentionCount: number
      // Enhanced fields from new table structure
      categoryDefinition?: string
      productCount?: number
    }>
  }> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/review-insights?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      return {
        painPoints: data.painPoints || [],
        customerLikes: data.customerLikes || [],
        underservedUseCases: data.underservedUseCases || []
      }
    } catch (error) {
      console.error('Error fetching review insights data by project:', error)
      throw error
    }
  }

  // 🔑 Get competitor analysis data with project filtering via backend API
  async getCompetitorAnalysisDataByProject(projectId: string, selectedAsins?: string): Promise<{
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
  }> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      let url = `${API_BASE_URL}/api/v1/dashboard/competitor-analysis?project_id=${projectId}`
      if (selectedAsins) {
        url += `&selected_asins=${selectedAsins}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      const data = await response.json()
      return {
        targetProducts: data.targetProducts || [],
        matrixData: data.matrixData || [],
        productTotalReviews: data.productTotalReviews || {},
        useCaseData: {
          targetProducts: data.useCaseData?.targetProducts || [],
          matrixData: data.useCaseData?.matrixData || []
        }
      }
    } catch (error) {
      console.error('Error fetching competitor analysis data by project:', error)
      throw error
    }
  }

  // 🔑 Get all review data with project filtering via backend API
  async getAllReviewDataByProject(projectId: string): Promise<Record<string, Array<{
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/all-review-data?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      const result = await response.json()
      return result.data || {}
    } catch (error) {
      console.error('Error fetching all review data by project:', error)
      throw error
    }
  }

  // 📋 Data Confirmation 功能 - 保留直接Supabase访问
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
          monthly_sales_volume,
          estimated_revenue,
          reviews_count,
          price_usd
        `)
        .not('category', 'is', null)
        .not('brand', 'is', null)

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
        .filter((item: DataConfirmationProduct) => item.monthly_sales_volume !== null)
        .sort((a: DataConfirmationProduct, b: DataConfirmationProduct) => (b.monthly_sales_volume || 0) - (a.monthly_sales_volume || 0))

      // 应用topSalesCount筛选到实际统计数据中
      const finalProducts = filters?.topSalesCount && filters.topSalesCount < data.length
        ? sortedProducts.slice(0, filters.topSalesCount)
        : (data as DataConfirmationProduct[])

      // 计算统计信息 - 基于最终筛选后的产品
      const totalProducts = finalProducts.length
      const totalBrands = new Set(finalProducts.map((item: DataConfirmationProduct) => item.brand)).size
      const totalReviews = finalProducts.reduce((sum: number, item: DataConfirmationProduct) => sum + (item.reviews_count || 0), 0)
      const avgMonthlySales = finalProducts
        .filter((item: DataConfirmationProduct) => item.monthly_sales_volume !== null)
        .reduce((sum: number, item: DataConfirmationProduct, _, arr: DataConfirmationProduct[]) => sum + (item.monthly_sales_volume || 0) / arr.length, 0)

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

  async getProjects(): Promise<Project[]> {
    try {
      // 使用后端API获取项目列表
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/`, {
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
      console.error('Failed to get projects:', error)
      throw error
    }
  }

  async getProject(id: string): Promise<Project | null> {
    try {
      // Use backend API to get project info, consistent with getProjects
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
      console.error('Failed to get project:', error)
      return null
    }
  }

  // 🔑 Get project overview data
  async getProjectOverview(projectId: string): Promise<{
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
    available_categories: string[]
  }> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/project-overview?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching project overview:', error)
      throw error
    }
  }

  // 🔑 Get available ASINs with product info for competitor selection
  async getAvailableAsins(projectId: string): Promise<Array<{
    platform_id: string
    title: string
    brand: string
    price_usd: number
    reviews_count: number
    category: string
  }>> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/available-asins?project_id=${projectId}`)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching available ASINs:', error)
      throw error
    }
  }
}

export const databaseService = new DatabaseService() 