"use client"

import { useState, useEffect, useCallback } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DashboardHeader } from "@/components/analysis-db/shared/dashboard-header"
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

interface DashboardData {
  brandAnalysis: {
    brandCategoryRevenue: Array<{
      brand: string
      segments: Record<string, { revenue: number; volume: number }>
      dimmerRevenue: number
      switchRevenue: number
      dimmerVolume: number
      switchVolume: number
    }>
    segmentNames: string[]
    segmentColors: string[]
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
      packSize: string
      count: number
      percentage: number
      salesVolume: number
    }>
    segmentDistributions: Record<string, Array<{
      packSize: string
      count: number
      percentage: number
      salesVolume: number
      salesRevenue: number
    }>>
    segmentNames: string[]
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
    underservedUseCases: Array<{
      useCase: string
      productAttribute: string
      gapLevel: number
      mentionCount: number
      categoryDefinition?: string
      productCount?: number
    }>
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

// 🔑 NEW: Fetch data by module to avoid loading all data at once
async function fetchBrandAnalysisData(projectId?: string, categoryFilters?: string[]) {
  try {
    // 🔑 REQUIRE project ID for Brand Analysis - no fallback to unfiltered data
    if (!projectId) {
      console.log('⏳ Brand Analysis waiting for project selection...');
      return { brandCategoryRevenue: [], segmentNames: [], segmentColors: [] };
    }
    
    console.log(`📊 Fetching Brand Analysis data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    
    const result = await databaseService.getBrandCategoryRevenueByProject(projectId, categoryFilters);
    console.log(`📈 Brand Analysis data received: ${result.brandCategoryRevenue.length} brands, ${result.segmentNames.length} segments`);
    
    if (result.brandCategoryRevenue.length > 0) {
      result.brandCategoryRevenue.forEach((brand, index) => {
        console.log(`  Brand ${index + 1}: ${brand.brand} - Segments: ${Object.keys(brand.segments || {}).join(', ')}`);
      });
      console.log(`  Segments: ${result.segmentNames.join(', ')}`);
    } else {
      console.log('  ⚠️ No brand data returned from API');
    }
    
    return result;
  } catch (error) {
    console.error('Error fetching brand analysis data:', error);
    return { brandCategoryRevenue: [], segmentNames: [], segmentColors: [] };
  }
}

async function fetchProductAnalysisData(projectId?: string, categoryFilters?: string[]) {
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
    
    const data = await databaseService.getProductAnalysisDataByProject(projectId, categoryFilters);
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

async function fetchPricingAnalysisData(projectId?: string, categoryFilters?: string[]) {
  try {
    if (!projectId) {
      console.log('⏳ Pricing Analysis waiting for project selection...');
      return {
        priceDistribution: [],
        brandPriceDistribution: []
      };
    }
    
    console.log(`📊 Fetching Pricing Analysis data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    
    const pricingAnalysisData = await databaseService.getPricingAnalysisDataByProject(projectId, categoryFilters);
    console.log(`📈 Pricing Analysis data received`);
    
    return pricingAnalysisData;
  } catch (error) {
    console.error('Error fetching pricing analysis data:', error);
    return {
      priceDistribution: [],
      brandPriceDistribution: []
    };
  }
}

async function fetchMarketInsightsData(projectId?: string, categoryFilters?: string[]) {
  try {
    if (!projectId) {
      console.log('⏳ Market Insights waiting for project selection...');
      return {
        segmentRevenue: {
          dimmerSwitches: [],
          lightSwitches: []
        }
      };
    }
    
    console.log(`📊 Fetching Market Insights data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    
    const marketInsightsData = await databaseService.getMarketInsightsDataByProject(projectId, categoryFilters);
    console.log(`📈 Market Insights data received`);
    
    return marketInsightsData;
  } catch (error) {
    console.error('Error fetching market insights data:', error);
    return {
      segmentRevenue: {
        dimmerSwitches: [],
        lightSwitches: []
      }
    };
  }
}

async function fetchPackagePreferenceData(projectId?: string, categoryFilters?: string[]) {
  try {
    if (!projectId) {
      console.log('⏳ Package Preference waiting for project selection...');
      return {
        sameProductComparison: [],
        packageDistribution: [],
        segmentDistributions: {},
        segmentNames: [],
        dimmerSwitches: [],
        lightSwitches: []
      };
    }
    
    console.log(`📊 Fetching Package Preference data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    
    const packagePreferenceData = await databaseService.getPackagePreferenceDataByProject(projectId, categoryFilters);
    console.log(`📈 Package Preference data received`);
    
    return packagePreferenceData;
  } catch (error) {
    console.error('Error fetching package preference data:', error);
    return {
      sameProductComparison: [],
      packageDistribution: [],
      segmentDistributions: {},
      segmentNames: [],
      dimmerSwitches: [],
      lightSwitches: []
    };
  }
}

async function fetchReviewInsightsData(projectId?: string, categoryFilters?: string[]) {
  try {
    if (!projectId) {
      console.log('⏳ Review Insights waiting for project selection...');
      return {
        painPoints: [],
        customerLikes: [],
        underservedUseCases: []
      };
    }
    
    console.log(`📊 Fetching Review Insights data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    
    const reviewInsightsData = await databaseService.getReviewInsightsDataByProject(projectId, categoryFilters);
    console.log(`📈 Review Insights data received`);
    
    return reviewInsightsData;
  } catch (error) {
    console.error('Error fetching review insights data:', error);
    return {
      painPoints: [],
      customerLikes: [],
      underservedUseCases: []
    };
  }
}

async function fetchCompetitorAnalysisData(projectId?: string, categoryFilters?: string[]) {
  try {
    if (!projectId) {
      console.log('⏳ Competitor Analysis waiting for project selection...');
      return {
        targetProducts: [],
        matrixData: [],
        productTotalReviews: {},
        useCaseData: {
          targetProducts: [],
          matrixData: []
        }
      };
    }
    
    console.log(`📊 Fetching Competitor Analysis data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    
    const competitorAnalysisData = await databaseService.getCompetitorAnalysisDataByProject(projectId, categoryFilters);
    console.log(`📈 Competitor Analysis data received`);
    
    return competitorAnalysisData;
  } catch (error) {
    console.error('Error fetching competitor analysis data:', error);
    return {
      targetProducts: [],
      matrixData: [],
      productTotalReviews: {},
      useCaseData: {
        targetProducts: [],
        matrixData: []
      }
    };
  }
}

async function fetchAllReviewData(projectId?: string, categoryFilters?: string[]): Promise<Pick<DashboardData, 'allReviewData'>> {
  try {
    if (!projectId) {
      console.log('⏳ All Review Data waiting for project selection...');
      return {
        allReviewData: {}
      };
    }
    
    console.log(`📊 Fetching All Review Data for project: ${projectId}`);
    if (categoryFilters && categoryFilters.length > 0) {
      console.log(`🔍 Applying category filters: ${categoryFilters.join(', ')}`);
    }
    
    const allReviewData = await databaseService.getAllReviewDataByProject(projectId, categoryFilters);
    console.log(`📈 All Review Data received`);
    
    return {
      allReviewData
    };
  } catch (error) {
    console.error('Error fetching all review data:', error);
    return {
      allReviewData: {}
    };
  }
}

interface AnalysisDbContainerProps {
  selectedProjectId?: string | null;
}

export function AnalysisDbContainer({ selectedProjectId: initialProjectId }: AnalysisDbContainerProps) {
  const [data, setData] = useState<Partial<DashboardData>>({})
  const [loading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialProjectId || null)
  const [appliedFilters, setAppliedFilters] = useState<{ categories: string[]; asins: string[] }>({
    categories: [],
    asins: []
  })

  
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

  const loadSpecificData = useCallback(async (dataType: keyof typeof loadingStates, projectId?: string, categoryFilters?: string[], forceReload = false) => {
    if (!projectId || (!forceReload && loadedData.has(dataType))) return
    
    try {
      setLoadingStates(prev => ({ ...prev, [dataType]: true }))
      setError(null)
      
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const result: any = {}
      
      switch (dataType) {
        case 'brandAnalysis':
          result.brandAnalysis = await fetchBrandAnalysisData(projectId, categoryFilters)
          break
        case 'productAnalysis':
          result.productAnalysis = await fetchProductAnalysisData(projectId, categoryFilters)
          break
        case 'pricingAnalysis':
          result.pricingAnalysis = await fetchPricingAnalysisData(projectId, categoryFilters)
          break
        case 'marketInsights':
          result.marketInsights = await fetchMarketInsightsData(projectId, categoryFilters)
          break
        case 'packagePreference':
          result.packagePreference = await fetchPackagePreferenceData(projectId, categoryFilters)
          break
        case 'reviewInsights':
          result.reviewInsights = await fetchReviewInsightsData(projectId, categoryFilters)
          break
        case 'competitorAnalysis':
          result.competitorAnalysis = await fetchCompetitorAnalysisData(projectId, categoryFilters)
          break
        case 'allReviewData':
          const reviewData = await fetchAllReviewData(projectId, categoryFilters)
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
  }, [loadedData])

  // 项目变更回调
  const handleProjectChange = (projectId: string) => {
    console.log(`🔄 Project changed to: ${projectId}`)
    console.log(`📊 Starting data load for project: ${projectId}`)
    setSelectedProjectId(projectId)
    // 清空之前的数据和状态
    setData({})
    setLoadedData(new Set())
    setAppliedFilters({ categories: [], asins: [] })
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
    // 立即加载第一个tab的数据
    loadSpecificData('brandAnalysis', projectId)
  }

  // Filter变更回调 - 重新加载所有数据
  const handleFiltersChange = (filters: { categories: string[]; asins: string[] }) => {
    console.log(`🔄 Filters applied:`, filters)
    setAppliedFilters(filters)
    
    if (!selectedProjectId) return
    
    // 清空之前的数据，强制重新加载
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
    
    // 🔑 直接传递新的filters值，而不是依赖状态更新
    const categoryFilters = filters.categories.length > 0 ? filters.categories : undefined
    
    // ProjectDataOverview会通过props在appliedFilters变化时自动重新加载
    
    // 重新加载当前活跃tab的数据
    loadSpecificData('brandAnalysis', selectedProjectId, categoryFilters)
    console.log(`📊 Data reload triggered by filter change with filters:`, categoryFilters)
  }

  // Tab切换处理函数
  const handleTabChange = (tabValue: string) => {
    if (!selectedProjectId) return
    
    // 🔑 传递当前的filters到loadSpecificData
    const categoryFilters = appliedFilters.categories.length > 0 ? appliedFilters.categories : undefined
    // 如果有filters，强制重新加载数据
    const forceReload = categoryFilters !== undefined
    
    switch (tabValue) {
      case 'brand-analysis':
        loadSpecificData('brandAnalysis', selectedProjectId, categoryFilters, forceReload)
        break
      case 'product-analysis':
        loadSpecificData('productAnalysis', selectedProjectId, categoryFilters, forceReload)
        break
      case 'pricing-analysis':
        loadSpecificData('pricingAnalysis', selectedProjectId, categoryFilters, forceReload)
        break
      case 'market-insights':
        loadSpecificData('marketInsights', selectedProjectId, categoryFilters, forceReload)
        break
      case 'package-preference':
        loadSpecificData('packagePreference', selectedProjectId, categoryFilters, forceReload)
        break
      case 'review-insights':
        loadSpecificData('reviewInsights', selectedProjectId, categoryFilters, forceReload)
        // 同时加载原始评论数据，因为ReviewInsights组件需要allReviewData
        loadSpecificData('allReviewData', selectedProjectId, categoryFilters, forceReload)
        break
      case 'competitor-analysis':
        loadSpecificData('competitorAnalysis', selectedProjectId, categoryFilters, forceReload)
        break
    }
  }

  useEffect(() => {
    // 如果有初始项目ID，自动加载数据
    if (initialProjectId) {
      console.log(`🏠 Dashboard initialized with project: ${initialProjectId}`);
      setSelectedProjectId(initialProjectId);
      // 立即加载第一个tab的数据，初始化时没有filters
      loadSpecificData('brandAnalysis', initialProjectId, undefined);
    } else {
      console.log('🏠 Dashboard initialized, waiting for project selection...');
    }
  }, [initialProjectId, loadSpecificData])

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
              <DashboardHeader 
                onProjectChange={handleProjectChange} 
                selectedProjectId={selectedProjectId}
                onFiltersChange={handleFiltersChange}
              />
              
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
        // 添加包装信息到产品对象
        const productWithPackInfo = {
          ...product,
          packCount: item.packCount,
          packSize: item.packSize
        }
        productLists.byPackageSize[packSize].push(productWithPackInfo)
      }
    })
  }

  return (
    <ProductPanelProvider>
      <ReviewPanelProvider>
        <div className="flex h-screen bg-gray-50">
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* 数据库版本标识 */}
            <PageDivider />
            
            <div className="flex-1 overflow-auto">
              <div className="p-6">
                <DashboardHeader 
                  onProjectChange={handleProjectChange} 
                  selectedProjectId={selectedProjectId}
                  onFiltersChange={handleFiltersChange}
                />
                
                <Tabs defaultValue="market-analysis" className="mt-6" onValueChange={(value) => handleTabChange(value)}>
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="market-analysis">Market Analysis</TabsTrigger>
                    <TabsTrigger value="review-insights">Review Insights</TabsTrigger>
                    <TabsTrigger value="competitor-analysis">Competitor Analysis</TabsTrigger>
                  </TabsList>

                  <TabsContent value="market-analysis" className="mt-6">
                    <Tabs defaultValue="brand-analysis" className="w-full" onValueChange={(value) => handleTabChange(value)}>
                      <TabsList className="grid w-full grid-cols-5">
                        <TabsTrigger value="brand-analysis">Brand Analysis</TabsTrigger>
                        <TabsTrigger value="product-analysis">Product Analysis</TabsTrigger>
                        <TabsTrigger value="pricing-analysis">Pricing Analysis</TabsTrigger>
                        <TabsTrigger value="market-insights">Market Insights</TabsTrigger>
                        <TabsTrigger value="package-preference">Package Preference</TabsTrigger>
                      </TabsList>

                      <TabsContent value="brand-analysis">
                        {data.brandAnalysis ? (
                          <BrandAnalysis 
                            data={data.brandAnalysis} 
                            productLists={productLists}
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
                        {data.productAnalysis ? (
                          <ProductAnalysis 
                            data={data.productAnalysis} 
                            productLists={productLists}
                          />
                        ) : loadingStates.productAnalysis ? (
                          <div className="flex items-center justify-center py-8">
                            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                            <span className="ml-2">Loading Product Analysis...</span>
                          </div>
                        ) : (
                          <div className="text-center py-8 text-gray-500">
                            Click to load Product Analysis data
                          </div>
                        )}
                      </TabsContent>
                      
                      <TabsContent value="pricing-analysis">
                        {data.pricingAnalysis ? (
                          <PricingAnalysis 
                            data={data.pricingAnalysis}
                            productLists={productLists}
                          />
                        ) : loadingStates.pricingAnalysis ? (
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
                      <ReviewInsights data={data as DashboardData} />
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
                    {data.competitorAnalysis ? (
                      <CompetitorAnalysis projectId={selectedProjectId} data={data as DashboardData} />
                    ) : loadingStates.competitorAnalysis ? (
                      <div className="flex items-center justify-center py-8">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                        <span className="ml-2">Loading Competitor Analysis...</span>
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
          </div>

          <ProductPanel />
          <ReviewPanel />
        </div>
      </ReviewPanelProvider>
    </ProductPanelProvider>
  )
} 