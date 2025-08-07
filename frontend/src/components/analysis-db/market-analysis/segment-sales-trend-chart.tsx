"use client"

import React, { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { useChartDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { ProjectFilters } from "../types/filters"
import { TopSegmentsByRevenueResponse } from "../data/database-service"
import { GroupedBarChart } from "@/components/analysis-db/charts/grouped-bar-chart"
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { BarChart3 } from "lucide-react"

interface SegmentSalesTrendChartProps {
  data?: TopSegmentsByRevenueResponse
  projectId?: string
  initialFilters?: ProjectFilters
}

export function SegmentSalesTrendChart({ data: initialData, projectId, initialFilters }: SegmentSalesTrendChartProps) {
  // 客户端挂载状态
  const [mounted, setMounted] = useState(false)
  const [metricType, setMetricType] = useState<MetricType>("revenue")

  useEffect(() => {
    setMounted(true)
  }, [])

  // 数据状态管理
  const {
    data: chartData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = useChartDataRefresh({
    chartId: 'segment-sales-trend',
    projectId: projectId || '',
    initialData,
    refreshFunction: async (projectId: string) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getTopSegmentsByRevenueData(projectId)
    }
  })

  // 过滤器状态管理
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.SEGMENT_ANALYSIS,
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  const { openPanel, loading: panelLoading } = useProductPanel()

  // Helper function to wrap long text
  const wrapLongText = (text: string, maxLength: number = 15) => {
    if (!text || text.length <= maxLength) return text || 'Unknown'
    const words = text.split(' ')
    if (words.length <= 1) return text
    const mid = Math.ceil(words.length / 2)
    return words.slice(0, mid).join(' ') + '\n' + words.slice(mid).join(' ')
  }

  // 构建chart数据
  const processedChartData = chartData?.data?.segments ? chartData.data.segments.map((segment, index) => ({
    name: wrapLongText(segment.segment || 'Unknown Segment'),
    originalName: segment.segment || 'Unknown Segment',
    [metricType]: segment[metricType] || 0,
    revenue: segment.revenue || 0,
    volume: segment.volume || 0,
    products: segment.products || 0,
    fill: getChartColor(index)
  })) : []

  // 为每个segment生成不同的颜色
  const chartColors = processedChartData.map((_, index) => getChartColor(index))

  const handleBarClick = (data: { activeLabel?: string }) => {
    if (data?.activeLabel) {
      // 查找原始segment名称
      const clickedDisplayName = data.activeLabel
      const matchedItem = processedChartData.find(item => item.name === clickedDisplayName)
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

  if (!mounted) {
    return null
  }

  return (
    <section className="mb-6">

       <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            Top 10 Segments by Revenue
          </h3>
        </div>
      </div>

     

      <div className="mt-6">
        <div data-chart-id="segment-sales-trend">

          <Card className="p-6 rounded-xl border shadow-sm" >
            <div className="mb-4">

              {/* 过滤器组件 */}
              <FilterRenderer
                projectId={projectId || ''}
                chartName={CHART_NAMES.SEGMENT_ANALYSIS}
                currentFilters={filters}
                onChange={handleFiltersChange}
                onFiltersReady={handleFiltersReady}
                disabled={dataLoading}
                className="mb-3"
              />
            </div>

            {/* 图表内容区域 */}
            <div className="p-3 bg-gray-50 ">
              {dataLoading ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-sm text-gray-600">正在更新图表数据...</p>
                  </div>
                </div>
              ) : !filtersReady ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                    <p className="text-sm text-gray-600">正在初始化过滤器...</p>
                  </div>
                </div>
              ) : dataError ? (
                <div className="flex items-center justify-center py-20">
                  <div className="text-center">
                    <p className="text-sm text-red-600 mb-3">数据加载失败: {dataError}</p>
                    <button
                      onClick={() => refreshData(filters)}
                      className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                    >
                      重新加载
                    </button>
                  </div>
                </div>
              ) : (
                // 图表渲染逻辑
                chartData && mounted ? (
                  <div className="space-y-6">
                    {/* 指标类型选择器 */}
                    <MetricTypeSelector onChange={setMetricType} value={metricType} />

                    {/* 图表显示 */}
                    {processedChartData.length > 0 ? (
                      <div className="bg-gray-50 p-0 ">
                        <div className="bg-gray-50 p-4 relative">
                          <div className="h-[600px] w-full">
                            <GroupedBarChart
                              data={processedChartData}
                              index="name"
                              categories={[metricType]}
                              colors={chartColors}
                              yAxisLabel={yAxisLabel}
                              metricType={metricType}
                              onBarClick={handleBarClick}
                            />
                          </div>
                          {/* Loading overlay */}
                          {panelLoading && (
                            <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10 rounded-lg">
                              <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
                                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                                <span className="text-gray-700 font-medium">Loading products...</span>
                              </div>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <div className="bg-gray-100 p-4 rounded">
                        <p className="text-sm text-gray-600 text-center">
                          No segment data available
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <p className="text-center text-gray-500">No segment sales trend data available</p>
                  </div>
                )
              )}
            </div>
          </Card>
        </div>
      </div>
    </section>
  )
}
