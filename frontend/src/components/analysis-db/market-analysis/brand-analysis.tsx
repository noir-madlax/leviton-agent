"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart } from "@/components/analysis-db/charts/bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
// 导入需要集成的组件
import { MarketInsights } from './market-insights'
import { PackagePreferenceAnalysis } from './package-preference-analysis'
// 导入 Sales Trend 组件
import { SalesTrendChart, SalesTrendSummary } from '@/app/chat/charts/sales_trend'
import { SALES_TREND_DATE_RANGE } from '@/app/chat/charts/sales_trend/services/sales-trend-api'
// import { useSalesTrendData } from '@/app/chat/charts/sales_trend/hooks/use-sales-trend-data'

interface BrandAnalysisProps {
  data: {
    brandCategoryRevenue: {
      brand: string
      categories: Record<string, { revenue: number; volume: number; product_count: number }>
      dimmerRevenue: number
      switchRevenue: number
      dimmerVolume: number
      switchVolume: number
    }[]
    categoryNames: string[]
    categoryColors: string[]
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

  if (!salesTrendData || !salesTrendData.trend_data || salesTrendData.trend_data.length === 0) {
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
        data={salesTrendData} 
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
        data={salesTrendData}
      />
    </div>
  )
}

export function BrandAnalysis({ data: initialData, productLists, projectId, initialFilters, marketInsights, packagePreference, salesTrend }: BrandAnalysisProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
  const [data] = useState(initialData)
  const { openPanel, loading } = useProductPanel()

  // 获取category信息
  const categoryNames = data.categoryNames || []
  const categoryColors = data.categoryColors || ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
  
  // 如果没有数据，显示空状态
  if (!categoryNames.length || !data.brandCategoryRevenue.length) {
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
  const chartData = data.brandCategoryRevenue
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
    // Handler for sales trend chart clicks
    console.log('Sales trend area clicked:', data)
  }

  // 处理饼图数据
  const processCategoryPieData = () => {
    return categoryNames.map(category => {
      const brandShares = data.brandCategoryRevenue
        .map(item => {
          const categoryData = item.categories[category] || { revenue: 0, volume: 0, product_count: 0 }
          return {
            brand: item.brand,
            revenue: categoryData.revenue,
            productCount: categoryData.product_count // 使用实际的产品数量（ASIN count）
          }
        })
        .filter(item => item.revenue > 0)
      
      const totalRevenue = brandShares.reduce((sum, item) => sum + item.revenue, 0)
      const totalProducts = brandShares.reduce((sum, item) => sum + item.productCount, 0)
      
      return {
        category,
        totalRevenue,
        totalProducts,
        brandShares: brandShares.map(item => ({
          ...item,
          name: item.brand, // 添加name属性，值为brand名称，这样Legend可以正确显示
          marketShare: totalRevenue > 0 ? (item.revenue / totalRevenue) * 100 : 0
        })).sort((a, b) => b.revenue - a.revenue)
      }
    }).filter(item => item.totalRevenue > 0)
  }

  // 自定义饼图标签
  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, marketShare }: {
    cx: number; cy: number; midAngle: number; innerRadius: number; outerRadius: number; marketShare: number;
  }) => {
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    // 只有当市场份额大于5%时才显示标签
    if (marketShare < 5) return null

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="bold"
      >
        {`${marketShare.toFixed(1)}%`}
      </text>
    )
  }

  // 自定义Tooltip
  const CustomTooltip = ({ active, payload }: { 
    active?: boolean; 
    payload?: Array<{
      payload: {
        brand: string;
        revenue: number;
        marketShare: number;
        productCount: number;
      }
    }> 
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-gray-50 p-3  ">
          <p className="font-medium">{`Brand: ${data.brand}`}</p>
          <p className="text-blue-600">{`Revenue: $${data.revenue.toLocaleString()}`}</p>
          <p className="text-green-600">{`Total number of products: ${data.productCount}`}</p>
          <p className="text-gray-600">{`Market Share: ${data.marketShare.toFixed(1)}%`}</p>
        </div>
      )
    }
    return null
  }

  const categoryPieData = processCategoryPieData()
  const pieColors = Array.from({ length: 20 }, (_, i) => getChartColor(i))

  // 计算总的市场数据
  const totalMarketRevenue = categoryPieData.reduce((sum, category) => sum + category.totalRevenue, 0)
  const totalMarketProducts = categoryPieData.reduce((sum, category) => sum + category.totalProducts, 0)

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">🏢 Market Analysis</h2>

      {/* Market Share Pie Charts - 按照正确的三层结构重新组织 */}
      <div className="mt-5">
 
        {/* 第一层：ChartWithFilters包装整个Market Share section */}
        <div data-chart-id="market-share-analysis">
        <ChartWithFilters
          chartId="market-share-analysis"
          projectId={projectId || ''}
          title="Total addressable market (TAM) and Market Share by brands"
          projectFilters={initialFilters}
        >
          {/* 第二层：单一的Summary区域 */}
          <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6">
            <p className="text-sm text-blue-700">
              <strong>Total addressable market (TAM): </strong>
              ${totalMarketRevenue.toLocaleString()} with {totalMarketProducts} products
            </p>
           
            
            {/* 分类别明细 */}
            {categoryPieData.length > 0 && (
              <div className="mt-0 pt-0 ">
                {categoryPieData.map((categoryData) => (
                  <p key={categoryData.category} className="text-sm text-blue-600 mt-1">
                    <strong>{categoryData.category}:</strong> ${categoryData.totalRevenue.toLocaleString()} with {categoryData.totalProducts} products
                  </p>
                ))}
              </div>
            )}
             <p className="text-sm pt-0 text-blue-700 mt-3">
             Approximated by the total Revenue of all products in the selected categories and time period.
            </p>
          </div>
          <Card className="p-6 bg-gray-50 mb-15">
          {/* 第三层：多个饼图区域 */}
          {categoryPieData.length > 0 ? (
            <div className="space-y-8">
              {categoryPieData.map((categoryData) => (
                <div key={categoryData.category} className="bg-gray-50 p-6 mb-0 rounded-lg">
                  <h4 className="text-lg font-medium mb-0 text-center">
                    📊 {categoryData.category} - Market Share by Brand
                  </h4>
                  <div className="h-[600px]">
                    <ResponsiveContainer width="100%" height="100%">
                      <PieChart>
                        <Pie
                          data={categoryData.brandShares}
                          cx="50%"
                          cy="50%"
                          labelLine={false}
                          label={renderCustomizedLabel}
                          outerRadius={160}
                          fill="#8884d8"
                          dataKey="revenue"
                        >
                          {categoryData.brandShares.map((entry, brandIndex) => (
                            <Cell key={`cell-${brandIndex}`} fill={pieColors[brandIndex % pieColors.length]} />
                          ))}
                        </Pie>
                        <Tooltip content={<CustomTooltip />} />
                        <Legend 
                          verticalAlign="bottom" 
                          height={250}
                          wrapperStyle={{
                            paddingTop: 20,
                            maxHeight: 200,
                          }}
                          formatter={(value) => {
                            // value现在是brand名称（因为我们设置了name属性）
                            const item = categoryData.brandShares.find(d => d.brand === value)
                            return `${value} (${item?.marketShare.toFixed(1) || '0.0'}%)`
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
              <p className="text-center text-gray-500">No market share data available</p>
            </div>
          )}
          </Card>
        </ChartWithFilters>
        </div>

     
      </div>

      <div className="mt-0">
      <div data-chart-id="brand-analysis">
      <ChartWithFilters
        chartId="brand-analysis"
        projectId={projectId || ''}
        title="Top 10 Brand Revenue by Category"
        projectFilters={initialFilters}
      >
        <Card className="p-6 bg-gray-50">
          <MetricTypeSelector onChange={setMetricType} value={metricType} />
          
          {/* Single grouped bar chart */}
          <div className="bg-gray-50 p-4 rounded-lg relative">
            <div className="h-[400px]">
              <BarChart
                data={chartData}
                index="name"
                categories={categoryNames}
                colors={colors}
                yAxisLabel={yAxisLabel}
                metricType={metricType}
                onBarClick={(data) => handleBarClick(data)}
              />
            </div>
            {/* Loading overlay */}
            {loading && (
              <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10 rounded-lg">
                <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-gray-700 font-medium">Loading products...</span>
                </div>
              </div>
            )}
          </div>
        </Card>
      </ChartWithFilters>
      </div>
      </div>

      {/* Sales Trend Charts - By Category */}
      <div className="mt-15">
        <div data-chart-id="sales-trend-analysis">
          <ChartWithFilters
            chartId="sales-trend-analysis"
            chartType="area"
            projectId={projectId || ''}
            title="Sales Trend of Top 10 brands"
            projectFilters={initialFilters}
          >
            {/* Summary for all categories */}
            <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6">
              <p className="text-sm text-blue-700">
                <strong>Sales Trend Analysis:</strong> Showing top 10 brands by revenue for each category. 
                Data aggregated yearly and ranked by total revenue.
              </p>
            </div>
            
            {categoryNames.length > 0 ? (
              <div className="space-y-8">
                {categoryNames.map((category) => (
                  <SalesTrendByCategoryComponent
                    key={category}
                    category={category}
                    projectId={projectId || ''}
                    initialFilters={initialFilters}
                    metricType={metricType}
                    onAreaClick={handleSalesTrendClick}
                    salesTrendData={salesTrend}
                    loading={!salesTrend}
                  />
                ))}
              </div>
            ) : (
              <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
                <p className="text-sm text-yellow-700">
                  <strong>Sales Trend of Top 10 brands</strong> - No categories available...
                </p>
              </div>
            )}
          </ChartWithFilters>
        </div>
      </div>

      {/* Market Insights - New Addition */}
      <div className="mt-15" data-chart-id="market-insights">
        {marketInsights ? (
          <MarketInsights 
            data={marketInsights}
            productLists={productLists}
            projectId={projectId}
            initialFilters={initialFilters}
          />
        ) : (
          <div className="bg-yellow-50 border-l-4 border-yellow-400 p-4">
            <p className="text-sm text-yellow-700">
              <strong>Top 10 Segments by Revenue</strong> - Loading market insights data...
            </p>
          </div>
        )}
      </div>

      {/* Package Preference Analysis - New Addition */}
      <div className="mt-15" data-chart-id="package-preference">
        {packagePreference ? (
          <PackagePreferenceAnalysis 
            data={packagePreference}
            productLists={productLists}
            projectId={projectId}
            categoryFilters={initialFilters?.categories}
            brandFilters={initialFilters?.brands}
            segmentFilters={initialFilters?.segments}
            extendFields={initialFilters?.extend_fields}
          />
        ) : (
          <div className="bg-gray-50  p-4">
            <p className="text-sm text-yellow-700">
              <strong>Package Type Distribution by Revenue</strong> - Loading package preference data...
            </p>
          </div>
        )}
      </div>

    </section>
  )
}
