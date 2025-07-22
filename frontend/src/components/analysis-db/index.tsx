"use client"

import { useState, useEffect, useCallback, useMemo, useRef } from 'react'
import { Tabs, TabsContent } from '@/components/ui/tabs'
import { BrandAnalysis } from "@/components/analysis-db/market-analysis/brand-analysis"
import { ProductAnalysis } from "@/components/analysis-db/market-analysis/product-analysis"
import { PricingAnalysis } from "@/components/analysis-db/market-analysis/pricing-analysis"
import { MarketInsights } from "@/components/analysis-db/market-analysis/market-insights"
import { PackagePreferenceAnalysis } from "@/components/analysis-db/market-analysis/package-preference-analysis"
import { ReviewInsights } from "@/components/analysis-db/review-insights/review-insights"
import { CompetitorAnalysis } from "@/components/analysis-db/competitor-analysis/competitor-analysis"
import { ProductPanelProvider } from './contexts/product-panel-context'
import { ReviewPanelProvider } from './contexts/review-panel-context'
import { ProductPanel } from "@/components/analysis-db/panels/product-panel"
import { ReviewPanel } from "@/components/analysis-db/panels/review-panel"
import { databaseService, type ProductAnalysisData } from '@/components/analysis-db/data/database-service'
import { PageDivider } from '@/components/ui/page-divider'
import { ProjectFilters, DEFAULT_FILTERS } from './types/filters'
import { ProjectFilterWrapper } from '@/components/integrated-dashboard/components/project-filter-wrapper'

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
    }>
    customerLikes: Array<{
      feature: string
      category: string
      frequency: number
      satisfactionLevel: 'High' | 'Medium' | 'Low'
    }>
    allUseCases: Array<{
      useCase: string
      productAttribute: string
      satisfactionRate: number
      mentionCount: number
      positiveCount: number
      negativeCount: number
      categoryDefinition?: string
      productCount?: number
    }>
    underservedUseCases: Array<{
      useCase: string
      productAttribute: string
      gapLevel: number
      mentionCount: number
      categoryDefinition?: string
      productCount?: number
    }>
    totalUseMentions: number
  }
  competitorAnalysis: {
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
}

// 获取品牌分析数据的async函数
async function fetchBrandAnalysisData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
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

async function fetchProductAnalysisData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
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
      topProducts: [
        { category: 'Dimmer Switches', products: [] },
        { category: 'Light Switches', products: [] }
      ]
    };
  }
}

async function fetchPricingAnalysisData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
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

async function fetchMarketInsightsData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
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

async function fetchPackagePreferenceData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>, metricType?: string) {
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

async function fetchReviewInsightsData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
  try {
    if (!projectId) {
      console.log('⏳ Review Insights waiting for project selection...');
      return { painPoints: [], customerLikes: [], allUseCases: [], underservedUseCases: [] };
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
    console.log(`📈 Review Insights data received: ${data.painPoints.length} pain points, ${data.customerLikes.length} likes, ${data.allUseCases.length} all use cases, ${data.underservedUseCases.length} underserved use cases`);
    
    return data;
  } catch (error) {
    console.error('Error fetching review insights data:', error);
    return { painPoints: [], customerLikes: [], allUseCases: [], underservedUseCases: [] };
  }
}

async function fetchCompetitorAnalysisData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
  try {
    if (!projectId) {
      console.log('⏳ Competitor Analysis waiting for project selection...');
      return { 
        targetProducts: [], 
        matrixData: [], 
        productTotalReviews: {},
        useCaseData: { targetProducts: [], matrixData: [] }
      };
    }
    
    console.log(`📊 Fetching Competitor Analysis data for project: ${projectId}`);
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
    
    const data = await databaseService.getCompetitorAnalysisDataByProject(projectId, categoryFilters, undefined, brandFilters, segmentFilters, extendFields);
    console.log(`📈 Competitor Analysis data received: ${data.targetProducts.length} target products, ${data.matrixData.length} matrix items`);
    
    return data;
  } catch (error) {
    console.error('Error fetching competitor analysis data:', error);
    return {
      targetProducts: [],
      matrixData: [],
      productTotalReviews: {},
      useCaseData: { targetProducts: [], matrixData: [] }
    };
  }
}

async function fetchAllReviewData(projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>): Promise<Pick<DashboardData, 'allReviewData'>> {
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

export function AnalysisDbContainer({ selectedProjectId: initialProjectId, filters, activeTab: externalActiveTab }: AnalysisDbContainerProps) {
  const [data, setData] = useState<Partial<DashboardData>>({})
  const [loading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialProjectId || null)
  const [currentActiveTab, setCurrentActiveTab] = useState<string>('brand-analysis')
  // 使用传入的filters，提供默认值，并确保引用稳定性
  const appliedFilters = useMemo(() => filters || DEFAULT_FILTERS, [filters]);

  
  // 为每个数据部分单独管理加载状态
  const [loadingStates, setLoadingStates] = useState({
    brandAnalysis: false,
    productAnalysis: false,
    pricingAnalysis: false,
    marketInsights: false,
    packagePreference: false,
    reviewInsights: false,
    competitorAnalysis: false,
    allReviewData: false
  })

  // 跟踪已加载的数据
  const [loadedData, setLoadedData] = useState<Set<string>>(new Set())
  const loadedDataRef = useRef<Set<string>>(new Set())

  // 保持 ref 与 state 同步
  useEffect(() => {
    loadedDataRef.current = loadedData
  }, [loadedData])

  const loadSpecificData = useCallback(async (dataType: keyof typeof loadingStates, projectId?: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>, forceReload = false) => {
    if (!projectId) return
    
    // 使用 ref 来检查已加载数据，避免依赖 state
    const shouldLoad = forceReload || !loadedDataRef.current.has(dataType)
    if (!shouldLoad) return
    
    try {
      setLoadingStates(prev => ({ ...prev, [dataType]: true }))
      setError(null)
      
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const result: any = {}
      
      switch (dataType) {
        case 'brandAnalysis':
          result.brandAnalysis = await fetchBrandAnalysisData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
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
        case 'competitorAnalysis':
          result.competitorAnalysis = await fetchCompetitorAnalysisData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          break
        case 'allReviewData':
          const reviewData = await fetchAllReviewData(projectId, categoryFilters, brandFilters, segmentFilters, extendFields)
          result.allReviewData = reviewData.allReviewData
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
      allReviewData: false
    })
    // 预加载所有 chart card 数据（移除allReviewData预载）
    console.log(`🚀 Preloading chart data for new project...`)
    loadSpecificData('brandAnalysis', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('marketInsights', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('packagePreference', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('pricingAnalysis', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('productAnalysis', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('reviewInsights', projectId, undefined, undefined, undefined, undefined, false)
    loadSpecificData('competitorAnalysis', projectId, undefined, undefined, undefined, undefined, false)
  }



  // Tab切换处理函数
  const handleTabChange = (tabValue: string) => {
    if (!selectedProjectId) return
    
    // 🔑 更新当前活跃tab状态
    setCurrentActiveTab(tabValue)
    
    // 🔑 传递当前的filters到loadSpecificData
    const categoryFilters = appliedFilters.categories.length > 0 ? appliedFilters.categories : undefined
    const brandFilters = ('brands' in appliedFilters) ? appliedFilters.brands : undefined
    const segmentFilters = ('segments' in appliedFilters) ? appliedFilters.segments : undefined
    const extendFields = ('extend_fields' in appliedFilters) ? appliedFilters.extend_fields : undefined
    // 如果有filters，强制重新加载数据
    const forceReload = categoryFilters !== undefined || brandFilters !== undefined || segmentFilters !== undefined || extendFields !== undefined
    
    switch (tabValue) {
      case 'brand-analysis':
        loadSpecificData('brandAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        // 同时加载marketInsights和packagePreference数据以在Market Analysis中显示
        loadSpecificData('marketInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        loadSpecificData('packagePreference', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
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
        loadSpecificData('competitorAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        // 同时加载原始评论数据，因为CustomerSentimentScatter组件需要allReviewData
        loadSpecificData('allReviewData', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, forceReload)
        break
    }
  }

  // 初始化effect - 只在项目ID变化时执行
  useEffect(() => {
    if (initialProjectId) {
      console.log(`🏠 Dashboard initialized with project: ${initialProjectId}`);
      console.log(`🔍 Dashboard initial filters:`, appliedFilters);
      setSelectedProjectId(initialProjectId);
      
      // 🔧 FIX: 初始化时也使用传入的筛选器，而不是默认空值
      const categoryFilters = appliedFilters.categories.length > 0 ? appliedFilters.categories : undefined;
      const brandFilters = ('brands' in appliedFilters) ? appliedFilters.brands : undefined;
      const segmentFilters = ('segments' in appliedFilters) ? appliedFilters.segments : undefined;
      const extendFields = ('extend_fields' in appliedFilters) ? appliedFilters.extend_fields : undefined;
      
      console.log(`🚀 Loading initial brand analysis with filters:`, { categoryFilters, brandFilters, segmentFilters, extendFields });
      // 预加载 Market Analysis 数据 (保持优先级)
      loadSpecificData('brandAnalysis', initialProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, false);
      loadSpecificData('marketInsights', initialProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, false);
      loadSpecificData('packagePreference', initialProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, false);
      
      // 预加载其他 Chart Card 数据（移除allReviewData预载）
      console.log(`📊 Preloading additional chart data...`);
      loadSpecificData('pricingAnalysis', initialProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, false);
      loadSpecificData('productAnalysis', initialProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, false);
      loadSpecificData('reviewInsights', initialProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, false);
      loadSpecificData('competitorAnalysis', initialProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, false);
    } else {
      console.log('🏠 Dashboard initialized, waiting for project selection...');
    }
  }, [initialProjectId, appliedFilters, loadSpecificData])

  // 监听filters变化，重新加载数据
  useEffect(() => {
    if (selectedProjectId) {
      console.log(`🔄 Filters changed:`, appliedFilters);
      // 清空已加载的数据缓存，强制重新加载
      setLoadedData(new Set());
      setData({});
      
      // 重新加载当前数据
      const categoryFilters = appliedFilters.categories.length > 0 ? appliedFilters.categories : undefined;
      const brandFilters = ('brands' in appliedFilters) ? appliedFilters.brands : undefined;
      const segmentFilters = ('segments' in appliedFilters) ? appliedFilters.segments : undefined;
      const extendFields = ('extend_fields' in appliedFilters) ? appliedFilters.extend_fields : undefined;
      
      // 重新加载所有预加载的数据（移除allReviewData重载）
      loadSpecificData('brandAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, true);
      loadSpecificData('marketInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, true);
      loadSpecificData('packagePreference', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, true);
      loadSpecificData('pricingAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, true);
      loadSpecificData('productAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, true);
      loadSpecificData('reviewInsights', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, true);
      loadSpecificData('competitorAnalysis', selectedProjectId, categoryFilters, brandFilters, segmentFilters, extendFields, true);
    }
  }, [appliedFilters, selectedProjectId, loadSpecificData])

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
                            productLists={productLists}
                            projectId={selectedProjectId || undefined}
                            initialFilters={appliedFilters}
                            marketInsights={data.marketInsights}
                            packagePreference={data.packagePreference}
                          />
                        ) : loadingStates.brandAnalysis ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2">Loading Brand Analysis...</span>
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            Click to load Brand Analysis data
                          </div>
                        )}
                      </TabsContent>
                      
                      <TabsContent value="product-analysis">
                        <ProductAnalysis />
                      </TabsContent>
                      
                      <TabsContent value="pricing-analysis">
                        {data.pricingAnalysis ? (
                          <PricingAnalysis 
                            data={{
                              ...data.pricingAnalysis,
                              // 传递productAnalysis数据给散点图使用
                              topProducts: data.productAnalysis?.topProducts,
                              segmentSummary: data.productAnalysis?.segmentSummary,
                              segmentNames: data.productAnalysis?.segmentNames
                            }}
                            projectId={selectedProjectId || undefined}
                            initialFilters={appliedFilters}
                          />
                        ) : (loadingStates.pricingAnalysis || loadingStates.productAnalysis) ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2">Loading Pricing Analysis...</span>
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            Click to load Pricing Analysis data
                          </div>
                        )}
                      </TabsContent>
                      
                      <TabsContent value="market-insights">
                        {data.marketInsights ? (
                          <MarketInsights 
                            data={data.marketInsights}
                            productLists={productLists}
                            projectId={selectedProjectId || undefined}
                            initialFilters={appliedFilters}
                          />
                        ) : loadingStates.marketInsights ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2">Loading Market Insights...</span>
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            Click to load Market Insights data
                          </div>
                        )}
                      </TabsContent>
                      
                      <TabsContent value="package-preference">
                        {data.packagePreference ? (
                          <PackagePreferenceAnalysis 
                            data={data.packagePreference}
                            productLists={productLists}
                            projectId={selectedProjectId || undefined}
                            categoryFilters={appliedFilters.categories}
                            brandFilters={appliedFilters.brands || []}
                            segmentFilters={appliedFilters.segments || []}
                            extendFields={appliedFilters.extend_fields || {}}
                          />
                        ) : loadingStates.packagePreference ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2">Loading Package Preference...</span>
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            Click to load Package Preference data
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
                        initialFilters={appliedFilters}
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
                    {data.competitorAnalysis && data.allReviewData ? (
                      <CompetitorAnalysis projectId={selectedProjectId} data={data as DashboardData} initialFilters={appliedFilters} />
                    ) : (loadingStates.competitorAnalysis || loadingStates.allReviewData) ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span className="ml-2">
                          Loading Competitor Analysis{loadingStates.allReviewData ? ' and Review Data' : ''}...
                        </span>
                      </div>
                    ) : (
                      <div className="text-center py-8 text-gray-500">
                        Click to load Competitor Analysis data
                      </div>
                    )}
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