"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart } from "@/components/analysis-db/charts/bar-chart"
import { StackedAreaChart } from "@/components/analysis-db/charts/stacked-area-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
// 导入需要集成的组件
import { MarketInsights } from './market-insights'
import { PackagePreferenceAnalysis } from './package-preference-analysis'

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

export function BrandAnalysis({ data: initialData, productLists, projectId, initialFilters, marketInsights, packagePreference }: BrandAnalysisProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
  const [data] = useState(initialData)
  const [loading] = useState(false)
  const { openPanel } = useProductPanel()

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
      openPanel({
        projectId: projectId || '',
        filters: { brands: [brand] },
        title: `${brand} Products`,
        subtitle: `All products from ${brand}`,
        showFilters: { brand: false, category: true, priceRange: true, packSize: true }
      })
    }
  }

  const handleSalesTrendClick = (data: unknown) => {
    // Mock handler for sales trend chart clicks
    console.log('Sales trend area clicked:', data)
  }

  // Mock data for Sales Trend Chart
  const mockTopBrands = ['Leviton', 'Lutron', 'GE', 'Philips', 'Legrand', 'Eaton', 'Honeywell', 'Schneider', 'Hubbell', 'Pass & Seymour']
  
  const mockSalesTrendData = [
    {
      month: 'Jan 2024',
      'Leviton': metricType === 'revenue' ? 850000 : 12500,
      'Lutron': metricType === 'revenue' ? 720000 : 9800,
      'GE': metricType === 'revenue' ? 680000 : 11200,
      'Philips': metricType === 'revenue' ? 580000 : 8900,
      'Legrand': metricType === 'revenue' ? 520000 : 7800,
      'Eaton': metricType === 'revenue' ? 450000 : 7200,
      'Honeywell': metricType === 'revenue' ? 380000 : 6100,
      'Schneider': metricType === 'revenue' ? 320000 : 5400,
      'Hubbell': metricType === 'revenue' ? 280000 : 4700,
      'Pass & Seymour': metricType === 'revenue' ? 240000 : 3900,
    },
    {
      month: 'Feb 2024',
      'Leviton': metricType === 'revenue' ? 780000 : 11800,
      'Lutron': metricType === 'revenue' ? 890000 : 12100,
      'GE': metricType === 'revenue' ? 720000 : 11800,
      'Philips': metricType === 'revenue' ? 610000 : 9300,
      'Legrand': metricType === 'revenue' ? 480000 : 7200,
      'Eaton': metricType === 'revenue' ? 520000 : 8100,
      'Honeywell': metricType === 'revenue' ? 420000 : 6800,
      'Schneider': metricType === 'revenue' ? 350000 : 5900,
      'Hubbell': metricType === 'revenue' ? 290000 : 4900,
      'Pass & Seymour': metricType === 'revenue' ? 260000 : 4200,
    },
    {
      month: 'Mar 2024',
      'Leviton': metricType === 'revenue' ? 920000 : 13800,
      'Lutron': metricType === 'revenue' ? 760000 : 10300,
      'GE': metricType === 'revenue' ? 640000 : 10500,
      'Philips': metricType === 'revenue' ? 650000 : 9900,
      'Legrand': metricType === 'revenue' ? 580000 : 8700,
      'Eaton': metricType === 'revenue' ? 490000 : 7600,
      'Honeywell': metricType === 'revenue' ? 360000 : 5800,
      'Schneider': metricType === 'revenue' ? 380000 : 6400,
      'Hubbell': metricType === 'revenue' ? 310000 : 5200,
      'Pass & Seymour': metricType === 'revenue' ? 280000 : 4500,
    },
    {
      month: 'Apr 2024',
      'Leviton': metricType === 'revenue' ? 880000 : 13200,
      'Lutron': metricType === 'revenue' ? 820000 : 11100,
      'GE': metricType === 'revenue' ? 700000 : 11500,
      'Philips': metricType === 'revenue' ? 590000 : 9000,
      'Legrand': metricType === 'revenue' ? 540000 : 8100,
      'Eaton': metricType === 'revenue' ? 510000 : 7900,
      'Honeywell': metricType === 'revenue' ? 400000 : 6400,
      'Schneider': metricType === 'revenue' ? 340000 : 5700,
      'Hubbell': metricType === 'revenue' ? 300000 : 5000,
      'Pass & Seymour': metricType === 'revenue' ? 270000 : 4300,
    },
    {
      month: 'May 2024',
      'Leviton': metricType === 'revenue' ? 950000 : 14200,
      'Lutron': metricType === 'revenue' ? 780000 : 10600,
      'GE': metricType === 'revenue' ? 660000 : 10800,
      'Philips': metricType === 'revenue' ? 620000 : 9500,
      'Legrand': metricType === 'revenue' ? 560000 : 8400,
      'Eaton': metricType === 'revenue' ? 480000 : 7400,
      'Honeywell': metricType === 'revenue' ? 410000 : 6600,
      'Schneider': metricType === 'revenue' ? 360000 : 6000,
      'Hubbell': metricType === 'revenue' ? 320000 : 5300,
      'Pass & Seymour': metricType === 'revenue' ? 290000 : 4700,
    },
    {
      month: 'Jun 2024',
      'Leviton': metricType === 'revenue' ? 870000 : 13000,
      'Lutron': metricType === 'revenue' ? 840000 : 11400,
      'GE': metricType === 'revenue' ? 710000 : 11600,
      'Philips': metricType === 'revenue' ? 580000 : 8800,
      'Legrand': metricType === 'revenue' ? 520000 : 7800,
      'Eaton': metricType === 'revenue' ? 530000 : 8200,
      'Honeywell': metricType === 'revenue' ? 390000 : 6200,
      'Schneider': metricType === 'revenue' ? 370000 : 6200,
      'Hubbell': metricType === 'revenue' ? 310000 : 5100,
      'Pass & Seymour': metricType === 'revenue' ? 250000 : 4000,
    }
  ]

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
          enableDynamicData={true}  // 启用动态数据
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
              Approximated by the total Revenue of all products within this category in the current project within the selected time period
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
        enableDynamicData={true}  // 启用动态数据
      >
        <Card className="p-6 bg-gray-50">
          <MetricTypeSelector onChange={setMetricType} value={metricType} />
          
          {/* Single grouped bar chart */}
          <div className="bg-gray-50 p-4 rounded-lg  ">
            <div className="h-[400px]">
              {loading ? (
                <div className="flex items-center justify-center h-full">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-2">Loading chart data...</span>
                </div>
              ) : (
                <BarChart
                  data={chartData}
                  index="name"
                  categories={categoryNames}
                  colors={colors}
                  yAxisLabel={yAxisLabel}
                  metricType={metricType}
                  onBarClick={(data) => handleBarClick(data)}
                />
              )}
            </div>
          </div>
        </Card>
      </ChartWithFilters>
      </div>
      </div>

      {/* Sales Trend Chart - New Addition */}
      <div className="mt-15">
        <div data-chart-id="sales-trend-analysis">
        <ChartWithFilters
          chartId="sales-trend-analysis"
          chartType="area"
          projectId={projectId || ''}
          title="Sales Trend of Top 10 brands"
          projectFilters={initialFilters}
          enableDynamicData={true}  // 启用动态数据
        >
            {/* Chart Description 类似summary*/}
            <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6">
              <p className="text-sm text-blue-700">
                <strong>Chart Definition:</strong> Stacked area chart showing monthly {metricType} trends for top 10 brands. 
                Height of each colored band represents {metricType === "revenue" ? "Revenue = SKU Price × Units sold" : "Volume = Units sold"} within the selected time period. 
                Hover to display percentage of {metricType} for each brand at that time slice.
              </p>
            </div>
          <Card className="p-6 bg-gray-50">
            <MetricTypeSelector onChange={setMetricType} value={metricType} />
            
            {/* Development Status Banner */}
            <div className="bg-amber-50 border-l-4 border-amber-400 p-4 mb-6">
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="w-5 h-5 text-amber-400" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-amber-700">
                    <strong>Only placeholder in this Demo version - blocked by the sales history API</strong>
                  </p>
                  <p className="text-xs text-amber-600 mt-1">
                    This feature is under development. Sales trend data will be available once the sales history API integration is complete.
                  </p>
                </div>
              </div>
            </div>

            {/* Mock Sales Trend Chart */}
            <div className="bg-gray-50 p-4 ">
              <div className="h-[500px] w-full">
                <StackedAreaChart
                  data={mockSalesTrendData}
                  brands={mockTopBrands}
                  yAxisLabel={metricType === "revenue" ? "Revenue ($)" : "Volume (Units)"}
                  onAreaClick={handleSalesTrendClick}
                />
              </div>
            </div>

          
          </Card>
        </ChartWithFilters>
        </div>
      </div>

      {/* Market Insights - New Addition */}
      <div className="mt-15" data-chart-id="market-insights">
        <ChartWithFilters
          chartId="market-insights"
          chartType="bar"
          projectId={projectId || ''}
          title="Top 10 Segments by Revenue"
          projectFilters={initialFilters}
          enableDynamicData={true}  // 启用动态数据
        >
          <MarketInsights 
            data={marketInsights || { 
              segmentRevenue: { 
                segments: [], 
                segmentNames: [],
                dimmerSwitches: [], 
                lightSwitches: [] 
              } 
            }}  // 提供完整的默认数据结构
            productLists={productLists}
            projectId={projectId}
            initialFilters={initialFilters}
            // 动态数据将通过 cloneElement 自动传递
          />
        </ChartWithFilters>
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
