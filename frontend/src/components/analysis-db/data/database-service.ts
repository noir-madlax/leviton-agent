import { supabase } from '@/lib/supabase'
import { ExtendFieldDefinition } from '../types/filters'

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
  categories: Record<string, { revenue: number; volume: number }>
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
  
  // 🔑 Get top 10 brand category revenue data with project filtering via backend API
  async getBrandCategoryRevenueByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
    brandCategoryRevenue: BrandCategoryData[]
    segmentNames: string[]
    segmentColors: string[]
  }> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      let url = `${API_BASE_URL}/api/v1/dashboard/brand-analysis?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      const result = await response.json()
      return {
        brandCategoryRevenue: result.data || [],           // Backend returns top 10 brands in 'data' field
        segmentNames: result.segmentNames || [],           // Backend returns 'segmentNames' field 
        segmentColors: result.segmentColors || []          // Backend returns 'segmentColors' field
      }
    } catch (error) {
      console.error('Error fetching top 10 brand category revenue by project:', error)
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      let url = `${API_BASE_URL}/api/v1/dashboard/product-analysis?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      const response = await fetch(url)
      
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      let url = `${API_BASE_URL}/api/v1/dashboard/pricing-analysis?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      return await response.json()
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      let url = `${API_BASE_URL}/api/v1/dashboard/market-insights?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching market insights data by project:', error)
      throw error
    }
  }

  // 🔑 Get package preference data with project filtering via backend API
  async getPackagePreferenceDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<{
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
      let url = `${API_BASE_URL}/api/v1/dashboard/package-preference?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      return await response.json()
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
      let url = `${API_BASE_URL}/api/v1/dashboard/review-insights?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching review insights data by project:', error)
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
  }> {
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      let url = `${API_BASE_URL}/api/v1/dashboard/competitor-analysis?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add selected ASINs if provided
      if (selectedAsins) {
        url += `&selected_asins=${encodeURIComponent(selectedAsins)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`API call failed: ${response.status}`)
      }
      
      return await response.json()
    } catch (error) {
      console.error('Error fetching competitor analysis data by project:', error)
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      let url = `${API_BASE_URL}/api/v1/dashboard/all-review-data?project_id=${projectId}`
      
      // Add category filters if provided
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      // Add packaging type filters if provided
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      // Add segment filters if provided
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      // Add extend fields if provided
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      const response = await fetch(url)
      
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
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    
    try {
      // Build URL with all filters
      let url = `${API_BASE_URL}/api/v1/dashboard/project-overview?project_id=${projectId}`
      
      if (categoryFilters && categoryFilters.length > 0) {
        const categoriesParam = categoryFilters.join(',')
        url += `&categories=${encodeURIComponent(categoriesParam)}`
      }
      
      if (packagingTypeFilters && packagingTypeFilters.length > 0) {
        const packagingTypesParam = packagingTypeFilters.join(',')
        url += `&packaging_types=${encodeURIComponent(packagingTypesParam)}`
      }
      
      if (segmentFilters && segmentFilters.length > 0) {
        const segmentsParam = segmentFilters.join(',')
        url += `&segments=${encodeURIComponent(segmentsParam)}`
      }
      
      if (extendFields && Object.keys(extendFields).length > 0) {
        const extendFieldsParam = JSON.stringify(extendFields)
        url += `&extend_fields=${encodeURIComponent(extendFieldsParam)}`
      }
      
      console.log('🔍 [PROJECT OVERVIEW] Fetching with filters:', { categoryFilters, packagingTypeFilters, segmentFilters, extendFields })
      
      const response = await fetch(url)
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      
      return await response.json()
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
  async getAvailableAsins(): Promise<Array<{
    platform_id: string
    title: string
    brand: string
    price_usd: number
    reviews_count: number
    category: string
    monthly_sales_volume?: number
    product_url?: string
  }>> {
    const { data: products, error } = await supabase
      .from('product_wide_table')
      .select('platform_id, title, brand, price_usd, reviews_count, category, product_url')

    if (error) throw error
    return products || []
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
      .select('platform_id, title, brand, price_usd, reviews_count, category, product_url')
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
}

export const databaseService = new DatabaseService() 