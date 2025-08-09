"use client"

import React from 'react'
import { Card } from "@/components/ui/card"
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'
import { BarChart3 } from "lucide-react"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { useChartDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { useChartsT } from "@/i18n/hooks"
import { ProjectFilters } from "@/components/analysis-db/types/filters"

// 定义产品数据类型
interface ProductData {
  id?: string
  name?: string
  brand?: string
  price?: number
  unitPrice?: number
  revenue?: number
  volume?: number
  url?: string
  [key: string]: unknown
}

// 定义散点图数据类型
interface ScatterPlotProduct {
  id: string
  name: string
  brand: string
  price: number
  unitPrice: number
  revenue: number
  volume: number
  url: string
  segment: string
  x: number
  y: number
}

// 定义散点图点击事件数据类型
interface ScatterClickData {
  payload: {
    id?: string
    name: string
    brand: string
    price?: number
    unitPrice?: number
    revenue?: number
    volume?: number
    url?: string
    segment?: string
    x: number
    y: number
  }
}


interface PriceVsRevenueChartProps {
  projectId?: string
  initialFilters?: ProjectFilters
}

export function PriceVsRevenueChart({
  projectId,
  initialFilters
}: PriceVsRevenueChartProps) {
  const chartsT = useChartsT()
  
  // 🆕 数据状态管理 - 使用通用Hook
  const {
    data: chartData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = useChartDataRefresh({
    chartId: 'price-vs-revenue',
    projectId: projectId || '',
    initialData: undefined,
    refreshFunction: async (projectId: string, _filters: ProjectFilters) => { // eslint-disable-line @typescript-eslint/no-unused-vars
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getPriceVsRevenueData(projectId)
    }
  })

  // 🆕 过滤器状态管理 - 使用通用Hook
  const {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange
  } = useChartWithFilters(
    CHART_NAMES.PRICE_VS_REVENUE,
    refreshData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  // 散点图数据处理函数
  const getPriceVsRevenueData = (): ScatterPlotProduct[] => {
    const allProducts: ScatterPlotProduct[] = []
    const dataToUse = chartData
    
    if (!dataToUse?.topProducts) {
      return []
    }
    
    const topProductsData = dataToUse.topProducts
    const segmentNamesData = dataToUse.segmentNames
    
    // 收集segments中的产品
    if (topProductsData.segments && segmentNamesData) {
      segmentNamesData.forEach((segment: string) => {
        const products = topProductsData.segments[segment] || []
        products.forEach((product: ProductData) => {
          allProducts.push({
            id: product.id || '',
            name: product.name || '',
            brand: product.brand || '',
            price: product.price || 0,
            unitPrice: product.unitPrice || product.price || 0,
            revenue: product.revenue || 0,
            volume: product.volume || 0,
            url: product.url || '',
            segment: segment,
            x: product.price || 0,
            y: product.revenue || 0
          })
        })
      })
    }
    
    // 收集dimmerSwitches中的产品
    if (topProductsData.dimmerSwitches) {
      topProductsData.dimmerSwitches.forEach((product: ProductData) => {
        allProducts.push({
          id: product.id || '',
          name: product.name || '',
          brand: product.brand || '',
          price: product.price || 0,
          unitPrice: product.unitPrice || product.price || 0,
          revenue: product.revenue || 0,
          volume: product.volume || 0,
          url: product.url || '',
          segment: 'Dimmer Switches',
          x: product.price || 0,
          y: product.revenue || 0
        })
      })
    }
    
    // 收集lightSwitches中的产品
    if (topProductsData.lightSwitches) {
      topProductsData.lightSwitches.forEach((product: ProductData) => {
        allProducts.push({
          id: product.id || '',
          name: product.name || '',
          brand: product.brand || '',
          price: product.price || 0,
          unitPrice: product.unitPrice || product.price || 0,
          revenue: product.revenue || 0,
          volume: product.volume || 0,
          url: product.url || '',
          segment: 'Light Switches',
          x: product.price || 0,
          y: product.revenue || 0
        })
      })
    }
    
    return allProducts
  }

  const getBrandDataForScatterChart = () => {
    const scatterData = getPriceVsRevenueData()
    const brandData: Record<string, ScatterPlotProduct[]> = {}
    
    scatterData.forEach(item => {
      if (!brandData[item.brand]) {
        brandData[item.brand] = []
      }
      brandData[item.brand].push(item)
    })
    
    return Object.entries(brandData).map(([brand, products]) => ({
      brand,
      products
    }))
  }

  // 散点图点击事件处理器
  const handleScatterClick = (data: ScatterClickData) => {
    if (data && data.payload) {
      // 直接跳转Amazon链接
      if (data.payload.url) {
        window.open(data.payload.url, '_blank', 'noopener,noreferrer')
      } else if (data.payload.id) {
        // 如果没有直接的URL但有产品ID（ASIN），构造Amazon链接
        const amazonUrl = `https://www.amazon.com/dp/${data.payload.id}`
        window.open(amazonUrl, '_blank', 'noopener,noreferrer')
      }
    }
  }

  const dataToUse = chartData
  const hasScatterData = dataToUse?.topProducts && (
    (dataToUse.topProducts.segments && dataToUse.segmentNames) ||
    dataToUse.topProducts.dimmerSwitches ||
    dataToUse.topProducts.lightSwitches
  )

  return (
    <section className="mb-10">
      {/* External title */}
      <div className="mb-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            <BarChart3 className="w-5 h-5" />
            {chartsT('priceVsRevenueDistribution')}
          </h3>
        </div>
      </div>
      <div className="mb-8" data-chart-id={CHART_NAMES.PRICE_VS_REVENUE}>
        <Card className="p-6 bg-gray-50 rounded-xl border shadow-sm">
          <div className="mb-4">
            {/* inner title removed to avoid duplication */}
            
            <FilterRenderer
              chartName={CHART_NAMES.PRICE_VS_REVENUE}
              projectId={projectId || ''}
              currentFilters={filters}
              onChange={handleFiltersChange}
              onFiltersReady={handleFiltersReady}
              disabled={dataLoading}
              className="mb-6"
            />
          </div>

          {dataLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">{chartsT('loadingScatterData')}</span>
            </div>
          ) : !filtersReady ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">{chartsT('initializingFilters')}</span>
            </div>
          ) : dataError ? (
            <div className="text-red-600 text-center py-8">
              {chartsT('errorLoadingScatterChart')}: {dataError}
              <button 
                onClick={() => refreshData(filters)}
                className="block mx-auto mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm"
              >
                {chartsT('retry')}
              </button>
            </div>
          ) : hasScatterData ? (
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart data={getPriceVsRevenueData()} margin={{ top: 5, right: 20, bottom: 30, left: 50 }}>
                  <CartesianGrid strokeDasharray="3,3" />
                  <XAxis 
                    type="number" 
                    dataKey="x" 
                    name="Price"
                    label={{ value: chartsT('priceUSD'), position: 'bottom', offset: 10 }}
                  />
                  <YAxis 
                    type="number" 
                    dataKey="y" 
                    name="Revenue"
                    label={{ value: chartsT('revenue'), angle: -90, position: 'left', offset: 30 }}
                  />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3,3' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload
                        return (
                          <div className="bg-white p-3 border rounded shadow">
                            <p className="font-medium">{data.name}</p>
                            <p className="text-sm text-gray-600">{chartsT('brand')}: {data.brand}</p>
                            <p className="text-sm text-gray-600">{chartsT('segment')}: {data.segment}</p>
                            <p className="text-sm text-gray-600">{chartsT('price')}: ${data.price}</p>
                            <p className="text-sm text-gray-600">{chartsT('revenue')}: ${data.revenue.toLocaleString()}</p>
                          </div>
                        )
                      }
                      return null
                    }}
                  />
                  <Legend verticalAlign="top" align="center" wrapperStyle={{ paddingBottom: 20 }} />
                  {getBrandDataForScatterChart().map((brandData, index) => (
                    <Scatter
                      key={brandData.brand}
                      name={brandData.brand}
                      data={brandData.products}
                      fill={getChartColor(index)}
                      onClick={handleScatterClick}
                      style={{ cursor: 'pointer' }}
                    />
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
              {chartsT('noScatterData')}
            </div>
          )}
        </Card>
      </div>
    </section>
  )
}
