"use client"

import React, { useState, useMemo } from "react"
import { Card } from "@/components/ui/card"
import { BarChart3 } from "lucide-react"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { useChartDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { PriceTypeSelector, type PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { MultiSegmentViolinChart } from "@/components/analysis-db/charts/multi-segment-violin-chart"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { useChartsT } from "@/i18n/hooks"
import { ProjectFilters } from "@/components/analysis-db/types/filters"


interface PriceDistributionOverviewProps {
  projectId?: string
  initialFilters?: ProjectFilters
}

// 定义价格统计数据类型
interface PriceStats {
  min: number
  max: number
  mean: number
  median?: number
  q1?: number
  q3?: number
}

export function PriceDistributionOverview({ 
  projectId, 
  initialFilters 
}: PriceDistributionOverviewProps) {
  const chartsT = useChartsT()
  const [priceType, setPriceType] = useState<PriceType>('unit')

  // 🆕 数据状态管理 - 使用通用Hook
  const {
    data: chartData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = useChartDataRefresh({
    chartId: 'price-distribution-overview',
    projectId: projectId || '',
    initialData: undefined,
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => { // eslint-disable-line @typescript-eslint/no-unused-vars
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getPriceDistributionOverviewData(projectId)
    }
  })

  // 🆕 过滤器状态管理 - 使用通用Hook
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.PRICE_DISTRIBUTION_OVERVIEW,
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  // 从刷新后的数据中获取分类，适配后端返回的 overview_data 格式
  const allCategories = useMemo(() => {
    if (!chartData?.overview_data) {
      return []
    }
    
    // 将后端返回的 overview_data 格式转换为前端期望的格式
    return chartData.overview_data.map((segment: {
      segment: string
      products: number
      min_price: number
      median_price: number
      max_price: number
      average_price: number
    }) => ({
      category: segment.segment,
      // 由于后端只返回统计数据，创建模拟的价格数组用于展示
      unitPrices: [], // 空数组，因为后端没有返回具体价格分布数据
      skuPrices: [],  // 空数组，因为后端没有返回具体价格分布数据
      productCount: segment.products,
      stats: {
        unit: {
          min: segment.min_price,
          max: segment.max_price,
          mean: segment.average_price,
          median: segment.median_price,
          q1: segment.min_price, // 暂时使用min价格
          q3: segment.max_price   // 暂时使用max价格
        },
        sku: {
          min: segment.min_price,
          max: segment.max_price,
          mean: segment.average_price,
          median: segment.median_price,
          q1: segment.min_price,
          q3: segment.max_price
        }
      }
    }))
  }, [chartData])

  // 生成小提琴图数据
  const violinSegments = useMemo(() => {
    return allCategories.map((category: { 
      category: string; 
      unitPrices: number[]; 
      skuPrices: number[]; 
      productCount?: number; 
      stats?: { unit?: PriceStats; sku?: PriceStats } 
    }, index: number) => ({
      name: category.category,
      prices: priceType === 'unit' ? category.unitPrices : category.skuPrices,
      color: getChartColor(index),
      productCount: category.productCount,
      stats: priceType === 'unit' ? category.stats?.unit : category.stats?.sku
    }))
  }, [allCategories, priceType])

  return (
    <section className="mb-10">
      <div className="mb-8" data-chart-id="price-distribution-overview">
        <Card className="p-6 bg-gray-50">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2 text-gray-600" />
              {chartsT('priceDistributionBySegment')}
            </h3>
            
            {/* 🆕 独立过滤器组件 */}
            <FilterRenderer
              projectId={projectId || ''}
              chartName="price-distribution-overview"
              currentFilters={filters}
              onChange={handleFiltersChange}
              onFiltersReady={handleFiltersReady}
              disabled={dataLoading}
              className="mb-6"
            />
          </div>

          <div className="mb-4">
            <PriceTypeSelector 
              onChange={setPriceType} 
              defaultValue={priceType}
            />
          </div>

          {/* 图表内容区域 */}
          <div className="overflow-x-auto">
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
              chartData ? (
                // 🆕 由于后端只返回统计数据而非价格分布数组，显示统计表格
                <div>
                  {allCategories.length > 0 ? (
                    <div className="overflow-x-auto">
                      <table className="w-full">
                        <thead>
                          <tr className="border-b">
                            <th className="text-left pb-2">Segment</th>
                            <th className="text-right pb-2">Products</th>
                            <th className="text-right pb-2">Min Price</th>
                            <th className="text-right pb-2">Median Price</th>
                            <th className="text-right pb-2">Max Price</th>
                            <th className="text-right pb-2">Average Price</th>
                          </tr>
                        </thead>
                        <tbody>
                          {allCategories.map((category, index) => {
                            const stats = priceType === 'unit' ? category.stats.unit : category.stats.sku
                            return (
                              <tr key={index} className="border-b hover:bg-gray-50">
                                <td className="py-2 font-medium">{category.category}</td>
                                <td className="text-right py-2">{category.productCount}</td>
                                <td className="text-right py-2">
                                  <span className="text-green-600 font-medium">${stats.min?.toFixed(2) || 'N/A'}</span>
                                </td>
                                <td className="text-right py-2">
                                  <span className="text-blue-600 font-medium">${stats.median?.toFixed(2) || 'N/A'}</span>
                                </td>
                                <td className="text-right py-2">
                                  <span className="text-red-600 font-medium">${stats.max?.toFixed(2) || 'N/A'}</span>
                                </td>
                                <td className="text-right py-2">
                                  <span className="text-purple-600 font-medium">${stats.mean?.toFixed(2) || 'N/A'}</span>
                                </td>
                              </tr>
                            )
                          })}
                        </tbody>
                      </table>
                    </div>
                  ) : (
                    <div className="bg-gray-100 p-6 rounded-lg">
                      <p className="text-center text-gray-500">No price distribution data available</p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="bg-gray-50 p-6 rounded-lg">
                  <p className="text-center text-gray-500">No data available</p>
                </div>
              )
            )}
          </div>
        </Card>
      </div>
    </section>
  )
}
