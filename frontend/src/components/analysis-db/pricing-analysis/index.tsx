"use client"

import React, { useState, useMemo, useEffect } from 'react'
import { Card } from "@/components/ui/card"
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'
import { BrandViolinChart } from "../charts/brand-violin-chart"
import { MultiSegmentViolinChart } from "../charts/multi-segment-violin-chart"
import { PriceTypeSelector, type PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { BarChart3 } from "lucide-react"

import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { FilterRenderer } from "@/components/analysis-db/filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { useChartSections } from "@/components/integrated-dashboard/hooks/use-chart-sections"
import { usePriceDistributionDataRefresh, usePriceVsRevenueDataRefresh, useBrandPriceDistributionDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { usePricingAnalysisFilters, usePriceVsRevenueFilters, useBrandPriceDistributionFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { useChartsT } from "@/i18n/hooks"

// 定义价格统计数据类型
interface PriceStats {
  min: number
  max: number
  mean: number
  median?: number
  q1?: number
  q3?: number
}

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

interface PricingAnalysisProps {
  data: {
    priceDistribution: {
      category: string
      skuPrices: number[]
      unitPrices: number[]
      productCount: number
      stats: {
        sku: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
        unit: {
          min: number
          q1: number
          median: number
          mean: number
          q3: number
          max: number
        }
      }
    }[]
    brandPriceDistribution: {
      category: string
      brands: {
        name: string
        skuPrices: number[]
        unitPrices: number[]
      }[]
    }[]
    // 添加散点图所需的数据字段
    topProducts?: {
      segments: Record<string, Array<{
        id: string
        name: string
        brand: string
        price: number
        unitPrice: number
        revenue: number
        volume: number
        url: string
      }>>
      dimmerSwitches: Array<{
        id: string
        name: string
        brand: string
        price: number
        unitPrice: number
        revenue: number
        volume: number
        url: string
      }>
      lightSwitches: Array<{
        id: string
        name: string
        brand: string
        price: number
        unitPrice: number
        revenue: number
        volume: number
        url: string
      }>
    }
    segmentSummary?: Record<string, {
      totalRevenue: number
      totalVolume: number
      productCount: number
      avgPrice: number
      topBrand: string
    }>
    segmentNames?: string[]
  }

  projectId?: string
  initialFilters?: ProjectFilters
}

// 价格分布图表封装 (包含自己的过滤器)
function PriceDistributionByTypeChart({
  initialData,
  priceDistributionData,
  projectId,
  initialFilters,
  priceDataLoading,
  refreshPriceData
}: {
  initialData: PricingAnalysisProps['data'],
  priceDistributionData: any,
  projectId?: string,
  initialFilters?: ProjectFilters,
  priceDataLoading: boolean,
  refreshPriceData: (filters: ProjectFilters) => Promise<any>
}) {
  const chartsT = useChartsT()
  const [priceType, setPriceType] = useState<PriceType>('unit')

  // 过滤器 Hook
  const {
    filters,
    handleFiltersReady,
    handleFiltersChange
  } = usePricingAnalysisFilters(
    refreshPriceData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  // 从刷新后的数据或初始数据中获取分类
  const allCategories = useMemo(() => 
    priceDistributionData?.priceDistribution || initialData?.priceDistribution || [],
    [priceDistributionData, initialData]
  )

  // 生成小提琴图数据
  const violinSegments = useMemo(() => {
    return allCategories.map((category: { category: string; unitPrices: number[]; skuPrices: number[]; productCount?: number; stats?: { unit?: PriceStats; sku?: PriceStats } }, index: number) => ({
      name: category.category,
      prices: priceType === 'unit' ? category.unitPrices : category.skuPrices,
      color: getChartColor(index),
      productCount: category.productCount,
      stats: priceType === 'unit' ? category.stats?.unit : category.stats?.sku
    }))
  }, [allCategories, priceType])


  return (
    <div className="mb-8" data-chart-id={CHART_NAMES.PRICE_ANALYSIS}>
      <Card className="p-6">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-gray-600" />
            {chartsT('priceDistributionByProductType')}
          </h3>
          <FilterRenderer
            chartName={CHART_NAMES.PRICE_ANALYSIS}
            projectId={projectId || ''}
            currentFilters={filters}
            onChange={handleFiltersChange}
            onFiltersReady={handleFiltersReady}
            disabled={priceDataLoading}
            className="mb-6"
          />
        </div>
        
        <div className="mb-4">
          <PriceTypeSelector 
            onChange={setPriceType} 
            defaultValue={priceType}
          />
        </div>
        
        <div className="h-[350px]">
          <MultiSegmentViolinChart
            segments={violinSegments}
            priceType={priceType}
            projectId={projectId || ''}
          />
        </div>
      </Card>
    </div>
  )
}

// Price vs Revenue 散点图独立组件
function PriceVsRevenueChart({
  projectId,
  initialFilters
}: {
  projectId?: string,
  initialFilters?: ProjectFilters
}) {
  const chartsT = useChartsT()
  // 使用独立的数据刷新hook
  const {
    data: priceVsRevenueData,
    loading: priceVsRevenueLoading,
    error: priceVsRevenueError,
    refreshData: refreshPriceVsRevenueData
  } = usePriceVsRevenueDataRefresh(projectId || '', undefined)

  // 使用独立的过滤器hook
  const {
    filters,
    handleFiltersReady,
    handleFiltersChange
  } = usePriceVsRevenueFilters(
    refreshPriceVsRevenueData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  // 🔧 修复：在组件挂载时触发初始数据加载（只执行一次）
  useEffect(() => {
    if (projectId) {
      console.log("🚀 Triggering initial data fetch for PriceVsRevenueChart...");
      const defaultFilters: ProjectFilters = {
        categories: [],
        asins: [],
        brands: [],
        segments: [],
        extend_fields: {},
        time_period: ""
      };
      refreshPriceVsRevenueData(initialFilters || defaultFilters);
    }
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  // 散点图数据处理函数
  const getPriceVsRevenueData = (): ScatterPlotProduct[] => {
    const allProducts: ScatterPlotProduct[] = []
    
    if (!priceVsRevenueData?.topProducts) {
      return []
    }
    
    const topProductsData = priceVsRevenueData.topProducts
    const segmentNamesData = priceVsRevenueData.segmentNames
    
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

  const hasScatterData = priceVsRevenueData?.topProducts && (
    (priceVsRevenueData.topProducts.segments && priceVsRevenueData.segmentNames) ||
    priceVsRevenueData.topProducts.dimmerSwitches ||
    priceVsRevenueData.topProducts.lightSwitches
  )

  return (
    <div className="mb-8" data-chart-id={CHART_NAMES.PRICE_VS_REVENUE}>
      <Card className="p-6 bg-gray-50">
        <div className="mb-4">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-gray-600" />
            {chartsT('priceVsRevenueDistribution')}
          </h3>
          
          <FilterRenderer
            chartName={CHART_NAMES.PRICE_VS_REVENUE}
            projectId={projectId || ''}
            currentFilters={filters}
            onChange={handleFiltersChange}
            onFiltersReady={handleFiltersReady}
            disabled={priceVsRevenueLoading}
            className="mb-6"
          />
        </div>

        {priceVsRevenueLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">{chartsT('loadingScatterData')}</span>
          </div>
        ) : priceVsRevenueError ? (
          <div className="text-red-600 text-center py-8">
            {chartsT('errorLoadingScatterChart')}: {priceVsRevenueError}
          </div>
        ) : hasScatterData ? (
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart data={getPriceVsRevenueData()}>
                <CartesianGrid strokeDasharray="3,3" />
                <XAxis 
                  type="number" 
                  dataKey="x" 
                  name="Price"
                  label={{ value: chartsT('priceUSD'), position: 'insideBottom', offset: -5 }}
                />
                <YAxis 
                  type="number" 
                  dataKey="y" 
                  name="Revenue"
                  label={{ value: chartsT('revenue'), angle: -90, position: 'insideLeft' }}
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
                <Legend />
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
  )
}

// Brand Price Distribution 独立组件
function BrandPriceDistributionChart({
  projectId,
  initialFilters
}: {
  projectId?: string,
  initialFilters?: ProjectFilters
}) {
  const chartsT = useChartsT()
  const [priceType, setPriceType] = useState<PriceType>('unit')

  // 使用独立的数据刷新hook
  const {
    data: brandPriceDistributionData,
    loading: brandPriceDistributionLoading,
    error: brandPriceDistributionError,
    refreshData: refreshBrandPriceDistributionData
  } = useBrandPriceDistributionDataRefresh(projectId || '', undefined)

  // 使用独立的过滤器hook
  const {
    filters,
    handleFiltersReady,
    handleFiltersChange
  } = useBrandPriceDistributionFilters(
    refreshBrandPriceDistributionData,
    projectId,
    { initialFilters: initialFilters || undefined }
  )

  // 🔧 修复：在组件挂载时触发初始数据加载（只执行一次）
  useEffect(() => {
    if (projectId) {
      console.log("🚀 Triggering initial data fetch for BrandPriceDistributionChart...");
      const defaultFilters: ProjectFilters = {
        categories: [],
        asins: [],
        brands: [],
        segments: [],
        extend_fields: {},
        time_period: ""
      };
      refreshBrandPriceDistributionData(initialFilters || defaultFilters);
    }
  }, [projectId]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
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
            disabled={brandPriceDistributionLoading}
            className="mb-6"
          />
          
          <div className="mb-4">
            <PriceTypeSelector 
              onChange={setPriceType} 
              defaultValue={priceType}
            />
          </div>
        </div>

        {brandPriceDistributionLoading ? (
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <span className="ml-2">{chartsT('loadingBrandPriceData')}</span>
          </div>
        ) : brandPriceDistributionError ? (
          <div className="text-red-600 text-center py-8">
            {chartsT('errorLoadingBrandPrice')}: {brandPriceDistributionError}
          </div>
        ) : brandPriceDistributionData?.brandPriceDistribution ? (
          <div className="space-y-8">
            {brandPriceDistributionData.brandPriceDistribution.map((categoryData: { category: string; brands: { name: string; skuPrices: number[]; unitPrices: number[] }[] }) => {
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
  )
}


export function PricingAnalysis({ data: initialData, projectId, initialFilters }: PricingAnalysisProps) {
  const chartsT = useChartsT()
  const [priceType, setPriceType] = useState<PriceType>('unit')
  
  // Get chart sections configuration for conditional rendering
  const { shouldShowChart } = useChartSections('pricing-analysis', projectId || '')

  // Price Distribution数据状态管理 - 使用新的hook
  const {
    data: priceDistributionData,
    loading: priceDataLoading,
    error: priceDataError,
    refreshData: refreshPriceData
  } = usePriceDistributionDataRefresh(projectId || '', initialData)

  // 获取所有分类数据 - 使用新的数据源
  const allCategories = useMemo(() => 
    priceDistributionData?.priceDistribution || initialData?.priceDistribution || [],
    [priceDistributionData, initialData]
  )



  // 检查是否有基础数据 - 使用新的数据源
  const currentData = priceDistributionData || initialData
  const hasBaseData = currentData?.priceDistribution && currentData.priceDistribution.length > 0
  
  if (!hasBaseData) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">💰 {chartsT('pricingAnalysis')}</h2>
        <Card className="p-6 bg-gray-50">
          {priceDataLoading ? (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
              <span className="ml-2">{chartsT('loadingPricingData')}</span>
            </div>
          ) : priceDataError ? (
            <p className="text-red-500 text-center">{chartsT('errorLoadingData')}: {priceDataError}</p>
          ) : (
            <>
              <p className="text-center text-gray-500">{chartsT('noPriceDistributionData')}</p>
              <p className="text-center text-gray-400 text-sm mt-2">{chartsT('waitingForValidData')}</p>
            </>
          )}
        </Card>
      </section>
    )
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-red-500 pl-4 mb-6">
          💰 {chartsT('pricingAnalysis')}
        </h2>

      {/* Price Distribution by Segment - 移至最上方 */}
      {shouldShowChart('price-distribution-overview') && (
      <div className="mb-8" data-chart-id="price-distribution-overview">
        <Card className="p-6 bg-gray-50">
          <h3 className="text-lg font-semibold text-gray-800 mb-4 flex items-center">
            <BarChart3 className="w-5 h-5 mr-2 text-gray-600" />
            {chartsT('priceDistributionBySegment')}
          </h3>
          <div className="mb-4">
            <PriceTypeSelector 
              onChange={setPriceType} 
              defaultValue={priceType}
            />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left pb-2">{chartsT('segment')}</th>
                  <th className="text-right pb-2">{chartsT('productsText')}</th>
                  <th className="text-right pb-2">{chartsT('min')}</th>
                  <th className="text-right pb-2">{chartsT('median')}</th>
                  <th className="text-right pb-2">{chartsT('max')}</th>
                  <th className="text-right pb-2">{chartsT('average')}</th>
                </tr>
              </thead>
              <tbody>
                {allCategories.map((category: { category: string; stats: { unit?: PriceStats; sku?: PriceStats }; unitPrices: number[]; skuPrices: number[] }, index: number) => {
                  const stats = priceType === 'unit' ? category.stats.unit : category.stats.sku
                  const segmentName = category.category
                  // 通过价格数组的长度计算产品数量
                  const productCount = priceType === 'unit' ? category.unitPrices.length : category.skuPrices.length

                  return (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="py-2 flex items-center">
                        <span className="mr-2">{getSegmentEmoji(segmentName)}</span>
                        <span className="font-medium">{segmentName}</span>
                      </td>
                      <td className="text-right py-2">{productCount}</td>
                      <td className="text-right py-2">
                        <span className="text-green-600 font-medium">${stats?.min?.toFixed(2) || 'N/A'}</span>
                      </td>
                      <td className="text-right py-2">
                        <span className="text-blue-600 font-medium">${stats?.median?.toFixed(2) || 'N/A'}</span>
                      </td>
                      <td className="text-right py-2">
                        <span className="text-red-600 font-medium">${stats?.max?.toFixed(2) || 'N/A'}</span>
                      </td>
                      <td className="text-right py-2">
                        <span className="text-purple-600 font-medium">${stats?.mean?.toFixed(2) || 'N/A'}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>
      )}

      {/* Price vs Revenue Distribution of Top Selling 20 Products - Independent Component */}
      {shouldShowChart('price-vs-revenue') && (
        <PriceVsRevenueChart
          projectId={projectId}
          initialFilters={initialFilters}
        />
      )}

      {/* Price Distribution by Product Type - with its own filter */}
      {shouldShowChart('price-distribution-by-type') && (
        <PriceDistributionByTypeChart
          initialData={initialData}
          priceDistributionData={priceDistributionData}
          projectId={projectId}
          initialFilters={initialFilters}
          priceDataLoading={priceDataLoading}
          refreshPriceData={refreshPriceData}
        />
      )}

      {/* Brand Price Distribution - Independent Component */}
      {shouldShowChart('price-distribution-by-brands') && (
        <BrandPriceDistributionChart
          projectId={projectId}
          initialFilters={initialFilters}
        />
      )}
    </section>
  )
}

// 根据分类名称获取emoji
function getSegmentEmoji(segmentName: string): string {
  const emojiMap: Record<string, string> = {
    // Category维度
    'Smart WiFi Dimmer Switches': '🔆',
    'Manual Slide Dimmer Switches': '🎛️',
    'Smart WiFi On Off Switches': '🔥',
    'Single Pole Rocker Wall Switches': '⚡',
    'In Wall Timer Switches': '⏰',
    'Motion Sensor Switches': '🚶',
    'RF Wireless Remote Switch Systems': '📡',
    'Mechanical Timer Outlets': '🔌',
    'Dimmer Switches': '🎛️',
    'Light Switches': '💡',
    // Smart Capability维度
    'Smart': '🔌',
    'Non-Smart': '🔧'
  }
  
  // 处理组合名称（如 "Dimmer Switches + Smart"）
  if (segmentName.includes(' + ')) {
    const parts = segmentName.split(' + ')
    if (parts.length >= 2) {
      const category = parts[0].trim()
      const smart = parts[1].trim()
      
      // 为组合提供特定的emoji
      if (category === 'Dimmer Switches' && smart === 'Smart') {
        return '🔆' // 智能调光开关
      } else if (category === 'Dimmer Switches' && smart === 'Non-Smart') {
        return '🎛️' // 非智能调光开关
      } else if (category === 'Light Switches' && smart === 'Smart') {
        return '💡' // 智能电灯开关
      } else if (category === 'Light Switches' && smart === 'Non-Smart') {
        return '⚡' // 非智能电灯开关
      }
    }
  }
  
  return emojiMap[segmentName] || '🔲'
}
