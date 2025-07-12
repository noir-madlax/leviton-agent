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
}

export function BrandAnalysis({ data, productLists }: BrandAnalysisProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
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
          <p className="text-gray-500 text-center">No brand analysis data available</p>
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
      // 过滤掉所有category都为0的品牌
      return categoryNames.some(category => {
        const value = item[category]
        return typeof value === 'number' && value > 0
      })
    })
    .sort((a, b) => {
      // 按总值排序
      const aTotal = categoryNames.reduce((sum, cat) => {
        const value = a[cat]
        return sum + (typeof value === 'number' ? value : 0)
      }, 0)
      const bTotal = categoryNames.reduce((sum, cat) => {
        const value = b[cat]
        return sum + (typeof value === 'number' ? value : 0)
      }, 0)
      return bTotal - aTotal
    })

  // 动态检测产品类型和生成标题
  const getProductTypeInfo = () => {
    const hasDimmers = categoryNames.some(cat => cat.toLowerCase().includes('dimmer'))
    const hasSwitches = categoryNames.some(cat => cat.toLowerCase().includes('switch'))
    const hasAirFryers = categoryNames.some(cat => cat.toLowerCase().includes('air fryer'))
    
    if (hasDimmers && hasSwitches) {
      return {
        type: "Switches",
        emoji: ""
      }
    } else if (hasAirFryers) {
      return {
        type: "Air Fryers", 
        emoji: "🔥 Air Fryers"
      }
    } else {
      return {
        type: "Products",
        emoji: "📊 Categories"
      }
    }
  }

  const productInfo = getProductTypeInfo()
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

      <h3 className="text-xl font-semibold mb-4">Top 10 Brand {titleSuffix} by Category</h3>
      <Card className="p-6 bg-gray-50">
        <MetricTypeSelector onChange={setMetricType} value={metricType} />
        
        {/* Category info */}
        <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-sm text-blue-700">
            <strong>Categories analyzed:</strong> {categoryNames.join(', ')} 
          </p>
        </div>

        {/* Single grouped bar chart */}
        <div className="bg-white p-4 rounded-lg border shadow-sm">
          <div className="h-[400px]">
            <BarChart
              data={chartData}
              index="name"
              categories={categoryNames}
              colors={categoryColors.slice(0, categoryNames.length)}
              yAxisLabel={yAxisLabel}
              metricType={metricType}
              onBarClick={(data) => handleBarClick(data)}
            />
          </div>
          
        
        </div>

      </Card>
    </section>
  )
}
