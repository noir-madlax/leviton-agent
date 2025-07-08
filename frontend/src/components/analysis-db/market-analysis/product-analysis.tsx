"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, Cell } from 'recharts'
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { filterValidProductSegments } from "@/components/analysis-db/shared/segment-filter-utils"

interface ProductAnalysisProps {
  data: {
    topProducts: {
      segments: Record<string, any[]>
      dimmerSwitches: any[]
      lightSwitches: any[]
    }
    segmentSummary: Record<string, {
      totalRevenue: number
      totalVolume: number
      productCount: number
      avgPrice: number
      topBrand: string
    }>
    segmentNames: string[]
    segmentColors: string[]
  }
  productLists: {
    byBrand: Record<string, any[]>
    bySegment: Record<string, any[]>
    byPackageSize: Record<string, any[]>
  }
}

export function ProductAnalysis({ data, productLists }: ProductAnalysisProps) {
  const [selectedSegment, setSelectedSegment] = useState<string>("")
  const { openPanel } = useProductPanel()

  // 获取动态segment信息并过滤，只保留有收入的segments
  const allSegmentNames = data.segmentNames || []
  const segmentSummary = data.segmentSummary || {}
  const segmentNames = filterValidProductSegments(allSegmentNames, segmentSummary)
  
  // 使用全局颜色配置，如果后端提供了颜色则使用后端的，否则使用全局配置
  const segmentColors = data.segmentColors || Array.from({ length: 20 }, (_, i) => getChartColor(i))
  
  // 如果没有有效的segments数据，显示空状态
  if (!segmentNames.length) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📊 Product Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-gray-500 text-center">No valid product segments with revenue data available</p>
          <p className="text-gray-400 text-sm text-center mt-2">Segments with zero revenue are filtered out</p>
        </Card>
      </section>
    )
  }

  // 预先计算按收入排序的segment数据，颜色基于排序后位置分配
  const sortedSegmentData = segmentNames.map((segment, index) => {
    const summary = segmentSummary[segment] || {
      totalRevenue: 0,
      totalVolume: 0,
      productCount: 0,
      avgPrice: 0,
      topBrand: 'N/A'
    }
    
    return {
      segment: segment,
      revenue: summary.totalRevenue,
      volume: summary.totalVolume,
      productCount: summary.productCount,
      avgPrice: summary.avgPrice,
      topBrand: summary.topBrand,
      originalIndex: index
    }
  }).sort((a, b) => b.revenue - a.revenue) // 先排序
  .map((item, sortedIndex) => ({ 
    ...item, 
    color: getChartColor(sortedIndex) // 基于排序后位置分配颜色，确保第一名总是橙色
  }))

  // 获取按收入排序的segment列表
  const sortedSegmentNames = sortedSegmentData.map(item => item.segment)
  
  // 设置默认选中的segment
  const activeSegment = selectedSegment || sortedSegmentNames[0]

  // 动态检测产品类型
  const getProductType = () => {
    const firstSegment = segmentNames[0] || ""
    if (firstSegment.toLowerCase().includes('air fryer')) return "Air Fryers"
    if (firstSegment.toLowerCase().includes('dimmer')) return "Dimmer Switches"
    if (firstSegment.toLowerCase().includes('switch')) return "Light Switches"
    return "Products"
  }

  const productType = getProductType()

  // Price vs Revenue 散点图数据
  const getPriceVsRevenueData = () => {
    const allProducts: any[] = []
    
    // 创建segment到颜色的映射（基于排序后位置的颜色）
    const segmentColorMap: Record<string, string> = {}
    sortedSegmentData.forEach((segmentData) => {
      segmentColorMap[segmentData.segment] = segmentData.color
    })
    
    segmentNames.forEach((segment) => {
      const products = data.topProducts.segments[segment] || []
      products.forEach(product => {
        allProducts.push({
          ...product,
          segment: segment,
          color: segmentColorMap[segment] || getChartColor(0), // 使用统一颜色作为fallback
          x: product.price || 0,
          y: product.revenue || 0
        })
      })
    })
    
    return allProducts
  }



  // 获取当前选中segment的top产品
  const getTopProductsForSegment = (segment: string) => {
    return data.topProducts.segments[segment] || []
  }

  const handleProductClick = (product: any) => {
    openPanel(
      [product],
      product.title || product.name || "Product Details",
      `Product from ${product.brand || 'Unknown Brand'}`,
      { brand: true, category: true, priceRange: true, packSize: true }
    )
  }

  const handleSegmentClick = (segmentData: any) => {
    const products = productLists.bySegment[segmentData.segment] || []
    openPanel(
      products,
      `${segmentData.segment} Products`,
      `All products in ${segmentData.segment} segment`,
      { brand: true, category: false, priceRange: true, packSize: true }
    )
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📊 Product Analysis</h2>

      {/* Segment Overview */}
      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">{productType} - Top Segments by Revenue</h3>
        <div className="mb-4 p-3 bg-blue-50 border-l-4 border-blue-400 rounded">
          <p className="text-sm text-blue-700">
            <strong>Top 3:</strong> {sortedSegmentData.slice(0, 3).map((segmentData, i) => 
              `${i + 1}. ${segmentData.segment} - $${(segmentData.revenue / 1000000).toFixed(1)}M`
            ).join(' • ')}
          </p>
        </div>
        
        <Card className="p-6 bg-gray-50">
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={sortedSegmentData}>
                <CartesianGrid strokeDasharray="3,3" />
                <XAxis 
                  dataKey="segment" 
                  angle={-45}
                  textAnchor="end"
                  height={100}
                  fontSize={12}
                />
                <YAxis 
                  label={{ value: 'Revenue ($)', angle: -90, position: 'insideLeft' }}
                  tickFormatter={(value) => `$${(value / 1000000).toFixed(1)}M`}
                />
                <Tooltip 
                  formatter={(value: any, name: string) => {
                    if (name === 'revenue') return [`$${(value / 1000000).toFixed(2)}M`, 'Revenue']
                    return [value, name]
                  }}
                  labelFormatter={(label) => `Segment: ${label}`}
                />
                <Bar 
                  dataKey="revenue" 
                  onClick={handleSegmentClick}
                  cursor="pointer"
                >
                  {sortedSegmentData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>

      {/* Segment Selection */}
      <div className="mb-6">
        <h3 className="text-xl font-semibold mb-4">Top Products by Segment</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {sortedSegmentData.map((segmentData, index) => (
            <Button
              key={segmentData.segment}
              variant={activeSegment === segmentData.segment ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedSegment(segmentData.segment)}
              className="text-xs"
              style={{
                backgroundColor: activeSegment === segmentData.segment ? segmentData.color : 'transparent',
                borderColor: segmentData.color,
                color: activeSegment === segmentData.segment ? 'white' : segmentData.color
              }}
            >
              {segmentData.segment} ({segmentData.productCount || 0})
            </Button>
          ))}
        </div>
      </div>

      {/* Top Products Table */}
      <Card className="p-6 bg-gray-50">
        <h4 className="text-lg font-medium mb-4">
          Top 20 {activeSegment} (by Total Revenue)
        </h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b">
                <th className="text-left p-2">Rank</th>
                <th className="text-left p-2">Product</th>
                <th className="text-left p-2">Brand</th>
                <th className="text-right p-2">Price</th>
                <th className="text-right p-2">Revenue</th>
                <th className="text-right p-2">Volume</th>
              </tr>
            </thead>
            <tbody>
              {getTopProductsForSegment(activeSegment).map((product, index) => (
                <tr 
                  key={index} 
                  className="border-b hover:bg-white cursor-pointer"
                  onClick={() => handleProductClick(product)}
                >
                  <td className="p-2 font-medium">#{index + 1}</td>
                  <td className="p-2">
                    <div className="font-medium text-blue-600 hover:text-blue-800">
                      {product.title?.length > 60 ? `${product.title.slice(0, 60)}...` : product.title}
                    </div>
                  </td>
                  <td className="p-2">{product.brand}</td>
                  <td className="p-2 text-right">${product.price?.toFixed(2) || '0.00'}</td>
                  <td className="p-2 text-right font-medium">
                    ${(product.revenue / 1000).toFixed(0)}K
                  </td>
                  <td className="p-2 text-right">{product.volume?.toLocaleString() || '0'}</td>
                </tr>
              ))}
            </tbody>
          </table>
          
          {getTopProductsForSegment(activeSegment).length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No products found for this segment
            </div>
          )}
        </div>
      </Card>

      {/* Price vs Revenue Scatter Plot */}
      <div className="mt-8">
        <h3 className="text-xl font-semibold mb-4">Price vs Revenue Analysis</h3>
        <Card className="p-6 bg-gray-50">
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
                  label={{ value: 'Revenue ($)', angle: -90, position: 'insideLeft' }}
                  tickFormatter={(value) => `$${(value / 1000).toFixed(0)}K`}
                />
                <Tooltip 
                  formatter={(value: any, name: string) => {
                    if (name === 'Revenue') return [`$${(value / 1000).toFixed(0)}K`, 'Revenue']
                    if (name === 'Price') return [`$${value}`, 'Price']
                    return [value, name]
                  }}
                  labelFormatter={() => ''}
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0].payload
                      return (
                        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
                          <p className="font-medium">{data.title?.length > 40 ? `${data.title.slice(0, 40)}...` : data.title}</p>
                          <p className="text-blue-600">Price: ${data.price?.toFixed(2)}</p>
                          <p className="text-green-600">Revenue: ${(data.revenue / 1000).toFixed(0)}K</p>
                          <p className="text-gray-600">Segment: {data.segment}</p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                {sortedSegmentData.map((segmentData, index) => (
                  <Scatter
                    key={segmentData.segment}
                    name={segmentData.segment}
                    data={getPriceVsRevenueData().filter(p => p.segment === segmentData.segment)}
                    fill={segmentData.color}
                  />
                ))}
                <Legend />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </Card>
      </div>
    </section>
  )
}
