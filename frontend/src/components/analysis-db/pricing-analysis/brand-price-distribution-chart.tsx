"use client"

import React, { useState } from "react"
import { Card } from "@/components/ui/card"
import { BarChart3 } from "lucide-react"
import { BrandViolinChart } from "../charts/brand-violin-chart"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { useChartDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { PriceTypeSelector, type PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { useChartsT } from "@/i18n/hooks"
import { ProjectFilters } from "@/components/analysis-db/types/filters"


interface BrandPriceDistributionChartProps {
  projectId?: string
  initialFilters?: ProjectFilters
}

export function BrandPriceDistributionChart({
  projectId,
  initialFilters
}: BrandPriceDistributionChartProps) {
  const chartsT = useChartsT()
  const [priceType, setPriceType] = useState<PriceType>('unit')

  // 🆕 数据状态管理 - 使用通用Hook
  const {
    data: chartData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = useChartDataRefresh({
    chartId: 'brand-price-distribution',
    projectId: projectId || '',
    initialData: undefined,
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => { // eslint-disable-line @typescript-eslint/no-unused-vars
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getBrandPriceDistributionData(projectId)
    }
  })

  // 🆕 过滤器状态管理 - 使用通用Hook
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.BRAND_PRICE_DISTRIBUTION,
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  const dataToUse = chartData

  return (
    <section className="mb-10">
      <h3 className="text-xl font-bold text-gray-800 border-l-4 border-orange-500 pl-4 mb-6">
        🏷️ {chartsT('brandPriceDistribution')}
      </h3>

      <div className="mb-8" data-chart-id={CHART_NAMES.BRAND_PRICE_DISTRIBUTION}>
        <Card className="p-6 bg-gray-50">
          <div className="mb-4">
            <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
              <BarChart3 className="w-5 h-5 mr-2 text-gray-600" />
              {chartsT('brandPriceDistribution')}
            </h3>
            
            <FilterRenderer
              chartName={CHART_NAMES.BRAND_PRICE_DISTRIBUTION}
              projectId={projectId || ''}
              currentFilters={filters}
              onChange={handleFiltersChange}
              onFiltersReady={handleFiltersReady}
              disabled={dataLoading}
              className="mb-6"
            />
            
            <div className="mb-4">
              <PriceTypeSelector 
                onChange={setPriceType} 
                defaultValue={priceType}
              />
            </div>
          </div>

          {dataLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">正在加载品牌价格分布数据...</span>
            </div>
          ) : !filtersReady ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">正在初始化过滤器...</span>
            </div>
          ) : dataError ? (
            <div className="text-red-600 text-center py-8">
              数据加载失败: {dataError}
              <button 
                onClick={() => refreshData(filters)}
                className="block mx-auto mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
              >
                重新加载
              </button>
            </div>
          ) : dataToUse?.brandPriceDistribution ? (
            <div className="space-y-8">
              {dataToUse.brandPriceDistribution.map((categoryData: { category: string; brands: { name: string; skuPrices: number[]; unitPrices: number[] }[] }) => {
                return (
                  <div key={categoryData.category}>
                    <h4 className="text-lg font-medium mb-4">{categoryData.category}</h4>
                    <div className="h-[320px]">
                      <BrandViolinChart
                        brands={categoryData.brands}
                        priceType={priceType}
                        category={categoryData.category}
                        projectId={projectId || ''}
                      />
                    </div>
                  </div>
                )
              })}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              {chartsT('noBrandPriceData')}
            </div>
          )}
        </Card>
      </div>
    </section>
  )
}
