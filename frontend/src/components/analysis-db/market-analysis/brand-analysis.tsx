"use client"

import React, { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart } from "@/components/analysis-db/charts/bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { useChartSections } from "@/components/integrated-dashboard/hooks/use-chart-sections"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
// 导入需要集成的组件
import { SegmentSalesTrendChart } from '@/components/analysis-db/market-analysis/segment-sales-trend-chart'
import { PackageSalesTrendChart } from '@/components/analysis-db/market-analysis/package-sales-trend-chart'
// 导入新的过滤器组件
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
// 导入 Sales Trend 组件
import { SalesTrendChart, SalesTrendSummary } from '@/app/chat/charts/sales_trend'
import { SALES_TREND_DATE_RANGE } from '@/app/chat/charts/sales_trend/services/sales-trend-api'

// 🆕 导入统一的过滤器 Hook
import { useChartWithFilters } from '@/components/analysis-db/hooks/use-chart-with-filters'
import { CHART_NAMES } from '@/components/analysis-db/constants'

// 🆕 导入新的品牌销售趋势图表组件
import { BrandSalesTrendChart } from './brand-sales-trend-chart'
import { BarChart3 } from "lucide-react"

interface BrandAnalysisProps {
  data: {
    brandCategoryRevenue: {
      brand: string
      categories: Record<string, { revenue: number; volume: number; product_count: number }>

    }[]
    categoryNames: string[]
    categoryColors: string[]
  }
  tamMarketShare?: {
    tam_data: {
      total_market_revenue: number
      total_market_volume: number
      total_products: number
      currency: string
    }
    market_share_by_category: Array<{
      category: string
      total_revenue: number
      total_volume: number
      total_products: number
      brand_shares: Array<{
        brand: string
        revenue: number
        volume: number
        product_count: number
        market_share_percentage: number
        rank: number
      }>
    }>
    metadata: {
      filtered_asins_count: number
      total_categories: number
      total_brands: number
      calculation_timestamp: string
    }
  }
  // 添加新的数据字段
  marketInsights?: {
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
  }
  packagePreference?: {
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
  }
  salesTrend?: {
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

  productLists: {
    byBrand: Record<string, Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>>
    bySegment: Record<string, Array<{
      id: string
      name: string
      brand: string
      price: number
      unitPrice: number
      revenue: number
      volume: number
      url: string
    }>>
    byPackageSize: Record<string, Array<{
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
  projectId?: string
  initialFilters?: ProjectFilters
}

// Sales Trend Component for Individual Category
interface SalesTrendByCategoryProps {
  category: string
  projectId: string
  initialFilters?: ProjectFilters
  metricType: MetricType
  onAreaClick: (data: unknown) => void
  salesTrendData?: BrandAnalysisProps['salesTrend'] // Use optional chaining
  loading?: boolean
  error?: string | null
}

function SalesTrendByCategoryComponent({ 
  category, 
  projectId, 
  initialFilters, 
  metricType, 
  onAreaClick,
  salesTrendData,
  loading,
  error
}: SalesTrendByCategoryProps) {

  if (loading) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-lg font-medium mb-4 text-center">
          📈 {category} - Sales Trend of Top 10 Brands
        </h4>
        <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
          <p className="text-sm text-yellow-700">
            Loading sales trend data for {category}...
          </p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-lg font-medium mb-4 text-center">
          📈 {category} - Sales Trend of Top 10 Brands
        </h4>
        <div className="bg-red-50 border-l-4 border-red-400 p-4">
          <p className="text-sm text-red-700">
            Error loading sales trend data for {category}: {error}
          </p>
        </div>
      </div>
    )
  }

  // 从预加载的分类数据中提取当前category的数据
  const categoryData = salesTrendData?.byCategory?.[category]
  
  if (!categoryData || !categoryData.trend_data || categoryData.trend_data.length === 0) {
    return (
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-lg font-medium mb-4 text-center">
          📈 {category} - Sales Trend of Top 10 Brands
        </h4>
        <div className="bg-gray-100 p-4 rounded">
          <p className="text-sm text-gray-600 text-center">
            No sales trend data available for {category}
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-gray-50 p-6 rounded-lg">
      <h4 className="text-lg font-medium mb-4 text-center">
        📈 {category} - Sales Trend of Top 10 Brands
      </h4>
      
      {/* Sales Trend Summary */}
      <SalesTrendSummary 
        data={categoryData} 
        metricType={metricType} 
      />
      
      {/* Sales Trend Chart */}
      <SalesTrendChart
        projectId={projectId}
        filters={{
          categories: [category],
          brands: initialFilters?.brands,
          segments: initialFilters?.segments,
          extend_fields: initialFilters?.extend_fields
        }}
        metricType={metricType}
        dateRange={SALES_TREND_DATE_RANGE}
        onAreaClick={onAreaClick}
        data={categoryData}
      />
    </div>
  )
}

export function BrandAnalysis({ data: initialData, tamMarketShare: initialTamMarketShare, productLists, projectId, initialFilters, marketInsights, packagePreference, salesTrend }: BrandAnalysisProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")

  const { openPanel, loading } = useProductPanel()

  // Get chart sections configuration for conditional rendering
  const { shouldShowChart } = useChartSections('brand-analysis', projectId || '')

  // TAM图表数据状态管理 - 使用通用的hook
  const {
    data: tamMarketShare,
    loading: tamDataLoading,
    error: tamDataError,
    refreshData: refreshTamData
  } = useChartDataRefresh({
    chartId: 'tam-market-share',
    projectId: projectId || '',
    initialData: initialTamMarketShare,
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getTAMMarketShareData(projectId, CHART_NAMES.MARKET_SHARE_ANALYSIS)
    }
  })

  // 🆕 使用统一的过滤器 Hook - 大大简化代码！
  const {
    filters: tamFilters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.MARKET_SHARE_ANALYSIS,
    refreshTamData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  // 畅销品牌图表数据状态管理 - 使用通用的hook
  const {
    data: bestSellingBrandsData,
    loading: bestSellingBrandsLoading,
    error: bestSellingBrandsError,
    refreshData: refreshBestSellingBrandsData
  } = useChartDataRefresh({
    chartId: 'best-selling-brands',
    projectId: projectId || '',
    initialData: initialTamMarketShare,
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getTAMMarketShareData(projectId, CHART_NAMES.BEST_SELLING_BRANDS)
    }
  })

  // 畅销品牌过滤器状态管理
  const {
    filters: bestSellingBrandsFilters,
    filtersReady: bestSellingBrandsFiltersReady,
    handleFiltersReady: handleBestSellingBrandsFiltersReady,
    handleFiltersChange: handleBestSellingBrandsFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.BEST_SELLING_BRANDS,
    refreshBestSellingBrandsData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )


  // 获取category信息
  const categoryNames = initialData.categoryNames || []
  const categoryColors = initialData.categoryColors || ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]

  // 如果没有数据，显示空状态
  if (!categoryNames.length || !initialData.brandCategoryRevenue.length) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">🏢 Market Analysis</h2>
        <Card className="p-6 bg-gray-50">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">Loading market analysis data...</span>
            </div>
          ) : (
            <p className="text-gray-500 text-center">No market analysis data available</p>
          )}
        </Card>
      </section>
    )
  }

  // 构建grouped bar chart数据 - 限制为Top 10品牌
  const chartData = initialData.brandCategoryRevenue
    .map(item => {
      const brandData: { name: string; [key: string]: number | string } = { name: item.brand }
      
      // 为每个category添加数据
      categoryNames.forEach(category => {
        const categoryData = item.categories[category] || { revenue: 0, volume: 0 }
        const value = metricType === "revenue" ? categoryData.revenue : categoryData.volume
        brandData[category] = value
      })
      
      return brandData
    })
    .filter(item => {
      // 过滤掉所有category值都为0的品牌
      const hasData = categoryNames.some(category => {
        const value = item[category] as number
        return value > 0
      })
      return hasData
    })
    .sort((a, b) => {
      // 按总收入/总量排序
      const aTotal = categoryNames.reduce((sum, category) => sum + (a[category] as number), 0)
      const bTotal = categoryNames.reduce((sum, category) => sum + (b[category] as number), 0)
      return bTotal - aTotal
    })
    .slice(0, 10) // 🔧 FIX: 限制Bar Chart只显示前10个品牌

  // 确保颜色数组匹配categories数量
  const colors = categoryColors.slice(0, categoryNames.length)

  const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : "Volume"

  const handleBarClick = (data: unknown) => {
    if (data && typeof data === 'object' && 'activeLabel' in data) {
      const chartData = data as { activeLabel: string }
      const brand = chartData.activeLabel
      
      // 合并现有筛选条件和当前点击的品牌
      const newFilters = {
        ...initialFilters,
        brands: [brand],
      }

      openPanel({
        projectId: projectId || '',
        filters: newFilters,
        title: `${brand} Products`,
        subtitle: `All products from ${brand} matching current filters`,
        showFilters: { brand: false, category: true, priceRange: true, packSize: true }
      })
    }
  }

  const handleSalesTrendClick = (data: unknown) => {
    // TODO: 实现销售趋势图点击处理逻辑
    console.log('Sales trend area clicked:', data)
  }

  // 使用新的TAM数据
  const useTAMData = tamMarketShare && tamMarketShare.tam_data;

  // TAM数据
  const totalMarketRevenue = useTAMData ? tamMarketShare.tam_data.total_market_revenue : 0;
  const totalMarketProducts = useTAMData ? tamMarketShare.tam_data.total_products : 0;
  const categoryPieData = useTAMData ? tamMarketShare.market_share_by_category : [];

  const pieColors = Array.from({ length: 20 }, (_, i) => getChartColor(i))

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">🏢 Market Analysis</h2>


      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 mb-6">
            <BarChart3 className="w-5 h-5" />
            Total addressable market (TAM) and Market Share
          </h3>
        </div>
      </div>

    {/* 第二层：单一的Summary区域 */}
    <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6">
            {tamDataLoading ? (
              <div className="flex items-center gap-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                <p className="text-sm text-blue-700">正在更新TAM数据...</p>
              </div>
            ) : tamDataError ? (
              <div className="flex items-center gap-2">
                <p className="text-sm text-red-700">
                  <strong>数据加载失败: </strong>{tamDataError}
                </p>
                <button
                  onClick={() => refreshTamData(tamFilters)}
                  className="text-xs text-blue-600 hover:text-blue-800 underline"
                >
                  重试
                </button>
              </div>
            ) : (
              <p className="text-sm text-blue-700">
                <strong>Total addressable market (TAM): </strong>
                ${totalMarketRevenue.toLocaleString()} with {totalMarketProducts} products
              </p>
            )}
           
            
            {/* 分类别明细 - 使用新的数据结构 */}
            {categoryPieData.length > 0 && (
              <div className="mt-0 pt-0 ">
                {(categoryPieData as Array<{category: string, total_revenue: number, total_products: number, brand_shares: Array<{brand: string, revenue: number, product_count: number, market_share_percentage: number}>}>).map((categoryData) => (
                  <p key={categoryData.category} className="text-sm text-blue-600 mt-1">
                    <strong>{categoryData.category}:</strong> ${categoryData.total_revenue.toLocaleString()} with {categoryData.total_products} products
                  </p>
                ))}
              </div>
            )}
             <p className="text-sm pt-0 text-blue-700 mt-3">
             Approximated by the total Revenue of all products in the selected categories and time period.
            </p>
          </div>


      {/* Market Share Pie Charts - 按照正确的三层结构重新组织 */}
      {shouldShowChart('market-share-analysis') && (
      <div className="mt-5">

        {/* 第一层：包装整个Market Share section - 使用新的过滤器组件 */}
        <div data-chart-id="market-share-analysis">
          <Card className="p-6 bg-gray-50 rounded-xl border shadow-sm" >
            <div className="mb-0 bg-gray-50">

              {/* 🆕 简化后的过滤器组件 - 使用统一 Hook */}
              <FilterRenderer
                projectId={projectId || ''}
                chartName="market-share-analysis"
                currentFilters={tamFilters}
                onChange={handleFiltersChange}
                onFiltersReady={handleFiltersReady}
                disabled={tamDataLoading}
                className="mb-6"
              />
            </div>

          <div className="p-6 bg-gray-50 mb-6 ">
          {/* 第三层：多个饼图区域 */}
          {tamDataLoading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                <p className="text-sm text-gray-600">正在更新图表数据...</p>
              </div>
            </div>
          ) : !filtersReady ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                <p className="text-sm text-gray-600">正在更新图表数据...</p>
              </div>
            </div>
          ) : tamDataError ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <p className="text-sm text-red-600 mb-3">图表数据加载失败: {tamDataError}</p>
                <button
                  onClick={() => refreshTamData(tamFilters)}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                >
                  重新加载
                </button>
              </div>
            </div>
          ) : (
            // TAM数据渲染
            categoryPieData.length > 0 ? (
              <div className="space-y-8">
                {(categoryPieData as Array<{category: string, total_revenue: number, total_products: number, brand_shares: Array<{brand: string, revenue: number, product_count: number, market_share_percentage: number}>}>).map((categoryData) => (
                  <div key={categoryData.category} className="bg-gray-50 p-6 ">
                    <h4 className="text-lg font-medium mb-0 text-center">
                      📊 {categoryData.category} - Market Share by Brand
                    </h4>
                    <div className="h-[600px]">
                      <ResponsiveContainer width="100%" height="100%">
                        <PieChart>
                          <Pie
                            data={categoryData.brand_shares.map((brand) => ({
                              brand: brand.brand,
                              revenue: brand.revenue,
                              product_count: brand.product_count,
                              market_share_percentage: brand.market_share_percentage,
                              name: brand.brand // 为Legend组件添加name字段
                            }))}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ market_share_percentage }: { market_share_percentage: number }) =>
                              market_share_percentage >= 5 ? `${market_share_percentage.toFixed(1)}%` : null
                            }
                            outerRadius={160}
                            fill="#8884d8"
                            dataKey="revenue"
                          >
                            {categoryData.brand_shares.map((_, brandIndex: number) => (
                              <Cell key={`cell-${brandIndex}`} fill={pieColors[brandIndex % pieColors.length]} />
                            ))}
                          </Pie>
                          <Tooltip content={(props) => {
                            if (props.active && props.payload && props.payload.length) {
                              const data = props.payload[0].payload as {
                                brand: string;
                                revenue: number;
                                market_share_percentage: number;
                                product_count: number;
                              }
                              return (
                                <div className="bg-gray-50 p-3">
                                  <p className="font-medium">{`Brand: ${data.brand}`}</p>
                                  <p className="text-blue-600">{`Revenue: $${data.revenue.toLocaleString()}`}</p>
                                  <p className="text-green-600">{`Total number of products: ${data.product_count}`}</p>
                                  <p className="text-gray-600">{`Market Share: ${data.market_share_percentage.toFixed(1)}%`}</p>
                                </div>
                              )
                            }
                            return null
                          }} />
                          <Legend
                            verticalAlign="bottom"
                            height={250}
                            wrapperStyle={{
                              paddingTop: 20,
                              maxHeight: 200,
                            }}
                            formatter={(value) => {
                              const item = categoryData.brand_shares.find((d: {brand: string, market_share_percentage: number}) => d.brand === value)
                              return `${value} (${item?.market_share_percentage.toFixed(1) || '0.0'}%)`
                            }}
                          />
                        </PieChart>
                      </ResponsiveContainer>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="bg-gray-50 p-6 rounded-lg">
                <p className="text-center text-gray-500">No TAM market share data available</p>
              </div>
            )
          )}
          </div>
          </Card>
        </div>


      </div>
      )}




      {/* Best Selling Brands Chart */}
      {shouldShowChart('market-share-analysis') && (

        <div>
      <div className="space-y-4">
        <div className="flex items-center justify-between mt-6">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Top 10 Best-Selling Brands
          </h3>
        </div>
      </div>
      <div className="mt-6 bg-gray-50 ">
        <div data-chart-id="best-selling-brands">
          <Card className="p-6 bg-gray-50  border shadow-sm rounded-xl">
            <div className="mb-4">

              {/* 过滤器组件 */}
              <FilterRenderer
                projectId={projectId || ''}
                chartName="best-selling-brands"
                currentFilters={bestSellingBrandsFilters}
                onChange={handleBestSellingBrandsFiltersChange}
                onFiltersReady={handleBestSellingBrandsFiltersReady}
                disabled={bestSellingBrandsLoading}
                className="mb-6"
              />

              {/* 指标类型选择器 */}
              <MetricTypeSelector onChange={setMetricType} value={metricType} />
            </div>

            {/* 图表内容区域 */}
            <div className="p-3 bg-gray-50 mt-[-3px]">
              {bestSellingBrandsLoading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-sm text-gray-600">正在更新图表数据...</p>
                  </div>
                </div>
              ) : !bestSellingBrandsFiltersReady ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-sm text-gray-600">正在更新图表数据...</p>
                  </div>
                </div>
              ) : bestSellingBrandsError ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <p className="text-sm text-red-600 mb-3">数据加载失败: {bestSellingBrandsError}</p>
                    <button
                      onClick={() => refreshBestSellingBrandsData(bestSellingBrandsFilters)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                    >
                      重新加载
                    </button>
                  </div>
                </div>
              ) : (
                // 使用与 Top 10 Brand Revenue by Category 完全相同的渲染逻辑
                bestSellingBrandsData && bestSellingBrandsData.market_share_by_category.length > 0 ? (
                  (() => {
                    // 构建与 Top 10 Brand Revenue by Category 相同的数据结构
                    const categoryNames = bestSellingBrandsData.market_share_by_category.map(cat => cat.category)
                    const categoryColors = ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#F7B731", "#A55EEA", "#26de81", "#FD79A8", "#2ECC71", "#E74C3C"]

                    // 构建 brandCategoryRevenue 数据结构
                    const brandCategoryRevenue: any[] = []
                    const allBrands = new Set<string>()

                    // 收集所有品牌
                    bestSellingBrandsData.market_share_by_category.forEach(categoryData => {
                      categoryData.brand_shares.forEach(brand => {
                        allBrands.add(brand.brand)
                      })
                    })

                    // 为每个品牌构建数据
                    allBrands.forEach(brandName => {
                      const brandData: any = {
                        brand: brandName,
                        categories: {}
                      }

                      categoryNames.forEach(category => {
                        const categoryData = bestSellingBrandsData.market_share_by_category.find(cat => cat.category === category)
                        const brandInfo = categoryData?.brand_shares.find(brand => brand.brand === brandName)

                        brandData.categories[category] = {
                          revenue: brandInfo?.revenue || 0,
                          volume: brandInfo?.volume || 0,
                          product_count: brandInfo?.product_count || 0
                        }
                      })

                      brandCategoryRevenue.push(brandData)
                    })

                    // 构建 grouped bar chart 数据 - 与原图表完全相同的逻辑
                    const chartData = brandCategoryRevenue
                      .map(item => {
                        const brandData: { name: string; [key: string]: number | string } = { name: item.brand }

                        // 为每个category添加数据
                        categoryNames.forEach(category => {
                          const categoryData = item.categories[category] || { revenue: 0, volume: 0 }
                          const value = metricType === "revenue" ? categoryData.revenue : categoryData.volume
                          brandData[category] = value
                        })

                        return brandData
                      })
                      .filter(item => {
                        // 过滤掉所有category值都为0的品牌
                        const hasData = categoryNames.some(category => {
                          const value = item[category] as number
                          return value > 0
                        })
                        return hasData
                      })
                      .sort((a, b) => {
                        // 按总收入/总量排序
                        const aTotal = categoryNames.reduce((sum, category) => sum + (a[category] as number), 0)
                        const bTotal = categoryNames.reduce((sum, category) => sum + (b[category] as number), 0)
                        return bTotal - aTotal
                      })
                      .slice(0, 10) // 限制为前10个品牌

                    // 确保颜色数组匹配categories数量
                    const colors = categoryColors.slice(0, categoryNames.length)
                    const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : "Volume"

                    const handleBarClick = (data: unknown) => {
                      if (data && typeof data === 'object' && 'activeLabel' in data) {
                        const chartData = data as { activeLabel: string }
                        const brand = chartData.activeLabel

                        // 合并现有筛选条件和当前点击的品牌
                        const newFilters = {
                          ...initialFilters,
                          brands: [brand],
                        }

                        openPanel({
                          projectId: projectId || '',
                          filters: newFilters,
                          title: `${brand} Products`,
                          subtitle: `All products from ${brand} matching current filters`,
                          showFilters: { brand: false, category: true, priceRange: true, packSize: true }
                        })
                      }
                    }

                    return (
                      <div className="bg-gray-50 p-0 rounded-lg relative">
                        <div className="h-[400px]">
                          <BarChart
                            data={chartData}
                            index="name"
                            categories={categoryNames}
                            colors={colors}
                            yAxisLabel={yAxisLabel}
                            metricType={metricType}
                            onBarClick={handleBarClick}
                          />
                        </div>
                        {/* Loading overlay */}
                        {bestSellingBrandsLoading && (
                          <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10 rounded-lg">
                            <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
                              <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                              <span className="text-gray-700 font-medium">Loading products...</span>
                            </div>
                          </div>
                        )}
                      </div>
                    )
                  })()
                ) : (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <p className="text-center text-gray-500">No best selling brands data available</p>
                  </div>
                )
              )}
            </div>
          </Card>
        </div>
      </div></div>
      )}


      {/* 🆕 Brand Sales Trend Chart - New Addition */}
      {shouldShowChart('market-share-analysis') && (
        <div className="mt-6">
          <BrandSalesTrendChart
            projectId={projectId}
            initialFilters={initialFilters}
          />
        </div>
      )}


      {/* Segment Sales Trend Chart - New Addition */}
      {shouldShowChart('market-share-analysis') && (
      <div className="mt-6" data-chart-id="segment-analysis">
        <SegmentSalesTrendChart
          projectId={projectId}
          initialFilters={initialFilters}
        />
      </div>
      )}

      {/* Package Sales Trend Chart - New Addition */}
      {shouldShowChart('market-share-analysis') && (
      <div className="mt-6" data-chart-id="package-sales-trend">
        <PackageSalesTrendChart
          projectId={projectId}
          initialFilters={initialFilters}
        />
      </div>
      )}

    </section>
  )
}
