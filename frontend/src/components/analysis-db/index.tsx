"use client"

import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { DashboardHeader } from "@/components/analysis-db/shared/dashboard-header"
import { BrandAnalysis } from "@/components/analysis-db/market-analysis/brand-analysis"
import { ProductAnalysis } from "@/components/analysis-db/market-analysis/product-analysis"
import { PricingAnalysis } from "@/components/analysis-db/market-analysis/pricing-analysis"
import { MarketInsights } from "@/components/analysis-db/market-analysis/market-insights"
import { PackagePreferenceAnalysis } from "@/components/analysis-db/market-analysis/package-preference-analysis"
import { ReviewInsights } from "@/components/analysis-db/review-insights/review-insights"
import { CompetitorAnalysis } from "@/components/analysis-db/competitor-analysis/competitor-analysis"
import { ProductPanelProvider } from "@/components/analysis-db/contexts/product-panel-context"
import { ReviewPanelProvider } from "@/components/analysis-db/contexts/review-panel-context"
import { ProductPanel } from "@/components/analysis-db/panels/product-panel"
import { databaseService, type ProductAnalysisData } from "@/components/analysis-db/data/database-service"

interface DashboardData {
  brandAnalysis: {
    brandCategoryRevenue: Array<{
      brand: string
      dimmerRevenue: number
      switchRevenue: number
      dimmerVolume: number
      switchVolume: number
    }>
  }
  productAnalysis: ProductAnalysisData
  pricingAnalysis: {
    priceDistribution: Array<{
      category: string
      skuPrices: number[]
      unitPrices: number[]
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
    content: string
    sentiment: 'positive' | 'negative' | 'neutral'
    category: string
    aspect: string
  }>>
}

async function fetchDatabaseData(): Promise<DashboardData> {
  try {
    const [
      brandCategoryRevenue,
      productAnalysisData,
      pricingAnalysisData,
      marketInsightsData,
      packagePreferenceData,
      reviewInsightsData,
      competitorAnalysisData,
      allReviewData
    ] = await Promise.all([
      databaseService.getBrandCategoryRevenue(),
      databaseService.getProductAnalysisData(),
      databaseService.getPricingAnalysisData(),
      databaseService.getMarketInsightsData(),
      databaseService.getPackagePreferenceData(),
      databaseService.getReviewInsightsData(),
      databaseService.getCompetitorAnalysisData(),
      databaseService.getAllReviewData()
    ])

    return {
      brandAnalysis: {
        brandCategoryRevenue
      },
      productAnalysis: productAnalysisData,
      pricingAnalysis: pricingAnalysisData,
      marketInsights: marketInsightsData,
      packagePreference: packagePreferenceData,
      reviewInsights: reviewInsightsData,
      competitorAnalysis: competitorAnalysisData,
      allReviewData: allReviewData
    }
  } catch (error) {
    console.error('Error fetching database data:', error)
    // 返回空数据结构
    return {
      brandAnalysis: { brandCategoryRevenue: [] },
      productAnalysis: { 
        priceVsRevenue: [
          { category: 'Dimmer Switches', products: [] },
          { category: 'Light Switches', products: [] }
        ], 
        topProducts: [
          { category: 'Dimmer Switches', products: [] },
          { category: 'Light Switches', products: [] }
        ]
      },
      pricingAnalysis: {
        priceDistribution: [],
        brandPriceDistribution: []
      },
      marketInsights: {
        segmentRevenue: {
          dimmerSwitches: [],
          lightSwitches: []
        }
      },
              packagePreference: {
          sameProductComparison: [],
          packageDistribution: [],
          dimmerSwitches: [],
          lightSwitches: []
        },
        reviewInsights: {
          painPoints: [],
          customerLikes: [],
          underservedUseCases: []
        },
        competitorAnalysis: {
          targetProducts: [],
          matrixData: [],
          productTotalReviews: {},
          useCaseData: {
            targetProducts: [],
            matrixData: []
          }
        },
        allReviewData: {}
      }
  }
}

export function AnalysisDbContainer() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true)
        setError(null)
        const dashboardData = await fetchDatabaseData()
        setData(dashboardData)
      } catch (err) {
        console.error('Failed to load database data:', err)
        setError('Failed to load data from database')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

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

  if (error || !data) {
    return (
      <div className="p-6">
        <div className="w-full h-2 bg-red-200 rounded-full mb-4">
          <div className="h-2 bg-red-600 rounded-full" style={{ width: '100%' }}></div>
        </div>
        <div className="text-center text-red-600">
          Error loading data (DB Version): {error || 'Unknown error'}
        </div>
      </div>
    )
  }

  // 构建产品列表用于面板显示
  const productLists = {
    byBrand: {} as Record<string, any[]>,
    bySegment: {} as Record<string, any[]>,
    byPackageSize: {} as Record<string, any[]>
  }

  // 从产品分析数据构建产品列表
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

  return (
    <ProductPanelProvider>
      <ReviewPanelProvider>
        <div className="flex h-screen bg-gray-50">
          <div className="flex-1 flex flex-col overflow-hidden">
            {/* 数据库版本标识 */}
            <div className="w-full h-1 bg-blue-600"></div>
            
            <div className="flex-1 overflow-auto">
              <div className="p-6">
                <DashboardHeader />
                
                <Tabs defaultValue="market-analysis" className="mt-6">
                  <TabsList className="grid w-full grid-cols-3">
                    <TabsTrigger value="market-analysis">Market Analysis</TabsTrigger>
                    <TabsTrigger value="review-insights">Review Insights</TabsTrigger>
                    <TabsTrigger value="competitor-analysis">Competitor Analysis</TabsTrigger>
                  </TabsList>

                  <TabsContent value="market-analysis" className="mt-6">
                    <Tabs defaultValue="brand-analysis" className="w-full">
                      <TabsList className="grid w-full grid-cols-5">
                        <TabsTrigger value="brand-analysis">Brand Analysis</TabsTrigger>
                        <TabsTrigger value="product-analysis">Product Analysis</TabsTrigger>
                        <TabsTrigger value="pricing-analysis">Pricing Analysis</TabsTrigger>
                        <TabsTrigger value="market-insights">Market Insights</TabsTrigger>
                        <TabsTrigger value="package-preference">Package Preference</TabsTrigger>
                      </TabsList>

                      <TabsContent value="brand-analysis">
                        <BrandAnalysis 
                          data={data.brandAnalysis} 
                          productLists={productLists}
                        />
                      </TabsContent>
                      
                      <TabsContent value="product-analysis">
                        <ProductAnalysis data={data.productAnalysis} />
                      </TabsContent>
                      
                      <TabsContent value="pricing-analysis">
                        <PricingAnalysis 
                          data={data.pricingAnalysis}
                          productAnalysis={data.productAnalysis}
                          productLists={productLists}
                        />
                      </TabsContent>
                      
                      <TabsContent value="market-insights">
                        <MarketInsights 
                          data={data.marketInsights}
                          productLists={productLists}
                        />
                      </TabsContent>
                      
                      <TabsContent value="package-preference">
                        <PackagePreferenceAnalysis 
                          data={data.packagePreference}
                          productLists={productLists}
                        />
                      </TabsContent>
                    </Tabs>
                  </TabsContent>

                  <TabsContent value="review-insights">
                    <ReviewInsights data={data} />
                  </TabsContent>

                  <TabsContent value="competitor-analysis">
                    <CompetitorAnalysis data={data} />
                  </TabsContent>
                </Tabs>
              </div>
            </div>
          </div>

          <ProductPanel />
        </div>
      </ReviewPanelProvider>
    </ProductPanelProvider>
  )
} 