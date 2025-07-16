"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart } from "@/components/analysis-db/charts/bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"

interface BrandAnalysisProps {
  data: {
    brandCategoryRevenue: {
      brand: string
      categories: Record<string, { revenue: number; volume: number }>
      dimmerRevenue: number
      switchRevenue: number
      dimmerVolume: number
      switchVolume: number
    }[]
    categoryNames: string[]
    categoryColors: string[]
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

export function BrandAnalysis({ data: initialData, productLists, projectId, initialFilters }: BrandAnalysisProps) {
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
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">🏢 Brand Analysis</h2>
        <Card className="p-6 bg-gray-50">
          {loading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">Loading...</span>
            </div>
          ) : (
            <p className="text-gray-500 text-center">No brand analysis data available</p>
          )}
        </Card>
      </section>
    )
  }

  // 构建grouped bar chart数据
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

  // 确保颜色数组匹配categories数量
  const colors = categoryColors.slice(0, categoryNames.length)



  const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : "Volume"

  const handleBarClick = (data: unknown) => {
    if (data && typeof data === 'object' && 'activeLabel' in data) {
      const chartData = data as { activeLabel: string }
      const brand = chartData.activeLabel
      const products = productLists.byBrand[brand] || []
      openPanel(
        products,
        `${brand} Products`,
        `All products from ${brand}`,
        { brand: false, category: true, priceRange: true, packSize: true }
      )
    }
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">🏢 Brand Analysis</h2>

      <ChartWithFilters
        chartId="brand-analysis"
        chartType="bar"
        projectId={projectId || ''}
        title="Top 10 Brand Revenue by Category"
        projectFilters={initialFilters}
      >
        <Card className="p-6 bg-gray-50">
          <MetricTypeSelector onChange={setMetricType} value={metricType} />
          
        
          {/* Single grouped bar chart */}
          <div className="bg-white p-4 rounded-lg border shadow-sm">
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
    </section>
  )
}
