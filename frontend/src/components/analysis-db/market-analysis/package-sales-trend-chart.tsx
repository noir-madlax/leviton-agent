"use client"

import React, { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { useChartDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { ProjectFilters } from "../types/filters"
import { PackageTypeDistributionResponse } from "../data/database-service"
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts'
import { MetricTypeSelector, type MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { BarChart3 } from "lucide-react"
import { useChartsT } from '@/i18n/hooks'

interface PackageSalesTrendChartProps {
  data?: PackageTypeDistributionResponse
  projectId?: string
  initialFilters?: ProjectFilters
}

export function PackageSalesTrendChart({ data: initialData, projectId, initialFilters }: PackageSalesTrendChartProps) {
  const chartsT = useChartsT()
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
    chartId: 'package-sales-trend',
    projectId: projectId || '',
    initialData,
    refreshFunction: async (projectId: string) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getPackageTypeDistributionData(projectId)
    }
  })

  // 过滤器状态管理
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.PACKAGE_PREFERENCE,
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  const { openPanel, loading: panelLoading } = useProductPanel()

  // Chart data processing is handled within individual chart components

  const handlePieClick = (data: { originalName?: string }) => {
    if (data?.originalName) {
      const packageTypeName = data.originalName
      openPanel({
        projectId: projectId || '',
        filters: { extend_fields: { package_type: packageTypeName } },
        title: `${packageTypeName} Products`,
        subtitle: `All products with ${packageTypeName} package type`,
        showFilters: { brand: true, category: true, priceRange: true, packSize: true }
      })
    }
  }

  if (!mounted) {
    return null
  }

  return (
    <section className="mb-6">

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            {chartsT('marketShareBySalesUnit')}
          </h3>
        </div>
      </div>

      {/* Summary Information - moved to below title */}
      {chartData && mounted && !dataLoading && !dataError && (
        <div className="bg-blue-50 border-l-4 border-blue-400 p-3 mb-6 mt-6">
          <p className="text-sm text-blue-700">
            <strong>{chartsT('packageTypeSalesTrendAnalysis')}</strong> Showing package type distribution.
            {chartData.metadata && (
              <> {chartsT('dataCoversRange')}</>
            )}
          </p>
        </div>
      )}

      <div className="mt-6">
        <div data-chart-id="package-sales-trend">
          <Card className="p-6 rounded-xl border shadow-sm">
            <div className="mb-4">
              
              {/* 过滤器组件 */}
              <FilterRenderer
                projectId={projectId || ''}
                chartName={CHART_NAMES.PACKAGE_PREFERENCE}
                currentFilters={filters}
                onChange={handleFiltersChange}
                onFiltersReady={handleFiltersReady}
                disabled={dataLoading}
                className="mb-6"
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

                    {/* 按类别显示饼图 */}
                    {chartData.data.distribution_by_category && chartData.data.distribution_by_category.length > 0 ? (
                      <div className="space-y-8">
                        {chartData.data.distribution_by_category.map((categoryData) => (
                          <div key={categoryData.category} className="bg-gray-50 p-0 mt-6">
                            <h4 className="text-lg font-semibold mb-4 text-center">
                              📦 {categoryData.category} - {chartsT('packageTypeDistribution')}
                            </h4>


                            {/* 类别饼图 */}
                            <div className="bg-gray-50 p-4 relative">
                              <div className="h-[400px] w-full">
                                <ResponsiveContainer width="100%" height="100%">
                                  <PieChart>
                                    <Pie
                                      data={categoryData.package_types.map((packageType, index) => ({
                                        name: packageType.package_type,
                                        originalName: packageType.package_type,
                                        value: metricType === "revenue" ? packageType.revenue : packageType.product_count,
                                        percentage: packageType.percentage,
                                        fill: getChartColor(index)
                                      }))}
                                      cx="50%"
                                      cy="50%"
                                      labelLine={false}
                                      label={({ percentage }: { percentage: number }) => 
                                        percentage >= 5 ? `${percentage.toFixed(1)}%` : null
                                      }
                                      outerRadius={120}
                                      fill="#8884d8"
                                      dataKey="value"
                                      onClick={handlePieClick}
                                      style={{ cursor: 'pointer' }}
                                    >
                                      {categoryData.package_types.map((_, index) => (
                                        <Cell key={`cell-${index}`} fill={getChartColor(index)} />
                                      ))}
                                    </Pie>
                                    <Tooltip 
                                      formatter={(value: number) => [
                                        metricType === "revenue" ? `$${value.toLocaleString()}` : value.toLocaleString(),
                                        metricType === "revenue" ? "Revenue" : "Products"
                                      ]}
                                    />
                                    <Legend />
                                  </PieChart>
                                </ResponsiveContainer>
                              </div>
                              {/* Loading overlay */}
                              {panelLoading && (
                                <div className="absolute inset-0 bg-white/70 flex items-center justify-center z-10 rounded-lg">
                                  <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
                                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                                     <span className="text-gray-700 font-medium">{chartsT('loadingProducts')}</span>
                                  </div>
                                </div>
                              )}
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div className="bg-gray-100 p-4 rounded">
                        <p className="text-sm text-gray-600 text-center">
                          No package type data available
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="bg-gray-50 p-6 rounded-lg">
                    <p className="text-center text-gray-500">No package type sales trend data available</p>
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
