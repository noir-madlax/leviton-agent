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
import { ReviewPanel } from "@/components/analysis-db/panels/review-panel"
import { databaseService, type ProductAnalysisData } from "@/components/analysis-db/data/database-service"

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
async function fetchBrandAnalysisData(projectId?: string) {
  try {
    // 🔑 REQUIRE project ID for Brand Analysis - no fallback to unfiltered data
    if (!projectId) {
      console.log('⏳ Brand Analysis waiting for project selection...');
      return { brandCategoryRevenue: [], segmentNames: [], segmentColors: [] };
    }
    
    console.log(`📊 Fetching Brand Analysis data for project: ${projectId}`);
    const result = await databaseService.getBrandCategoryRevenueByProject(projectId);
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

async function fetchProductAnalysisData(projectId?: string) {
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
    const data = await databaseService.getProductAnalysisDataByProject(projectId);
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

async function fetchPricingAnalysisData(projectId?: string) {
  try {
    if (!projectId) {
      console.log('⏳ Pricing Analysis waiting for project selection...');
      return {
        priceDistribution: [],
        brandPriceDistribution: []
      };
    }
    
    console.log(`📊 Fetching Pricing Analysis data for project: ${projectId}`);
    const pricingAnalysisData = await databaseService.getPricingAnalysisDataByProject(projectId);
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

async function fetchMarketInsightsData(projectId?: string) {
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
    const marketInsightsData = await databaseService.getMarketInsightsDataByProject(projectId);
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

async function fetchPackagePreferenceData(projectId?: string) {
  try {
    if (!projectId) {
      console.log('⏳ Package Preference waiting for project selection...');
      return {
        sameProductComparison: [],
        packageDistribution: [],
        dimmerSwitches: [],
        lightSwitches: []
      };
    }
    
    console.log(`📊 Fetching Package Preference data for project: ${projectId}`);
    const packagePreferenceData = await databaseService.getPackagePreferenceDataByProject(projectId);
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

async function fetchReviewInsightsData(projectId?: string) {
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
    const reviewInsightsData = await databaseService.getReviewInsightsDataByProject(projectId);
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



async function fetchCompetitorAnalysisData(projectId?: string) {
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
    const competitorAnalysisData = await databaseService.getCompetitorAnalysisDataByProject(projectId);
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

async function fetchAllReviewData(projectId?: string): Promise<Pick<DashboardData, 'allReviewData'>> {
  try {
    if (!projectId) {
      console.log('⏳ All Review Data waiting for project selection...');
      return {
        allReviewData: {}
      };
    }
    
    console.log(`📊 Fetching All Review Data for project: ${projectId}`);
    const allReviewData = await databaseService.getAllReviewDataByProject(projectId);
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

async function fetchDatabaseData(projectId?: string): Promise<DashboardData> {
  try {
    // 🔑 Load all market analysis modules with project filtering
    const [brandAnalysisData, productAnalysisData, pricingAnalysisData, marketInsightsData, packagePreferenceData, reviewInsightsData, competitorAnalysisData, allReviewData] = await Promise.all([
      fetchBrandAnalysisData(projectId),
      fetchProductAnalysisData(projectId),
      fetchPricingAnalysisData(projectId),
      fetchMarketInsightsData(projectId),
      fetchPackagePreferenceData(projectId),
      fetchReviewInsightsData(projectId),
      fetchCompetitorAnalysisData(projectId),
      fetchAllReviewData(projectId)
    ]);

    return {
      brandAnalysis: brandAnalysisData,
      productAnalysis: productAnalysisData,
      pricingAnalysis: pricingAnalysisData,
      marketInsights: marketInsightsData,
      packagePreference: packagePreferenceData,
      reviewInsights: reviewInsightsData,
      competitorAnalysis: competitorAnalysisData,
      allReviewData: allReviewData.allReviewData
    } as DashboardData;
  } catch (error) {
    console.error('Error fetching database data:', error)
    // 返回空数据结构
    return {
      brandAnalysis: { 
        brandCategoryRevenue: [],
        segmentNames: [],
        segmentColors: []
      },
      productAnalysis: { 
        priceVsRevenue: [],
        topProducts: {
          segments: {},
          dimmerSwitches: [],
          lightSwitches: []
        },
        segmentSummary: {},
        segmentNames: [],
        segmentColors: []
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
        segmentDistributions: {},
        segmentNames: [],
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
    } as DashboardData
  }
}

interface AnalysisDbContainerProps {
  selectedProjectId?: string | null;
}

export function AnalysisDbContainer({ selectedProjectId: initialProjectId }: AnalysisDbContainerProps) {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(initialProjectId || null)

  const loadData = async (projectId?: string) => {
    try {
      setLoading(true)
      setError(null)
      console.log(`🔄 Loading dashboard data${projectId ? ` for project ${projectId}` : ' (waiting for project selection)'}`)
      
      const dashboardData = await fetchDatabaseData(projectId || undefined)
      setData(dashboardData)
      
      console.log(`✅ Dashboard data loaded successfully${projectId ? ` for project ${projectId}` : ' (empty data, waiting for project)'}`)
    } catch (err) {
      console.error('Failed to load database data:', err)
      setError('Failed to load data from database')
    } finally {
      setLoading(false)
    }
  }

  // 项目变更回调
  const handleProjectChange = (projectId: string) => {
    console.log(`🔄 Project changed to: ${projectId}`)
    console.log(`📊 Starting data load for project: ${projectId}`)
    setSelectedProjectId(projectId)
    loadData(projectId)
  }

  useEffect(() => {
    // 如果有初始项目ID，自动加载数据
    if (initialProjectId) {
      console.log(`🏠 Dashboard initialized with project: ${initialProjectId}`);
      setSelectedProjectId(initialProjectId);
      loadData(initialProjectId);
    } else {
      console.log('🏠 Dashboard initialized, waiting for project selection...');
      setLoading(false); // Stop loading immediately, wait for user action
    }
  }, [initialProjectId])

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

  // 🎯 NEW: Show project selection UI when no data is loaded yet
  if (!data) {
    return (
      <div className="flex h-screen bg-gray-50">
        <div className="flex-1 flex flex-col overflow-hidden">
          {/* 数据库版本标识 */}
          <div className="w-full h-1 bg-blue-600"></div>
          
          <div className="flex-1 overflow-auto">
            <div className="p-6">
              <DashboardHeader 
                onProjectChange={handleProjectChange} 
                selectedProjectId={selectedProjectId} 
              />
              
              <div className="mt-12 text-center">
                <div className="w-full h-2 bg-blue-200 rounded-full mb-4 mx-auto max-w-md">
                  <div className="h-2 bg-blue-600 rounded-full" style={{ width: '0%' }}></div>
                </div>
                <div className="text-gray-600 text-lg">
                  📋 Please select a project from the dropdown above to load analysis data
                </div>
                <div className="text-gray-400 text-sm mt-2">
                  {selectedProjectId ? 'Loading data...' : 'Waiting for project selection...'}
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
                <DashboardHeader 
                  onProjectChange={handleProjectChange} 
                  selectedProjectId={selectedProjectId} 
                />
                
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
                        <ProductAnalysis 
                          data={data.productAnalysis} 
                          productLists={productLists}
                        />
                      </TabsContent>
                      
                      <TabsContent value="pricing-analysis">
                        <PricingAnalysis 
                          data={data.pricingAnalysis}
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
          <ReviewPanel />
        </div>
      </ReviewPanelProvider>
    </ProductPanelProvider>
  )
} 