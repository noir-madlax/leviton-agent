"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart } from "@/components/analysis-db/charts/bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"

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
    byBrand: Record<string, any[]>
    bySegment: Record<string, any[]>
    byPackageSize: Record<string, any[]>
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
  
  // 按segment重组数据 - 为每个segment创建独立的图表数据
  const segmentChartData = segmentNames.map((segment, segmentIndex) => {
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
  }).filter(item => item.hasData) // 只保留有数据的segments

  const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : "Volume"
  const titleSuffix = metricType === "revenue" ? "Revenue" : "Volume"

  const handleBarClick = (data: any, segment: string) => {
    if (data && data.activeLabel) {
      const brand = data.activeLabel
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
        <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-sm text-blue-700">
            <strong>Segments analyzed:</strong> {segmentChartData.length} segments with data ({productType})
          </p>
          <p className="text-xs text-blue-600 mt-1">
            Each chart shows brands competing in that specific segment
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
                  onBarClick={(data) => handleBarClick(data, segmentChart.segment)}
                />
              </div>
            </div>
          ))}
        </div>

        {/* Summary */}
        <div className="mt-6 p-3 bg-gray-100 rounded">
          <p className="text-sm text-gray-700">
            <strong>Total segments with data:</strong> {segmentChartData.length} out of {segmentNames.length} segments
          </p>
        </div>
      </Card>
    </section>
  )
}
