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
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getTopSegmentsByRevenueData(projectId)
    }
  })

  // 过滤器状态管理
  const {
    filters,
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

  const handleBarClick = (data: any) => {
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
    <section className="mb-10">
      <div className="mt-5">
        <div data-chart-id="segment-sales-trend">
          <Card className="p-6">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Monthly Sales Trend of Top 10 Segments
              </h3>
              
              {/* 过滤器组件 */}
              <FilterRenderer
                projectId={projectId || ''}
                chartName={CHART_NAMES.SEGMENT_ANALYSIS}
                currentFilters={filters}
                onChange={handleFiltersChange}
                onFiltersReady={handleFiltersReady}
                disabled={dataLoading}
                className="mb-6"
              />
            </div>

            <div className="space-y-6">
              {/* 错误状态 */}
              {dataError ? (
                <div className="bg-red-50 border-l-4 border-red-400 p-4">
                  <div className="flex flex-col space-y-3">
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
                    {/* 汇总信息 */}
                    <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6">
                      <p className="text-sm text-blue-700">
                        <strong>Segment Sales Trend Analysis:</strong> Showing top 10 segments by revenue.
                        {chartData.metadata && (
                          <> Data includes {chartData.metadata.returned_segments} segments from {chartData.metadata.total_segments} total segments.</>
                        )}
                      </p>
                    </div>

                    {/* 指标类型选择器 */}
                    <MetricTypeSelector onChange={setMetricType} value={metricType} />

                    {/* 图表显示 */}
                    {processedChartData.length > 0 ? (
                      <div className="bg-white p-6 rounded-lg border">
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
