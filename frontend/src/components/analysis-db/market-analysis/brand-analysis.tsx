"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart } from "@/components/analysis-db/charts/bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"

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
  const segmentColors = data.segmentColors || ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
  
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
  
  // Transform data for the chart - always show all segments
  const chartData = data.brandCategoryRevenue.map((item) => {
    const chartItem: any = { name: item.brand }
    
    // 显示所有segments
    segmentNames.forEach((segment, index) => {
      const segmentData = item.segments[segment] || { revenue: 0, volume: 0 }
      const emojis = ["🔆", "💡", "🔥", "⚡", "🌟", "🎯", "📊", "💎"]
      const emoji = emojis[index % emojis.length]
      chartItem[`${emoji} ${segment}`] = metricType === "revenue" 
        ? segmentData.revenue 
        : segmentData.volume
    })
    
    return chartItem
  })

  // 动态生成categories for chart - show all segments
  const chartCategories = segmentNames.map((segment, index) => {
    const emojis = ["🔆", "💡", "🔥", "⚡", "🌟", "🎯", "📊", "💎"]
    const emoji = emojis[index % emojis.length]
    return `${emoji} ${segment}`
  })

  // 使用对应的颜色
  const chartColors = segmentColors.slice(0, chartCategories.length)

  const yAxisLabel = metricType === "revenue" ? "$ Total Revenue ($)" : "# Total Volume (Packages)"
  const titleSuffix = metricType === "revenue" ? "Revenue" : "Volume"

  // 生成标题
  const chartTitle = `Brand ${titleSuffix} by All Segments (${productType})`

  const handleBarClick = (data: any) => {
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

      <h3 className="text-xl font-semibold mb-4">{chartTitle}</h3>
      <Card className="p-6 bg-gray-50">
        <MetricTypeSelector onChange={setMetricType} value={metricType} />
        
        {/* Segment info */}
        <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-sm text-blue-700">
            <strong>Segments analyzed:</strong> {segmentNames.length} segments ({productType})
          </p>
          <p className="text-xs text-blue-600 mt-1">
            Showing all {segmentNames.length} segments across {data.brandCategoryRevenue.length} brands
          </p>
        </div>

        <div className="h-[500px]">
          <BarChart
            data={chartData}
            index="name"
            categories={chartCategories}
            colors={chartColors}
            yAxisLabel={yAxisLabel}
            xAxisLabel="Brand"
            metricType={metricType}
            onBarClick={handleBarClick}
          />
        </div>
      </Card>
    </section>
  )
}
