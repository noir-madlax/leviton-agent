"use client"

import { useState, useEffect, useCallback, useRef } from 'react'
import { Tabs, TabsContent } from '@/components/ui/tabs'
import { PricingAnalysis } from "@/components/analysis-db/pricing-analysis"
import { BrandAnalysis } from "@/components/analysis-db/market-analysis/brand-analysis"
import { ReviewInsights } from "@/components/analysis-db/review-insights/review-insights"
import { CompetitorAnalysis } from "@/components/analysis-db/competitor-analysis/competitor-analysis"
import { ProductPanelProvider } from './contexts/product-panel-context'
import { ReviewPanelProvider } from './contexts/review-panel-context'
import { ProductPanel } from "@/components/analysis-db/panels/product-panel"
import { ReviewPanel } from "@/components/analysis-db/panels/review-panel"
import { databaseService, type ProductAnalysisData, type TAMMarketShareResponse } from '@/components/analysis-db/data/database-service'
import { PageDivider } from '@/components/ui/page-divider'
import { ProjectFilters, DEFAULT_FILTERS } from './types/filters'
import { ProjectFilterWrapper } from '@/components/integrated-dashboard/components/project-filter-wrapper'
import { SALES_TREND_DATE_RANGE } from "@/app/chat/charts/sales_trend/services/sales-trend-api";
import { useUnifiedFilter } from './contexts/unified-filter-context'

interface DashboardData {
  brandAnalysis: {
    brandCategoryRevenue: Array<{
      brand: string
      categories: Record<string, { revenue: number; volume: number; product_count: number }>
      dimmerRevenue: number
      switchRevenue: number
      dimmerVolume: number
      switchVolume: number
    }>
    categoryNames: string[]
    categoryColors: string[]
  }
  tamMarketShare?: TAMMarketShareResponse
  productAnalysis: {
    priceVsRevenue: ProductAnalysisData['priceVsRevenue']
    topProducts: {
      segments: Record<string, Array<{
        id: string
        name: string
        brand: string
        price: number
        unitPrice: number
        revenue: number
        volume: number
        url: string
      }>>
      dimmerSwitches: Array<{
        id: string
        name: string
        brand: string
        price: number
        unitPrice: number
        revenue: number
        volume: number
        url: string
      }>
      lightSwitches: Array<{
        id: string
        name: string
        brand: string
        price: number
        unitPrice: number
        revenue: number
        volume: number
        url: string
      }>
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
  }
  pricingAnalysis: {
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
  }
  marketInsights: {
    segmentRevenue: {
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
  }
  packagePreference: {
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
  }
  reviewInsights: {
    painPoints: Array<{
      aspect: string
      category: string
      severity: number
      frequency: number
      impactedProducts: number
      type: 'Physical' | 'Performance' | 'Usability'
      // Enhanced fields from backend
      category_name?: string
      total_reviews?: number
      positive_reviews?: number
      negative_reviews?: number
      negative_rate?: number
      satisfaction_rate?: number
      category_definition?: string
      category_id?: number
      categoryId?: number // Add categoryId for review panel functionality
      related_detail_texts?: string[]
    }>
    customerLikes: Array<{
      feature: string
      category: string
      frequency: number
      satisfactionLevel: 'High' | 'Medium' | 'Low'
      // Enhanced fields from backend
      category_name?: string
      total_reviews?: number
      positive_reviews?: number
      negative_reviews?: number
      positive_rate?: number
      category_definition?: string
      category_id?: number
      categoryId?: number // Add categoryId for review panel functionality
      related_detail_texts?: string[]
    }>
    allUseCases: Array<{
      useCase: string
      productAttribute: string
      satisfactionRate: number
      positiveReviews: number
      negativeReviews: number
      categoryDefinition?: string
      productCount?: number
      // Enhanced fields from backend
      use_case?: string
      total_reviews?: number
      category_definition?: string
      category_id?: number
      categoryId?: number // Add categoryId for review panel functionality
      related_detail_texts?: string[]
    }>
  }

  allReviewData: Record<string, Array<{
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
  salesTrend: {
    byCategory: Record<string, {
      trend_data: Array<{
        month: string
        [brandName: string]: { revenue: number; volume: number } | string
      }>
      brands: string[]
      summary: {
        total_brands: number
        date_range: { start: string; end: string }
        total_revenue: number
        total_volume: number
      }
    }>
    categories: string[]
  }
}

// 🚫 移除 fetchTAMMarketShareData 函数，TAM 数据现在由 brand-analysis.tsx 组件自己管理

// 获取品牌分析数据的async函数 (保留用于其他图表)
async function fetchBrandAnalysisData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>) {
  try {
    if (!projectId) {
      console.log('⏳ Brand Analysis waiting for project selection...');
      return { brandCategoryRevenue: [], categoryNames: [], categoryColors: [] };
    }
    
    console.log(`📊 Fetching Brand Analysis data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    if (brandFilters && brandFilters.length > 0) {
      console.log(`📦 Applying packaging filters: ${brandFilters.join(', ')}`);
    }
    if (segmentFilters && segmentFilters.length > 0) {
      console.log(`🎯 Applying segment filters: ${segmentFilters.join(', ')}`);
    }
    if (extendFields && Object.keys(extendFields).length > 0) {
      console.log(`🔧 Applying extend fields: ${JSON.stringify(extendFields)}`);
    }
    
    const data = await databaseService.getBrandCategoryRevenueByProject(projectId, categoryFilters, brandFilters, segmentFilters, extendFields);
    console.log(`📈 Brand Analysis data received: ${data.brandCategoryRevenue.length} brands, ${data.segmentNames.length} segments`);
    console.log(`  Segments: ${data.segmentNames.join(', ')}`);
    
    // 转换数据结构以匹配DashboardData.brandAnalysis接口
    return {
      brandCategoryRevenue: data.brandCategoryRevenue,
      categoryNames: data.segmentNames,  // 将segmentNames重命名为categoryNames
      categoryColors: data.segmentColors
    };
  } catch (error) {
    console.error('Error fetching brand analysis data:', error);
    return {
      brandCategoryRevenue: [
        { brand: 'Loading failed...', categories: {}, dimmerRevenue: 0, switchRevenue: 0, dimmerVolume: 0, switchVolume: 0 }
      ],
      categoryNames: ['Dimmer Switches', 'Light Switches'],  // 修复这里也使用categoryNames
      categoryColors: ["#FF6B6B", "#4ECDC4"]
    };
  }
}

// 获取销售趋势数据的async函数 - 为每个category分别获取数据
async function fetchSalesTrendData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>) {
  try {
    if (!projectId) {
      console.log('⏳ Sales Trend waiting for project selection...');
      return {
        byCategory: {},
        categories: []
      };
    }
    
    console.log(`📊 Fetching Sales Trend data for project: ${projectId}`);
    
    // 获取项目的所有categories（从brandAnalysis或直接获取）
    let availableCategories: string[] = [];
    if (categoryFilters && categoryFilters.length > 0) {
      availableCategories = categoryFilters;
    } else {
      // 如果没有指定categories，获取项目的所有categories
      try {
        const brandData = await databaseService.getBrandCategoryRevenueByProject(projectId);
        availableCategories = brandData.segmentNames || [];
             } catch {
         console.warn('Failed to get categories, using fallback');
         availableCategories = ['Dimmer Switches', 'Light Switches'];
       }
    }
    
    console.log(`🔍 Will fetch sales trend for categories: ${availableCategories.join(', ')}`);
    
    // 为每个category分别获取数据
    const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const categoryDataPromises = availableCategories.map(async (category) => {
      try {
        console.log(`📊 Fetching sales trend for category: ${category}`);
        const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/sales-trend`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            project_id: projectId,
            filters: {
              categories: [category], // 为每个category单独请求
              brands: brandFilters,
              segments: segmentFilters,
              extend_fields: extendFields
            },
            date_range: SALES_TREND_DATE_RANGE,
            aggregation: "monthly"
          })
        });
        
        if (!response.ok) {
          throw new Error(`Failed to fetch sales trend data for ${category}: ${response.statusText}`);
        }
        
        const data = await response.json();
        console.log(`📈 Sales Trend data received for ${category}: ${data.brands?.length || 0} brands, ${data.trend_data?.length || 0} months`);
        
        return { category, data };
      } catch (error) {
        console.error(`Error fetching sales trend data for category ${category}:`, error);
        return {
          category,
          data: {
            trend_data: [],
            brands: [],
            summary: {
              total_brands: 0,
              date_range: { start: "2025-01-01", end: "2025-06-30" },
              total_revenue: 0,
              total_volume: 0
            }
          }
        };
      }
    });
    
    // 等待所有category的数据
    const categoryResults = await Promise.all(categoryDataPromises);
    
    // 组织成按category分组的数据结构
    const byCategory: Record<string, {
      trend_data: Array<{
        month: string
        [brandName: string]: { revenue: number; volume: number } | string
      }>
      brands: string[]
      summary: {
        total_brands: number
        date_range: { start: string; end: string }
        total_revenue: number
        total_volume: number
      }
    }> = {};
    categoryResults.forEach(({ category, data }) => {
      byCategory[category] = data;
    });
    
    console.log(`📈 Sales Trend data fetching completed for ${availableCategories.length} categories`);
    
    return {
      byCategory,
      categories: availableCategories
    };
  } catch (error) {
    console.error('Error fetching sales trend data:', error);
    return {
      byCategory: {},
      categories: []
    };
  }
}

async function fetchProductAnalysisData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>) {
  try {
    if (!projectId) {
      console.log('⏳ Product Analysis waiting for project selection...');
      return { 
        priceVsRevenue: [], 
        topProducts: { segments: {}, dimmerSwitches: [], lightSwitches: [] },
        segmentSummary: {},
        segmentNames: [],
        segmentColors: []
      };
    }
    
    console.log(`📊 Fetching Product Analysis data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    if (brandFilters && brandFilters.length > 0) {
      console.log(`📦 Applying packaging filters: ${brandFilters.join(', ')}`);
    }
    if (segmentFilters && segmentFilters.length > 0) {
      console.log(`🎯 Applying segment filters: ${segmentFilters.join(', ')}`);
    }
    if (extendFields && Object.keys(extendFields).length > 0) {
      console.log(`🔧 Applying extend fields: ${JSON.stringify(extendFields)}`);
    }
    
    const data = await databaseService.getProductAnalysisDataByProject(projectId, categoryFilters, brandFilters, segmentFilters, extendFields);
    console.log(`📈 Product Analysis data received: ${data.priceVsRevenue.length} price vs revenue categories, ${data.segmentNames.length} segments`);
    console.log(`  Segments: ${data.segmentNames.join(', ')}`);
    console.log(`  Segment summary keys: ${Object.keys(data.segmentSummary).join(', ')}`);
    
    return data;
  } catch (error) {
    console.error('Error fetching product analysis data:', error);
    return {
      priceVsRevenue: [
        { category: 'Dimmer Switches', products: [] },
        { category: 'Light Switches', products: [] }
      ],
      topProducts: {
        segments: {},
        dimmerSwitches: [],
        lightSwitches: []
      },
      segmentSummary: {},
      segmentNames: [],
      segmentColors: []
    };
  }
}

async function fetchPricingAnalysisData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>) {
  try {
    if (!projectId) {
      console.log('⏳ Pricing Analysis waiting for project selection...');
      return { priceDistribution: [], brandPriceDistribution: [] };
    }
    
    console.log(`📊 Fetching Pricing Analysis data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    if (brandFilters && brandFilters.length > 0) {
      console.log(`📦 Applying packaging filters: ${brandFilters.join(', ')}`);
    }
    if (segmentFilters && segmentFilters.length > 0) {
      console.log(`🎯 Applying segment filters: ${segmentFilters.join(', ')}`);
    }
    if (extendFields && Object.keys(extendFields).length > 0) {
      console.log(`🔧 Applying extend fields: ${JSON.stringify(extendFields)}`);
    }
    
    const data = await databaseService.getPricingAnalysisDataByProject(projectId, categoryFilters, brandFilters, segmentFilters, extendFields);
    console.log(`📈 Pricing Analysis data received: ${data.priceDistribution.length} price distributions, ${data.brandPriceDistribution.length} brand distributions`);
    
    return data;
  } catch (error) {
    console.error('Error fetching pricing analysis data:', error);
    return { priceDistribution: [], brandPriceDistribution: [] };
  }
}

async function fetchMarketInsightsData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>) {
  try {
    if (!projectId) {
      console.log('⏳ Market Insights waiting for project selection...');
      return { segmentRevenue: { dimmerSwitches: [], lightSwitches: [] } };
    }
    
    console.log(`📊 Fetching Market Insights data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    if (brandFilters && brandFilters.length > 0) {
      console.log(`📦 Applying packaging filters: ${brandFilters.join(', ')}`);
    }
    if (segmentFilters && segmentFilters.length > 0) {
      console.log(`🎯 Applying segment filters: ${segmentFilters.join(', ')}`);
    }
    if (extendFields && Object.keys(extendFields).length > 0) {
      console.log(`🔧 Applying extend fields: ${JSON.stringify(extendFields)}`);
    }
    
    const data = await databaseService.getMarketInsightsDataByProject(projectId, categoryFilters, brandFilters, segmentFilters, extendFields);
    const totalSegments = data.segmentRevenue.dimmerSwitches.length + data.segmentRevenue.lightSwitches.length;
    console.log(`📈 Market Insights data received: ${totalSegments} segments total`);
    
    return data;
  } catch (error) {
    console.error('Error fetching market insights data:', error);
    return { segmentRevenue: { dimmerSwitches: [], lightSwitches: [] } };
  }
}

async function fetchPackagePreferenceData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>, metricType?: string) {
  try {
    if (!projectId) {
      console.log('⏳ Package Preference waiting for project selection...');
      return { 
        sameProductComparison: [], 
        packageDistribution: [],
        segmentDistributions: {},
        segmentNames: [],
        segmentColors: [],
        dimmerSwitches: [], 
        lightSwitches: [] 
      };
    }
    
    console.log(`📊 Fetching Package Preference data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    if (brandFilters && brandFilters.length > 0) {
      console.log(`📦 Applying packaging filters: ${brandFilters.join(', ')}`);
    }
    if (segmentFilters && segmentFilters.length > 0) {
      console.log(`🎯 Applying segment filters: ${segmentFilters.join(', ')}`);
    }
    if (extendFields && Object.keys(extendFields).length > 0) {
      console.log(`🔧 Applying extend fields: ${JSON.stringify(extendFields)}`);
    }
    
    const data = await databaseService.getPackagePreferenceDataByProject(projectId, categoryFilters, brandFilters, segmentFilters, extendFields, metricType);
    console.log(`✅ Package Preference data received: ${data.packageDistribution.length} package distributions`);
    
    return data;
  } catch (error) {
    console.error('Error fetching package preference data:', error);
    return {
      sameProductComparison: [],
      packageDistribution: [],
      segmentDistributions: {},
      segmentNames: [],
      segmentColors: [],
      dimmerSwitches: [],
      lightSwitches: []
    };
  }
}

async function fetchReviewInsightsData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>) {
  try {
    if (!projectId) {
      console.log('⏳ Review Insights waiting for project selection...');
      return { 
        painPoints: [], 
        customerLikes: [], 
        allUseCases: [], 
        underservedUseCases: [],
        totalUseMentions: 0
      };
    }
    
    console.log(`📊 Fetching Review Insights data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    if (brandFilters && brandFilters.length > 0) {
      console.log(`📦 Applying packaging filters: ${brandFilters.join(', ')}`);
    }
    if (segmentFilters && segmentFilters.length > 0) {
      console.log(`🎯 Applying segment filters: ${segmentFilters.join(', ')}`);
    }
    if (extendFields && Object.keys(extendFields).length > 0) {
      console.log(`🔧 Applying extend fields: ${JSON.stringify(extendFields)}`);
    }
    
    const data = await databaseService.getReviewInsightsDataByProject(projectId, categoryFilters, brandFilters, segmentFilters, extendFields);
    console.log(`📈 Review Insights data received: ${data.painPoints.length} pain points, ${data.customerLikes.length} likes, ${data.allUseCases.length} all use cases`);
    
    return data;
  } catch (error) {
    console.error('Error fetching review insights data:', error);
    return { 
      painPoints: [], 
      customerLikes: [], 
      allUseCases: []
    };
  }
}



async function fetchAllReviewData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>): Promise<Pick<DashboardData, 'allReviewData'>> {
  try {
    if (!projectId) {
      console.log('⏳ All Review Data waiting for project selection...');
      return { allReviewData: {} };
    }
    
    console.log(`📊 Fetching All Review Data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    if (brandFilters && brandFilters.length > 0) {
      console.log(`📦 Applying packaging filters: ${brandFilters.join(', ')}`);
    }
    if (segmentFilters && segmentFilters.length > 0) {
      console.log(`🎯 Applying segment filters: ${segmentFilters.join(', ')}`);
    }
    if (extendFields && Object.keys(extendFields).length > 0) {
      console.log(`🔧 Applying extend fields: ${JSON.stringify(extendFields)}`);
    }
    
    const data = await databaseService.getAllReviewDataByProject(projectId, categoryFilters, brandFilters, segmentFilters, extendFields);
    console.log(`📈 All Review Data received: ${Object.keys(data).length} aspects`);
    
    return { allReviewData: data };
  } catch (error) {
    console.error('Error fetching all review data:', error);
    return { allReviewData: {} };
  }
}

interface AnalysisDbContainerProps {
  selectedProjectId?: string | null;
  filters?: ProjectFilters;
  activeTab?: string;
}

// 内部组件：读取Context数据并渲染内容
function AnalysisDbContent({ selectedProjectId: initialProjectId, filters, activeTab: externalActiveTab }: AnalysisDbContainerProps) {
  // 🆕 读取统一过滤器数据
  const { filterData: unifiedFilterData, isLoading: filterDataLoading } = useUnifiedFilter()
  const [data, setData] = useState<Partial<DashboardData>>({})
  const [loading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialProjectId || null)
  const [currentActiveTab, setCurrentActiveTab] = useState<string>('brand-analysis')
  // Use state for filters to allow for async update from DB defaults
  const [currentFilters, setCurrentFilters] = useState<ProjectFilters>(filters || DEFAULT_FILTERS);

  
  // 为每个数据部分单独管理加载状态
  const [loadingStates, setLoadingStates] = useState({
    brandAnalysis: false,
    tamMarketShare: false,
    productAnalysis: false,
    pricingAnalysis: false,
    marketInsights: false,
    packagePreference: false,
    reviewInsights: false,
    competitorAnalysis: false,
    allReviewData: false,
    salesTrend: false
  })

  // 跟踪已加载的数据
  const [loadedData, setLoadedData] = useState<Set<string>>(new Set())
  const loadedDataRef = useRef<Set<string>>(new Set())

  // 保持 ref 与 state 同步
  useEffect(() => {
    loadedDataRef.current = loadedData
  }, [loadedData])

  const loadSpecificData = useCallback(async (dataType: keyof typeof loadingStates, projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, unknown>, forceReload = false) => {
    if (!projectId) return
    
    // 使用 ref 来检查已加载数据，避免依赖 state
    const shouldLoad = forceReload || !loadedDataRef.current.has(dataType)
    if (!shouldLoad) return
    
    try {
      setLoadingStates(prev => ({ ...prev, [dataType]: true }))
      setError(null)
      
      const result: Partial<DashboardData> = {}
      
      switch (dataType) {
        case 'brandAnalysis':
          result.brandAnalysis = await fetchBrandAnalysisData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
        // 🚫 移除 tamMarketShare case，让 brand-analysis.tsx 组件自己管理
        // case 'tamMarketShare':
        //   result.tamMarketShare = await fetchTAMMarketShareData(projectId)
        //   break
        case 'productAnalysis':
          result.productAnalysis = await fetchProductAnalysisData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
        case 'pricingAnalysis':
          result.pricingAnalysis = await fetchPricingAnalysisData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
        case 'marketInsights':
          result.marketInsights = await fetchMarketInsightsData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
        case 'packagePreference':
          result.packagePreference = await fetchPackagePreferenceData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
        case 'reviewInsights':
          result.reviewInsights = await fetchReviewInsightsData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break

        case 'allReviewData':
          const reviewData = await fetchAllReviewData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          result.allReviewData = reviewData.allReviewData
          break
        case 'salesTrend':
          result.salesTrend = await fetchSalesTrendData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
      }
      
      setData(prevData => ({ ...prevData, ...result }))
      setLoadedData(prev => new Set([...prev, dataType]))
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error occurred')
    } finally {
      setLoadingStates(prev => ({ ...prev, [dataType]: false }))
    }
  }, [])

  // 项目变更回调
  /*
  const handleProjectChange = (projectId: string) => {
    console.log(`🔄 Project changed to: ${projectId}`)
    console.log(`📊 Starting data load for project: ${projectId}`)
    setSelectedProjectId(projectId)
    // 清空之前的数据和状态
    setData({})
    setLoadedData(new Set())
    setLoadingStates({
      brandAnalysis: false,
      productAnalysis: false,
      pricingAnalysis: false,
      marketInsights: false,
      packagePreference: false,
      reviewInsights: false,
      competitorAnalysis: false,
      allReviewData: false,
      salesTrend: false
    })
    // 预加载所有 chart card 数据（移除allReviewData预载）
    console.log(`🚀 Preloading chart data for new project...`)
    loadSpecificData('brandAnalysis', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('marketInsights', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('packagePreference', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('salesTrend', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('pricingAnalysis', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificDadata('productAnalysis', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('reviewInsights', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('competitorAnalysis', projectId, undefined, undefined, undefined, undefined, false)
  }
  */



  // Tab切换处理函数
  const handleTabChange = (tabValue: string) => {
    if (!selectedProjectId) return
    
    // 🔑 更新当前活跃tab状态
    setCurrentActiveTab(tabValue)
    
    // 🔑 传递当前的filters到loadSpecificData
    const categoryFilters = currentFilters.categories.length > 0 ? currentFilters.categories : undefined
    const brandFilters = ('brands' in currentFilters) ? currentFilters.brands : undefined
    const segmentFilters = ('segments' in currentFilters) ? currentFilters.segments : undefined
    const extendFields = ('extend_fields' in currentFilters) ? currentFilters.extend_fields : undefined
    // Tab切换时不强制重新加载，让缓存机制决定是否需要加载
    const forceReload = false
    
    switch (tabValue) {
      case 'brand-analysis':
        loadSpecificData('brandAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        // 同时加载marketInsights、packagePreference和salesTrend数据以在Market Analysis中显示
        loadSpecificData('marketInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        loadSpecificData('packagePreference', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        loadSpecificData('salesTrend', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
      case 'product-analysis':
        loadSpecificData('productAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
      case 'pricing-analysis':
        loadSpecificData('pricingAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        // 同时加载productAnalysis数据以支持散点图
        loadSpecificData('productAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
      case 'market-insights':
        loadSpecificData('marketInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
      case 'package-preference':
        loadSpecificData('packagePreference', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
      case 'review-insights':
        loadSpecificData('reviewInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        // 同时加载原始评论数据，因为ReviewInsights组件需要allReviewData
        loadSpecificData('allReviewData', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
      case 'competitor-analysis':
        // loadSpecificData('competitorAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        // 同时加载原始评论数据，因为CustomerSentimentScatter组件需要allReviewData
        // loadSpecificData('allReviewData', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
    }
  }

  // Initialization effect - fetches project defaults and sets up initial state
  useEffect(() => {
    const initializeDashboard = async (projectId: string) => {
      setSelectedProjectId(projectId);

      // 优化：不再重复调用filter defaults API，使用UnifiedFilterProvider提供的数据
      console.log(`Initializing dashboard for project: ${projectId} (using UnifiedFilterProvider data)`);

      // Use provided filters from props, otherwise use hardcoded defaults
      // UnifiedFilterProvider will handle the actual API calls
      const resolvedInitialFilters = filters || DEFAULT_FILTERS;

      console.log('Resolved initial filters:', resolvedInitialFilters);
      setCurrentFilters(resolvedInitialFilters);
    };

    if (initialProjectId) {
      initializeDashboard(initialProjectId);
    } else {
      console.log('🏠 Dashboard initialized, waiting for project selection...');
    }
  }, [initialProjectId, filters]);

  // Data loading effect - runs when project or filters change
  useEffect(() => {
    if (selectedProjectId) {
      console.log(`🔄 Data loading triggered for project ${selectedProjectId} with filters:`, currentFilters);
      
      // Reset data to show loading state and prevent showing stale data
      setLoadedData(new Set());
      setData({});
      
      const categoryFilters = currentFilters.categories.length > 0 ? currentFilters.categories : undefined;
      const brandFilters = currentFilters.brands?.length ? currentFilters.brands : undefined;
      const segmentFilters = currentFilters.segments?.length ? currentFilters.segments : undefined;
      const extendFields = currentFilters.extend_fields;

      // Reload all data with the new filters
      const forceReload = true;
      loadSpecificData('brandAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);
      // 🚫 移除 tamMarketShare 的加载，让 brand-analysis.tsx 组件自己管理
      // loadSpecificData('tamMarketShare', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);
      loadSpecificData('marketInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);
      loadSpecificData('packagePreference', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);
      loadSpecificData('salesTrend', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);
      loadSpecificData('pricingAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);
      loadSpecificData('productAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);
      loadSpecificData('reviewInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload);

    }
  }, [selectedProjectId, currentFilters, loadSpecificData]);


  // 监听外部传入的activeTab变化
  useEffect(() => {
    if (externalActiveTab && externalActiveTab !== currentActiveTab) {
      setCurrentActiveTab(externalActiveTab)
      handleTabChange(externalActiveTab)
    }
  }, [externalActiveTab, currentActiveTab])

  // 根据activeTab决定主tab和子tab
  const getMainTabFromActiveTab = (activeTab: string): string => {
    if (['brand-analysis', 'product-analysis', 'pricing-analysis', 'market-insights', 'package-preference'].includes(activeTab)) {
      return 'market-analysis'
    } else if (activeTab === 'review-insights') {
      return 'review-insights'
    } else if (activeTab === 'competitor-analysis') {
      return 'competitor-analysis'
    }
    return 'market-analysis' // 默认
  }

  const mainTabValue = getMainTabFromActiveTab(currentActiveTab)
  const subTabValue = ['brand-analysis', 'product-analysis', 'pricing-analysis', 'market-insights', 'package-preference'].includes(currentActiveTab) 
    ? currentActiveTab 
    : 'brand-analysis'

  if (loading) {
    return (
      <div className="p-6">
        <div className="w-full h-2 bg-blue-200 rounded-full mb-4">
          <div className="h-2 bg-blue-600 rounded-full animate-pulse" style={{ width: '60%' }}></div>
        </div>
        <div className="text-center text-gray-600">Loading analysis data from database (DB Version)...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6">
        <div className="w-full h-2 bg-red-200 rounded-full mb-4">
          <div className="h-2 bg-red-600 rounded-full" style={{ width: '100%' }}></div>
        </div>
        <div className="text-center text-red-600">
          Error loading data (DB Version): {error}
        </div>
      </div>
    )
  }

  // Show loading state when no data is loaded yet
  if (!data) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 数据库版本标识 */}
          <PageDivider />
          
          <div className="flex-1 overflow-auto">
            <div className="p-6">
              {selectedProjectId && (
                <ProjectFilterWrapper
                  projectId={selectedProjectId}
                  initialFilters={DEFAULT_FILTERS}
                  onFiltersChange={(filters) => {
                    // 暂时保留空处理器，因为这个页面可能需要重构
                    console.log('Filters changed:', filters)
                  }}
                />
              )}
              
              <div className="mt-12 text-center">
                <div className="w-full h-2 bg-blue-200 rounded-full mb-4 mx-auto max-w-md">
                  <div className="h-2 bg-blue-600 rounded-full animate-pulse" style={{ width: '60%' }}></div>
                </div>
                <div className="text-gray-600 text-lg">
                  Loading analysis data...
                </div>
                <div className="text-gray-400 text-sm mt-2">
                  Preparing your dashboard
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  // 构建产品列表用于面板显示
  const productLists = {
    byBrand: {} as Record<string, Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>>,
    bySegment: {} as Record<string, Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>>,
    byPackageSize: {} as Record<string, Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>>
  }

  // 从产品分析数据构建产品列表
  if (data.productAnalysis?.priceVsRevenue) {
    data.productAnalysis.priceVsRevenue.forEach(categoryData => {
      categoryData.products.forEach(product => {
        // 按品牌分组
        if (!productLists.byBrand[product.brand]) {
          productLists.byBrand[product.brand] = []
        }
        productLists.byBrand[product.brand].push(product)

        // 按类别分组（作为segment的替代）
        if (!productLists.bySegment[categoryData.category]) {
          productLists.bySegment[categoryData.category] = []
        }
        productLists.bySegment[categoryData.category].push(product)
      })
    })
  }

  // 从Package Preference数据构建按包装尺寸分组的产品列表
  if (data.packagePreference?.sameProductComparison) {
    // 创建产品名称到产品对象的映射
    const productMap = new Map<string, {
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>()
    if (data.productAnalysis?.priceVsRevenue) {
      data.productAnalysis.priceVsRevenue.forEach(categoryData => {
        categoryData.products.forEach(product => {
          productMap.set(product.name, product)
        })
      })
    }

    // 使用Package Preference数据来构建按包装尺寸分组的产品列表
    data.packagePreference.sameProductComparison.forEach(item => {
      const product = productMap.get(item.productName)
      if (product) {
        const packSize = item.packSize
        if (!productLists.byPackageSize[packSize]) {
          productLists.byPackageSize[packSize] = []
        }
        productLists.byPackageSize[packSize].push(product)
      }
    })
  }

  // 补充方案：如果sameProductComparison为空，直接从segmentDistributions和产品数据构建
  if (data.packagePreference?.segmentDistributions && Object.keys(productLists.byPackageSize).length === 0) {
    // 遍历所有segment的包装分布数据
    Object.values(data.packagePreference.segmentDistributions).forEach(distributions => {
      distributions.forEach(distItem => {
        const packSize = distItem.packSize
        if (!productLists.byPackageSize[packSize]) {
          productLists.byPackageSize[packSize] = []
        }
        
        // 从所有产品中找到匹配的包装尺寸
        if (data.productAnalysis?.priceVsRevenue) {
          data.productAnalysis.priceVsRevenue.forEach(categoryData => {
            categoryData.products.forEach(product => {
              // 简单的包装匹配逻辑 - 可以根据实际产品数据调整
              const productPackSize = product.name.toLowerCase().includes('pack') ? 
                (product.name.match(/(\d+).*pack/i)?.[1] || '1') : '1'
              
              if (productPackSize === packSize || 
                  (packSize === 'Single' && productPackSize === '1') ||
                  (packSize === '1' && productPackSize === 'Single')) {
                if (!productLists.byPackageSize[packSize].some(p => p.id === product.id)) {
                  productLists.byPackageSize[packSize].push(product)
                }
              }
            })
          })
        }
      })
    })
  }

  return (
    <ProductPanelProvider>
      <ReviewPanelProvider>
        <div className="h-full flex flex-col bg-gray-50">
          {/* 数据库版本标识 */}
          <PageDivider />
          
          <div className="flex-1 overflow-y-auto">
            <div className="p-6 pt-0">
                <Tabs value={mainTabValue} className="mt-6" onValueChange={(value) => handleTabChange(value)}>
                  {/* 隐藏主要的Tab导航 */}
                  {/* <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="market-analysis">Market Analysis</TabsTrigger>
                    <TabsTrigger value="review-insights">Review Insights</TabsTrigger>
                    <TabsTrigger value="competitor-analysis">Competitor Analysis</TabsTrigger>
                  </TabsList> */}

                  <TabsContent value="market-analysis" className="mt-6">
                    <Tabs value={subTabValue} className="w-full" onValueChange={(value) => handleTabChange(value)}>
                      {/* 隐藏次级Tab导航 */}
                      {/* <TabsList className="grid w-full grid-cols-5">
                        <TabsTrigger value="brand-analysis">Brand Analysis</TabsTrigger>
                        <TabsTrigger value="product-analysis">Product Analysis</TabsTrigger>
                        <TabsTrigger value="pricing-analysis">Pricing Analysis</TabsTrigger>
                        <TabsTrigger value="market-insights">Market Insights</TabsTrigger>
                        <TabsTrigger value="package-preference">Package Preference</TabsTrigger>
                      </TabsList> */}

                      <TabsContent value="brand-analysis">
                        {data.brandAnalysis ? (
                          <BrandAnalysis
                            data={data.brandAnalysis}
                            tamMarketShare={undefined}
                            productLists={productLists}
                            projectId={selectedProjectId || undefined}
                            initialFilters={currentFilters}
                            marketInsights={data.marketInsights}
                            packagePreference={data.packagePreference}
                            salesTrend={data.salesTrend}
                          />
                        ) : loadingStates.brandAnalysis ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2">Loading Market Analysis Data...</span>
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            Click to load Market Analysis data
                          </div>
                        )}
                      </TabsContent>
                      
                      <TabsContent value="pricing-analysis">
                        {data.pricingAnalysis ? (
                          <PricingAnalysis
                            projectId={selectedProjectId || undefined}
                            initialFilters={currentFilters}
                          />
                        ) : loadingStates.pricingAnalysis ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2">Loading Pricing Analysis Data...</span>
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            Click to load Pricing Analysis data
                          </div>
                        )}
                      </TabsContent>
                       
                      
                       
                    </Tabs>
                  </TabsContent>

                  <TabsContent value="review-insights">
                    {data.reviewInsights && data.allReviewData ? (
                      <ReviewInsights 
                        data={data as DashboardData} 
                        projectId={selectedProjectId || undefined}
                        initialFilters={currentFilters}
                      />
                    ) : (loadingStates.reviewInsights || loadingStates.allReviewData) ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span className="ml-2">
                          Loading Review Insights{loadingStates.allReviewData ? ' and Review Data' : ''}...
                        </span>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        Click to load Review Insights data
                      </div>
                    )}
                  </TabsContent>

                  <TabsContent value="competitor-analysis">
                    <CompetitorAnalysis projectId={selectedProjectId} data={data as DashboardData} initialFilters={currentFilters} />
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          
          <ProductPanel />
          <ReviewPanel />
        </div>
      </ReviewPanelProvider>
    </ProductPanelProvider>
  )
}

// 🆕 主要导出组件：用Provider包装
export function AnalysisDbContainer(props: AnalysisDbContainerProps) {
  // 🆕 移除重复的 UnifiedFilterProvider，直接使用上层的 Provider
  return <AnalysisDbContent {...props} />
}
