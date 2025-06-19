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
      dimmerRevenue: number
      switchRevenue: number
      dimmerVolume: number
      switchVolume: number
    }[]
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

  // Transform data for the chart based on selected metric
  const chartData = data.brandCategoryRevenue.map((item) => ({
    name: item.brand,
    "🔆 Dimmer Switches": metricType === "revenue" ? item.dimmerRevenue : item.dimmerVolume,
    "💡 Light Switches": metricType === "revenue" ? item.switchRevenue : item.switchVolume,
  }))

  const yAxisLabel = metricType === "revenue" ? "$ Total Revenue ($)" : "# Total Volume (Packages)"
  const titleSuffix = metricType === "revenue" ? "Revenue" : "Volume"

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

      <h3 className="text-xl font-semibold mb-4">Brand {titleSuffix} by Category (🔆 Dimmers vs 💡 Switches)</h3>
      <Card className="p-6 bg-gray-50">
        <MetricTypeSelector onChange={setMetricType} value={metricType} />
        <div className="h-[500px]">
          <BarChart
            data={chartData}
            index="name"
            categories={["🔆 Dimmer Switches", "💡 Light Switches"]}
            colors={["#FF6B6B", "#4ECDC4"]}
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
