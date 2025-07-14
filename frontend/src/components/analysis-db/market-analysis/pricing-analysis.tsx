"use client"

import React, { useState, useMemo } from 'react'
import { Card } from "@/components/ui/card"
import { XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter } from 'recharts'
import { BrandViolinChart } from "../charts/brand-violin-chart"
import { MultiSegmentViolinChart } from "../charts/multi-segment-violin-chart"
import { PriceTypeSelector, type PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import type { Product } from "@/components/analysis-db/types/analysis"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"

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
  productLists: {
    byBrand: Record<string, Product[]>
    bySegment: Record<string, Product[]>
    byPackageSize: Record<string, Product[]>
  }
}

export function PricingAnalysis({ data, productLists }: PricingAnalysisProps) {
  const [priceType, setPriceType] = useState<PriceType>('unit')
  const { openPanel } = useProductPanel()

  // 获取所有分类数据
  const allCategories = useMemo(() => 
    data?.priceDistribution || [],
    [data]
  )

  // 生成Multi-Segment Violin Chart数据
  const violinSegments = useMemo(() => {
    return allCategories.map((category, index) => ({
      name: category.category,
      prices: priceType === 'unit' ? category.unitPrices : category.skuPrices,
      color: getChartColor(index),
      productCount: category.productCount,
      stats: priceType === 'unit' ? category.stats.unit : category.stats.sku
    }))
  }, [allCategories, priceType])

  // 散点图相关的数据处理函数
  const getPriceVsRevenueData = () => {
    const allProducts: any[] = []
    
    // 检查是否有散点图所需的数据
    if (!data?.topProducts) {
      return []
    }
    
    // 收集segments中的产品
    if (data.topProducts.segments && data.segmentNames) {
      data.segmentNames.forEach((segment) => {
        const products = data.topProducts!.segments[segment] || []
        products.forEach(product => {
          allProducts.push({
            ...product,
            segment: segment,
            x: product.price || 0,
            y: product.revenue || 0
          })
        })
      })
    }
    
    // 收集dimmerSwitches中的产品
    if (data.topProducts.dimmerSwitches) {
      data.topProducts.dimmerSwitches.forEach(product => {
        allProducts.push({
          ...product,
          segment: 'Dimmer Switches',
          x: product.price || 0,
          y: product.revenue || 0
        })
      })
    }
    
    // 收集lightSwitches中的产品
    if (data.topProducts.lightSwitches) {
      data.topProducts.lightSwitches.forEach(product => {
        allProducts.push({
          ...product,
          segment: 'Light Switches',
          x: product.price || 0,
          y: product.revenue || 0
        })
      })
    }
    
    // 按revenue排序，取前20
    return allProducts
      .sort((a, b) => b.revenue - a.revenue)
      .slice(0, 20)
  }

  const getBrandDataForScatterChart = () => {
    const scatterData = getPriceVsRevenueData()
    const brandData: Record<string, any[]> = {}
    
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

  const handleViolinClick = (segmentName: string) => {
    // 获取该分类的产品
    const products = productLists.bySegment[segmentName] || []
    openPanel(products, `${segmentName} Products`)
  }

  const handleBrandViolinClick = (brand: string, category: string) => {
    // 获取该品牌的产品
    const products = productLists.byBrand[brand] || []
    openPanel(products, `${brand} Products`)
  }

  // 检查是否有基础数据
  const hasBaseData = data?.priceDistribution && data.priceDistribution.length > 0
  const hasScatterData = data?.topProducts && (
    (data.topProducts.segments && data.segmentNames) ||
    data.topProducts.dimmerSwitches ||
    data.topProducts.lightSwitches
  )
  
  if (!hasBaseData) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">💰 Pricing Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-center text-gray-500">Price distribution data is not available.</p>
          <p className="text-center text-gray-400 text-sm mt-2">Waiting for valid product data...</p>
        </Card>
      </section>
    )
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">💰 Pricing Analysis</h2>

      {/* Price vs Revenue Scatter Plot */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Top 20 Products by Revenue</h3>
        <Card className="p-6 bg-gray-50">
          {hasScatterData ? (
            <div className="h-[400px]">
              <ResponsiveContainer width="100%" height="100%">
                <ScatterChart data={getPriceVsRevenueData()}>
                  <CartesianGrid strokeDasharray="3,3" />
                  <XAxis 
                    type="number" 
                    dataKey="x" 
                    name="Price"
                    label={{ value: 'Price (USD)', position: 'insideBottom', offset: -5 }}
                  />
                  <YAxis 
                    type="number" 
                    dataKey="y" 
                    name="Revenue"
                    label={{ value: 'Revenue', angle: -90, position: 'insideLeft' }}
                  />
                  <Tooltip 
                    cursor={{ strokeDasharray: '3,3' }}
                    content={({ active, payload }) => {
                      if (active && payload && payload.length) {
                        const data = payload[0].payload
                        return (
                          <div className="bg-white p-3 border rounded shadow">
                            <p className="font-medium">{data.name}</p>
                            <p className="text-sm text-gray-600">Brand: {data.brand}</p>
                            <p className="text-sm text-gray-600">Segment: {data.segment}</p>
                            <p className="text-sm text-gray-600">Price: ${data.price}</p>
                            <p className="text-sm text-gray-600">Revenue: ${data.revenue.toLocaleString()}</p>
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
                    />
                  ))}
                </ScatterChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="h-[400px] flex items-center justify-center">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p className="text-gray-500">Loading scatter chart data...</p>
                <p className="text-sm text-gray-400 mt-2">Waiting for product analysis data</p>
              </div>
            </div>
          )}
        </Card>
      </div>

      {/* Price Distribution by Segment */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Price Distribution by Segment</h3>
        <Card className="p-6 bg-gray-50">
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
                  <th className="text-left pb-2">Segment</th>
                  <th className="text-right pb-2">Products</th>
                  <th className="text-right pb-2">Min</th>
                  <th className="text-right pb-2">Median</th>
                  <th className="text-right pb-2">Max</th>
                  <th className="text-right pb-2">Average</th>
                </tr>
              </thead>
              <tbody>
                {allCategories.map((category, index) => {
                  const stats = priceType === 'unit' ? category.stats.unit : category.stats.sku
                  const segmentName = category.category
                  
                  return (
                    <tr key={index} className="border-b hover:bg-gray-50">
                      <td className="py-2 flex items-center">
                        <span className="mr-2">{getSegmentEmoji(segmentName)}</span>
                        <span className="font-medium">{segmentName}</span>
                      </td>
                      <td className="text-right py-2">{category.productCount}</td>
                      <td className="text-right py-2">
                        <span className="text-green-600 font-medium">${stats.min.toFixed(2)}</span>
                      </td>
                      <td className="text-right py-2">
                        <span className="text-blue-600 font-medium">${stats.median.toFixed(2)}</span>
                      </td>
                      <td className="text-right py-2">
                        <span className="text-red-600 font-medium">${stats.max.toFixed(2)}</span>
                      </td>
                      <td className="text-right py-2">
                        <span className="text-purple-600 font-medium">${stats.mean.toFixed(2)}</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </Card>
      </div>

      {/* All Segments Price Distribution Comparison */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">All Segments Price Distribution Comparison</h3>
        <Card className="p-6 bg-gray-50">
          <div className="mb-4">
            <PriceTypeSelector 
              onChange={setPriceType} 
              defaultValue={priceType}
            />
          </div>
          
          <div className="h-[500px]">
            <MultiSegmentViolinChart 
              segments={violinSegments}
              priceType={priceType}
              onViolinClick={handleViolinClick}
            />
          </div>
        </Card>
      </div>

      {/* Brand Price Distribution */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Brand Price Distribution</h3>
        <Card className="p-6 bg-gray-50">
          <div className="mb-4">
            <PriceTypeSelector 
              onChange={setPriceType} 
              defaultValue={priceType}
            />
          </div>
          
          <div className="space-y-8">
            {data.brandPriceDistribution.map((categoryData, index) => (
              <div key={index}>
                <h4 className="text-lg font-medium mb-4">{categoryData.category}</h4>
                <div className="h-[400px]">
                  <BrandViolinChart 
                    brands={categoryData.brands}
                    priceType={priceType}
                    category={categoryData.category}
                    onViolinClick={handleBrandViolinClick}
                  />
                </div>
              </div>
            ))}
          </div>
        </Card>
      </div>
    </section>
  )
}

// 根据分类名称获取emoji
function getSegmentEmoji(segmentName: string): string {
  const emojiMap: Record<string, string> = {
    'Smart WiFi Dimmer Switches': '🔆',
    'Manual Slide Dimmer Switches': '🎛️',
    'Smart WiFi On Off Switches': '🔥',
    'Single Pole Rocker Wall Switches': '⚡',
    'In Wall Timer Switches': '⏰',
    'Motion Sensor Switches': '🚶',
    'RF Wireless Remote Switch Systems': '📡',
    'Mechanical Timer Outlets': '🔌'
  }
  return emojiMap[segmentName] || '🔲'
}
