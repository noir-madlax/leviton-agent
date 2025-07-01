"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { GroupedBarChart } from "@/components/analysis-db/charts/grouped-bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"

interface SegmentData {
  segment: string
  revenue: number
  volume: number
  products: number
}

interface MarketInsightsProps {
  data: {
    segmentRevenue: {
      segments?: SegmentData[]  // 新格式：所有segments
      segmentNames?: string[]   // 新格式：segment名称列表
      dimmerSwitches: SegmentData[]  // 旧格式兼容
      lightSwitches: SegmentData[]   // 旧格式兼容
    }
  }
  productLists: {
    byBrand: Record<string, any[]>
    bySegment: Record<string, any[]>
    byPackageSize: Record<string, any[]>
  }
}

// Color palette for segments
const segmentColors = [
  "#E67E22", "#3498DB", "#9B59B6", "#2ECC71", "#F39C12", 
  "#E74C3C", "#1ABC9C", "#34495E", "#F1C40F", "#95A5A6",
  "#8E44AD", "#27AE60", "#D35400", "#2980B9", "#C0392B"
]

export function MarketInsights({ data, productLists }: MarketInsightsProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
  const { openPanel } = useProductPanel()

  // 检测是否使用新格式
  const useNewFormat = data.segmentRevenue.segments && data.segmentRevenue.segments.length > 0
  
  // 获取所有segments数据
  const allSegments = useNewFormat 
    ? data.segmentRevenue.segments 
    : [...data.segmentRevenue.dimmerSwitches, ...data.segmentRevenue.lightSwitches]
  
  // 按收入排序所有segments
  const sortedSegments = [...(allSegments || [])].sort((a, b) => b.revenue - a.revenue)

  // Helper function to wrap long text
  const wrapText = (text: string, maxLength: number = 15) => {
    if (text.length <= maxLength) return text
    
    const words = text.split(' ')
    const lines = []
    let currentLine = ''
    
    for (const word of words) {
      if ((currentLine + word).length <= maxLength) {
        currentLine += (currentLine ? ' ' : '') + word
      } else {
        if (currentLine) lines.push(currentLine)
        currentLine = word
      }
    }
    if (currentLine) lines.push(currentLine)
    
    return lines.join('\n')
  }

  // 动态检测类别名称
  const getCommonCategoryName = (segments: SegmentData[]) => {
    if (!segments || segments.length === 0) return "Category"
    
    // 找出最常见的产品类型关键词
    const keywords = segments.map(s => s.segment).join(' ').toLowerCase()
    
    if (keywords.includes('air fryer')) return "Air Fryers"
    if (keywords.includes('dimmer')) return "Dimmer Switches"
    if (keywords.includes('switch')) return "Light Switches"
    if (keywords.includes('light')) return "Lighting"
    
    // 默认使用第一个segment的主要类型
    const firstSegment = segments[0].segment
    const words = firstSegment.split(' ')
    // 取最后2-3个关键词作为类别名
    if (words.length >= 2) {
      return words.slice(-2).join(' ')
    }
    return firstSegment
  }

  // 动态获取项目类型和名称
  const projectType = useNewFormat && sortedSegments.length > 0 
    ? getCommonCategoryName(sortedSegments)
    : "Products"

  // 准备图表数据 - 显示所有segments
  const chartData = sortedSegments
    .slice(0, 10)  // 显示top 10 segments
    .map((item, index) => {
      const cleanName = item.segment
        .replace(" Switches", " Switch")
        .replace("Smart Wi-Fi Enabled", "Wi-Fi Smart")
        .replace("Smart Hub-Dependent", "Hub-Dependent Smart")
        .replace("Fan and Light Combination", "Fan+Light")
        .replace("Incandescent Compatible", "Incandescent")
        .replace("Handheld Remote Control", "Remote")
        .replace("WiFi Connected Smart", "WiFi Smart")
        .replace("Three Way Multi-Location", "3-Way Multi-Location")
        .replace("Smart Hub Dependent", "Hub-Dependent Smart")
        .replace("Multi-Function Combination", "Multi-Function")
        .replace("RF Wireless Remote Control", "RF Remote Control")
        .replace("LED Illuminated Indicator", "LED Indicator")
        .replace("Four Way Multi-Location", "4-Way Multi-Location")
        .replace("High Amperage Rocker", "High Amp Rocker")
        .replace("Switch Outlet Combination Devices", "Switch+Outlet")
        .replace("Add On Auxiliary", "Auxiliary")
        .replace("Multi-Feature Combination Control", "Multi-Feature")
        .replace("Inline Cord Control", "Inline Cord")
        .replace("Air Fryers", "")
        .replace("Air Fryer", "")
        .trim()
      
      const wrappedName = wrapText(cleanName, 12)
      
      return {
        name: wrappedName,
        originalName: item.segment,
        value: metricType === "revenue" ? item.revenue : item.volume,
        fill: segmentColors[index % segmentColors.length]
      }
    })

  // 生成top 3描述
  const topSegmentsText = sortedSegments.slice(0, 3)
    .map((segment, index) => {
      const revenue = segment.revenue / 1000000
      return `${index + 1}. ${segment.segment} ($${revenue.toFixed(1)}M)`
    })
    .join(' • ')

  // 为了兼容老组件，也准备分类数据
  const categoryA = getCommonCategoryName(data.segmentRevenue.dimmerSwitches)
  const categoryB = getCommonCategoryName(data.segmentRevenue.lightSwitches)
  
  const categoryAChartData = data.segmentRevenue.dimmerSwitches.slice(0, 5).map((item, index) => ({
    name: wrapText(item.segment.replace("Air Fryers", "").replace("Air Fryer", "").trim(), 12),
    value: metricType === "revenue" ? item.revenue : item.volume,
    fill: segmentColors[index % segmentColors.length]
  }))
  
  const categoryBChartData = data.segmentRevenue.lightSwitches.slice(0, 5).map((item, index) => ({
    name: wrapText(item.segment.replace("Air Fryers", "").replace("Air Fryer", "").trim(), 12),
    value: metricType === "revenue" ? item.revenue : item.volume,
    fill: segmentColors[(index + 5) % segmentColors.length]
  }))

  const topCategoryASegments = data.segmentRevenue.dimmerSwitches.slice(0, 3)
  const topCategoryBSegments = data.segmentRevenue.lightSwitches.slice(0, 3)

  const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : "Volume (Units)"
  const titleSuffix = metricType === "revenue" ? "Revenue" : "Volume"
  const valueFormatter = metricType === "revenue" 
    ? (value: number) => `$${value.toLocaleString()}`
    : (value: number) => `${value.toLocaleString()}`

  const handleBarClick = (clickData: any) => {
    if (clickData && clickData.activeLabel) {
      // 查找原始segment名称
      const clickedDisplayName = clickData.activeLabel
      let originalSegmentName = ''
      
      // 在chartData中查找对应的原始名称
      const matchedItem = chartData.find(item => item.name === clickedDisplayName)
      if (matchedItem) {
        originalSegmentName = matchedItem.originalName
      } else {
        // 兜底逻辑：在所有segments中查找
        for (const segment of (allSegments || [])) {
          const displayName = segment.segment
            .replace(" Switches", " Switch")
            .replace("Smart Wi-Fi Enabled", "Wi-Fi Smart")
            .replace("Smart Hub-Dependent", "Hub-Dependent Smart")
            .replace("Fan and Light Combination", "Fan+Light")
            .replace("Incandescent Compatible", "Incandescent")
            .replace("Handheld Remote Control", "Remote")
            .replace("WiFi Connected Smart", "WiFi Smart")
            .replace("Three Way Multi-Location", "3-Way Multi-Location")
            .replace("Smart Hub Dependent", "Hub-Dependent Smart")
            .replace("Multi-Function Combination", "Multi-Function")
            .replace("RF Wireless Remote Control", "RF Remote Control")
            .replace("LED Illuminated Indicator", "LED Indicator")
            .replace("Four Way Multi-Location", "4-Way Multi-Location")
            .replace("High Amperage Rocker", "High Amp Rocker")
            .replace("Switch Outlet Combination Devices", "Switch+Outlet")
            .replace("Add On Auxiliary", "Auxiliary")
            .replace("Multi-Feature Combination Control", "Multi-Feature")
            .replace("Inline Cord Control", "Inline Cord")
            .replace("Air Fryers", "")
            .replace("Air Fryer", "")
            .trim()

          if (wrapText(displayName, 12) === clickedDisplayName) {
            originalSegmentName = segment.segment
            break
          }
        }
      }

      const products = productLists.bySegment[originalSegmentName] || []
      openPanel(
        products,
        `${originalSegmentName}`,
        `Products in the ${originalSegmentName} segment`,
        { brand: true, category: false, priceRange: true, packSize: true }
      )
    }
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📊 Market Insights</h2>

      <div className="mb-4">
        <MetricTypeSelector onChange={setMetricType} value={metricType} />
      </div>

      {useNewFormat ? (
        // 新格式：显示统一的segments图表
        <Card className="p-6 bg-gray-50">
          <div className="mb-4">
            <h3 className="text-xl font-semibold mb-2 text-center">🔆 {projectType} - Top Segments by {titleSuffix}</h3>
            <div className="text-sm text-gray-600 text-center mb-2">
              {topSegmentsText}
            </div>
          </div>
          <div className="h-[590px]">
            <GroupedBarChart
              data={chartData}
              index="name"
              categories={["value"]}
              colors={chartData.map(item => item.fill)}
              yAxisLabel={yAxisLabel}
              xAxisLabel="Product Segment"
              metricType={metricType}
              onBarClick={handleBarClick}
            />
          </div>
        </Card>
      ) : (
        // 旧格式：显示分类图表
        <div className="space-y-8">
          {/* Category A Chart */}
          <Card className="p-6 bg-gray-50">
            <div className="mb-4">
              <h3 className="text-xl font-semibold mb-2 text-center">🔆 {categoryA} - Top Segments by {titleSuffix}</h3>
              <div className="text-sm text-gray-600 text-center mb-2">
                Top 3: {topCategoryASegments.map((s, i) => 
                  `${i + 1}. ${s.segment.replace(" Dimmer Switches", "").replace(" Air Fryers", "")} (${valueFormatter(metricType === "revenue" ? s.revenue : s.volume)})`
                ).join(" • ")}
              </div>
            </div>
            <div className="h-[590px]">
              <GroupedBarChart
                data={categoryAChartData}
                index="name"
                categories={["value"]}
                colors={categoryAChartData.map(item => item.fill)}
                yAxisLabel={yAxisLabel}
                xAxisLabel="Product Segment"
                metricType={metricType}
                onBarClick={handleBarClick}
              />
            </div>
          </Card>

          {/* Category B Chart - 只在有数据时显示 */}
          {data.segmentRevenue.lightSwitches.length > 0 && (
            <Card className="p-6 bg-gray-50">
              <div className="mb-4">
                <h3 className="text-xl font-semibold mb-2 text-center">💡 {categoryB} - Top Segments by {titleSuffix}</h3>
                <div className="text-sm text-gray-600 text-center mb-2">
                  Top 3: {topCategoryBSegments.map((s, i) => 
                    `${i + 1}. ${s.segment.replace(" Switches", "").replace(" Control", "").replace(" Air Fryers", "")} (${valueFormatter(metricType === "revenue" ? s.revenue : s.volume)})`
                  ).join(" • ")}
                </div>
              </div>
              <div className="h-[590px]">
                <GroupedBarChart
                  data={categoryBChartData}
                  index="name"
                  categories={["value"]}
                  colors={categoryBChartData.map(item => item.fill)}
                  yAxisLabel={yAxisLabel}
                  xAxisLabel="Product Segment"
                  metricType={metricType}
                  onBarClick={handleBarClick}
                />
              </div>
            </Card>
          )}
        </div>
      )}
    </section>
  )
}
