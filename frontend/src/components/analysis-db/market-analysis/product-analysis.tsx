"use client"

import { useState } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ScatterChart, Scatter, Cell } from 'recharts'
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"

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

  // 获取动态segment信息
  const segmentNames = data.segmentNames || []
  const segmentColors = data.segmentColors || ["#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4"]
  const segmentSummary = data.segmentSummary || {}
  
  // 如果没有数据，显示空状态
  if (!segmentNames.length) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📊 Product Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-gray-500 text-center">No product analysis data available</p>
        </Card>
      </section>
    )
  }

  // 设置默认选中的segment
  const activeSegment = selectedSegment || segmentNames[0]

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
    
    segmentNames.forEach((segment, index) => {
      const products = data.topProducts.segments[segment] || []
      products.forEach(product => {
        allProducts.push({
          ...product,
          segment: segment,
          color: segmentColors[index] || '#8884d8',
          x: product.price || 0,
          y: product.revenue || 0
        })
      })
    })
    
    return allProducts
  }

  // Segment汇总数据用于条形图
  const getSegmentSummaryData = () => {
    return segmentNames.map((segment, index) => {
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
        color: segmentColors[index] || '#8884d8'
      }
    })
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
            <strong>Top 3:</strong> {segmentNames.slice(0, 3).map((segment, i) => 
              `${i + 1}. ${segment} - ${segmentSummary[segment] ? 
                `$${(segmentSummary[segment].totalRevenue / 1000000).toFixed(1)}M` : '$0'}`
            ).join(' • ')}
          </p>
        </div>
        
        <Card className="p-6 bg-gray-50">
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={getSegmentSummaryData()}>
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
                  {getSegmentSummaryData().map((entry, index) => (
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
          {segmentNames.map((segment, index) => (
            <Button
              key={segment}
              variant={activeSegment === segment ? "default" : "outline"}
              size="sm"
              onClick={() => setSelectedSegment(segment)}
              className="text-xs"
              style={{
                backgroundColor: activeSegment === segment ? segmentColors[index] : 'transparent',
                borderColor: segmentColors[index],
                color: activeSegment === segment ? 'white' : segmentColors[index]
              }}
            >
              {segment} ({segmentSummary[segment]?.productCount || 0})
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
                      {product.title?.slice(0, 60)}...
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
                          <p className="font-medium">{data.title?.slice(0, 40)}...</p>
                          <p className="text-blue-600">Price: ${data.price?.toFixed(2)}</p>
                          <p className="text-green-600">Revenue: ${(data.revenue / 1000).toFixed(0)}K</p>
                          <p className="text-gray-600">Segment: {data.segment}</p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
                {segmentNames.map((segment, index) => (
                  <Scatter
                    key={segment}
                    name={segment}
                    data={getPriceVsRevenueData().filter(p => p.segment === segment)}
                    fill={segmentColors[index]}
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
