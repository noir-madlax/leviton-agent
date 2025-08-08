"use client"

import React, { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { useChartDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { ProjectFilters } from "../types/filters"
import { BrandSalesTrendResponse } from "../data/database-service"
import { SalesTrendChart, SalesTrendSummary } from '@/app/chat/charts/sales_trend'
import { BarChart3 } from "lucide-react"
import { useChartsT } from '@/i18n/hooks'

interface BrandSalesTrendChartProps {
  data?: BrandSalesTrendResponse
  projectId?: string
  initialFilters?: ProjectFilters
}

export function BrandSalesTrendChart({ data: initialData, projectId, initialFilters }: BrandSalesTrendChartProps) {
  const chartsT = useChartsT()
  // 客户端挂载状态
  const [mounted, setMounted] = useState(false)

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
    chartId: 'brand-sales-trend',
    projectId: projectId || '',
    initialData,
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getBrandSalesTrendData(projectId)
    }
  })

  // 过滤器状态管理
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.SALES_TREND_ANALYSIS,
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  return (
    <section className="mb-6">

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            {chartsT('salesTrendTop10Brands')}
          </h3>
        </div>
      </div>

      {/* Summary Information - moved to below title */}
      {chartData && mounted && !dataLoading && !dataError && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6 mt-6">
          <p className="text-sm text-blue-700">
            <strong>{chartsT('salesTrendAnalysis')}</strong> Showing top 10 brands by revenue for each category and aggregated yearly rank by total revenue.
          </p>
        </div>
      )}

      <div className="mt-6">
        <div data-chart-id="brand-sales-trend">
          <Card className="p-6 bg-gray-50 rounded-xl border shadow-sm">
            <div className="mb-0">
              
              {/* 过滤器组件 */}
              <FilterRenderer
                projectId={projectId || ''}
                chartName={CHART_NAMES.SALES_TREND_ANALYSIS}
                currentFilters={filters}
                onChange={handleFiltersChange}
                onFiltersReady={handleFiltersReady}
                disabled={dataLoading}
                className="mb-6"
              />
            </div>

            {/* 图表内容区域 */}
            <div className="p-0 ">
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
                    {/* 按类别显示趋势图 */}
                    {chartData.categories_data && Object.keys(chartData.categories_data).length > 0 ? (
                      <div className="space-y-8">
                        {Object.entries(chartData.categories_data).map(([category, categoryData]) => (
                          <div key={category} className=" p-0 ">
                            <h4 className="text-lg font-semibold mb-4 text-center">
                              📈 {category} - {chartsT('salesTrendTopBrandsSuffix')}
                            </h4>

                            {/* 类别趋势图 */}
                            <SalesTrendChart
                              projectId={projectId || ''}
                              filters={{
                                categories: [category],
                                brands: filters?.brands,
                                segments: filters?.segments,
                                extend_fields: filters?.extend_fields
                              }}
                              metricType="revenue"
                              onAreaClick={(data: unknown) => {
                                console.log(`Clicked on ${category} trend chart:`, data)
                              }}
                              data={categoryData}
                            />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="bg-gray-100 p-4 rounded">
                        <p className="text-sm text-gray-600 text-center">
                          No category data available
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <p className="text-center text-gray-500">No sales trend data available</p>
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
