"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { GroupedBarChart } from "@/components/analysis-db/charts/grouped-bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"

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
  projectId?: string
  initialFilters?: ProjectFilters
}

export function MarketInsights({ data: initialData, projectId, initialFilters }: MarketInsightsProps) {
  const [metricType, setMetricType] = useState<MetricType>("revenue")
  const [data] = useState(initialData)
  const [loading] = useState(false)
  const { openPanel } = useProductPanel()



  // 检测是否使用新格式
  const useNewFormat = data.segmentRevenue?.segments && Array.isArray(data.segmentRevenue.segments) && data.segmentRevenue.segments.length > 0
  
  // 获取所有segments数据
  const allSegments = useNewFormat 
    ? data.segmentRevenue.segments 
    : [
        ...(data.segmentRevenue?.dimmerSwitches || []), 
        ...(data.segmentRevenue?.lightSwitches || [])
      ]
  
  // 确保有数据并且是数组
  const validSegments = Array.isArray(allSegments) ? allSegments : []
  
  // 按收入排序所有segments，只取前10个
  const sortedSegments = [...validSegments]
    .sort((a, b) => (b.revenue || 0) - (a.revenue || 0))
    .slice(0, 10)

  // Helper function to wrap long text
  const wrapLongText = (text: string, maxLength: number = 15) => {
    if (!text || text.length <= maxLength) return text || 'Unknown'
    const words = text.split(' ')
    if (words.length <= 1) return text
    const mid = Math.ceil(words.length / 2)
    return words.slice(0, mid).join(' ') + '\n' + words.slice(mid).join(' ')
  }

  // 构建chart数据
  const chartData = sortedSegments.map((segment, index) => ({
    name: wrapLongText(segment.segment || 'Unknown Segment'),
    originalName: segment.segment || 'Unknown Segment',
    [metricType]: segment[metricType] || 0,
    revenue: segment.revenue || 0,
    volume: segment.volume || 0,
    products: segment.products || 0,
    fill: getChartColor(index)
  }))
  
  // 为每个segment生成不同的颜色
  const chartColors = chartData.map((_, index) => getChartColor(index))
  
  // 如果没有数据，显示空状态
  if (chartData.length === 0) {
    return (
      <section className="mb-10">
      
        <Card className="p-6 bg-gray-50">
          <p className="text-center text-gray-500">No segment data available for this project.</p>
        </Card>
      </section>
    )
  }

  const handleBarClick = (data: any) => {
    if (data?.activeLabel) {
      // 查找原始segment名称
      const clickedDisplayName = data.activeLabel
      const matchedItem = chartData.find(item => item.name === clickedDisplayName)
              const segmentName = matchedItem?.originalName || clickedDisplayName
      openPanel({
        projectId: projectId || '',
        filters: { segments: [segmentName] },
        title: `${segmentName} Products`,
        subtitle: `All products in ${segmentName}`,
        showFilters: { brand: true, category: true, priceRange: true, packSize: true }
      })
    }
  }

  const yAxisLabel = metricType === "revenue" ? "Revenue ($)" : metricType === "volume" ? "Volume" : "Products"

  return (
    <section className="mb-10">
    
      
      <ChartWithFilters
        chartId="market-insights"
        chartType="bar"
        projectId={projectId || ''}
        title="Top 10 Segments by Revenue"
        projectFilters={initialFilters}
      >
        <Card className="p-6 bg-gray-50 pb-0">
          <MetricTypeSelector onChange={setMetricType} value={metricType} />

          {/* Segment Revenue Chart */}
          <div className="mb-8">
            <div className="bg-gray-50 p-4 ">
              <div className="h-[600px] w-full">
                {loading ? (
                  <div className="flex items-center justify-center h-full">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                    <span className="ml-2">Loading chart data...</span>
                  </div>
                ) : (
                  <GroupedBarChart
                    data={chartData}
                    index="name"
                    categories={[metricType]}
                    colors={chartColors}
                    yAxisLabel={yAxisLabel}
                    metricType={metricType}
                    onBarClick={handleBarClick}
                  />
                )}
              </div>
            </div>
          </div>

          {/* 统计摘要 */}
         
        </Card>
      </ChartWithFilters>
    </section>
  )
}
