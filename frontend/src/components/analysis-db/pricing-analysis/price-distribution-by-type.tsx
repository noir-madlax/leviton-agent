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

// 定义价格统计数据类型
interface PriceStats {
  min: number
  max: number
  mean: number
  median?: number
  q1?: number
  q3?: number
}


interface PriceDistributionByTypeProps {
  projectId?: string
  initialFilters?: ProjectFilters
}

export function PriceDistributionByTypeChart({
  projectId,
  initialFilters
}: PriceDistributionByTypeProps) {
  const chartsT = useChartsT()
  const [priceType, setPriceType] = useState<PriceType>('unit')

  // 🆕 数据状态管理 - 使用通用Hook
  const {
    data: chartData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = useChartDataRefresh({
    chartId: 'price-distribution-by-type',
    projectId: projectId || '',
    initialData: undefined,
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => { // eslint-disable-line @typescript-eslint/no-unused-vars
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getPriceDistributionByTypeData(projectId)
    }
  })

  // 🆕 过滤器状态管理 - 使用通用Hook
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.PRICE_ANALYSIS,
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  // 从刷新后的数据中获取分类
  const allCategories = useMemo(() => 
    chartData?.priceDistribution || [],
    [chartData]
  )

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
      {/* External title */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            {chartsT('priceDistributionByProductType')}
          </h3>
        </div>
      </div>
      <div className="mb-8" data-chart-id={CHART_NAMES.PRICE_ANALYSIS}>
        <Card className="p-6 bg-gray-50 rounded-xl border shadow-sm">
          <div className="mb-4">
            {/* 内部标题移除，避免双标题 */}
            
            {/* 🆕 独立过滤器组件 */}
            <FilterRenderer
              chartName={CHART_NAMES.PRICE_ANALYSIS}
              projectId={projectId || ''}
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
          <div className="h-[350px]">
            {dataLoading ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                  <p className="text-sm text-gray-600">{chartsT('updatingChartData')}</p>
                </div>
              </div>
            ) : !filtersReady ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                  <p className="text-sm text-gray-600">{chartsT('initializingFilters')}</p>
                </div>
              </div>
            ) : dataError ? (
              <div className="flex items-center justify-center h-full">
                <div className="text-center">
                  <p className="text-sm text-red-600 mb-3">{chartsT('dataLoadFailed')}: {dataError}</p>
                  <button 
                    onClick={() => refreshData(filters)}
                    className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
                  >
                    {chartsT('retry')}
                  </button>
                </div>
              </div>
            ) : (
              violinSegments.length > 0 ? (
                <MultiSegmentViolinChart
                  segments={violinSegments}
                  priceType={priceType}
                  projectId={projectId || ''}
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <p className="text-center text-gray-500">No price distribution data available</p>
                </div>
              )
            )}
          </div>
        </Card>
      </div>
    </section>
  )
}
