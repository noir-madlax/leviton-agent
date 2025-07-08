"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart } from "@/components/analysis-db/charts/bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { filterValidBrandSegments } from "@/components/analysis-db/shared/segment-filter-utils"

interface BrandAnalysisProps {
  data: {
    brandCategoryRevenue: {
      brand: string
      segments: Record<string, { revenue: number; volume: number }>
      dimmerRevenue: number
      switchRevenue: number
      dimmerVolume: number
      switchVolume: number
    }[]
    segmentNames: string[]
    segmentColors: string[]
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
}

export function BrandAnalysis({ data, productLists }: BrandAnalysisProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
  const { openPanel } = useProductPanel()

  // 获取动态segment信息
  const segmentNames = data.segmentNames || []
  const segmentColors = data.segmentColors || Array.from({ length: 20 }, (_, i) => getChartColor(i))
  
  // 如果没有segment数据，使用fallback
  if (!segmentNames.length || !data.brandCategoryRevenue.length) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">🏢 Brand Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-gray-500 text-center">No brand analysis data available</p>
        </Card>
      </section>
    )
  }

  // 动态检测产品类型
  const getProductType = () => {
    const firstSegment = segmentNames[0] || ""
    if (firstSegment.toLowerCase().includes('air fryer')) return "Air Fryers"
    if (firstSegment.toLowerCase().includes('dimmer')) return "Dimmer Switches"
    if (firstSegment.toLowerCase().includes('switch')) return "Light Switches"
    return "Products"
  }

  const productType = getProductType()
  
  // 使用公共过滤函数过滤有效的segments
  const validSegmentNames = filterValidBrandSegments(segmentNames, data.brandCategoryRevenue, metricType)
  
  // 按segment重组数据 - 为每个有效segment创建独立的图表数据
  const segmentChartData = validSegmentNames.map((segment, segmentIndex) => {
    const brandsForSegment = data.brandCategoryRevenue
      .map(item => {
        const segmentData = item.segments[segment] || { revenue: 0, volume: 0 }
        const value = metricType === "revenue" ? segmentData.revenue : segmentData.volume
        return {
          name: item.brand,
          value: value
        }
      })
      .filter(item => item.value > 0) // 只保留有数据的品牌
      .sort((a, b) => b.value - a.value) // 按值排序

    const emojis = ["🔆", "💡", "🔥", "⚡", "🌟", "🎯", "📊", "💎"]
    const emoji = emojis[segmentIndex % emojis.length]
    
    return {
      segment,
      emoji,
      brands: brandsForSegment,
      color: segmentColors[segmentIndex % segmentColors.length],
      hasData: brandsForSegment.length > 0
    }
  }) // 不再需要额外过滤，因为已经使用了过滤后的segments

  const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : "Volume"
  const titleSuffix = metricType === "revenue" ? "Revenue" : "Volume"

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

      <h3 className="text-xl font-semibold mb-4">Brand {titleSuffix} by Segment ({productType})</h3>
      <Card className="p-6 bg-gray-50">
        <MetricTypeSelector onChange={setMetricType} value={metricType} />
        
        {/* Segment info */}
        <div className="mb-0 p-2 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-sm text-blue-700">
            <strong>Segments analyzed:</strong> {segmentChartData.length} segments with data ({productType})
          </p>
        </div>

        {/* Multiple charts - one per segment */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
          {segmentChartData.map((segmentChart) => (
            <div key={segmentChart.segment} className="bg-white p-3 rounded-lg border shadow-sm">
              <h4 className="text-sm font-semibold mb-2 text-center text-gray-800">
                {segmentChart.emoji} {segmentChart.segment}
              </h4>
              <p className="text-xs text-gray-600 text-center mb-2">
                {segmentChart.brands.length} brands
              </p>
              
              <div className="h-[280px]">
                <BarChart
                  data={segmentChart.brands}
                  index="name"
                  categories={["value"]}
                  colors={[segmentChart.color]}
                  yAxisLabel={yAxisLabel}
                  metricType={metricType}
                  onBarClick={(data) => handleBarClick(data)}
                />
              </div>
            </div>
          ))}
        </div>

      </Card>
    </section>
  )
}
