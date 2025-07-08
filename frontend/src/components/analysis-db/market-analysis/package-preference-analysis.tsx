'use client'

import React, { useState } from 'react'
import { PieChart, Pie, Cell, Legend, ResponsiveContainer, Tooltip } from 'recharts'
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
import { Card } from "@/components/ui/card"
import type { Product } from "@/components/analysis-db/types/analysis"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"

interface PackagePreferenceData {
  segmentDistributions: Record<string, Array<{
    packSize: string;
    count: number;
    percentage: number;
    salesVolume: number;
    salesRevenue: number;
  }>>;
  segmentNames: string[];
}

const MetricTypeSelector = ({ 
  onChange, 
  value 
}: { 
  onChange: (value: 'revenue' | 'volume') => void;
  value: 'revenue' | 'volume';
}) => {
  return (
    <div className="mb-4">
      <label className="block text-sm font-medium text-gray-700 mb-2">Metric Type:</label>
      <select 
        value={value} 
        onChange={(e) => onChange(e.target.value as 'revenue' | 'volume')}
        className="block w-48 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
      >
        <option value="revenue">Revenue</option>
        <option value="volume">Volume</option>
      </select>
    </div>
  )
}

export function PackagePreferenceAnalysis({ 
  data, 
  productLists 
}: { 
  data: PackagePreferenceData
  productLists: {
    byBrand: Record<string, Product[]>
    bySegment: Record<string, Product[]>
    byPackageSize: Record<string, Product[]>
  }
}) {
  const [metricType, setMetricType] = useState<'revenue' | 'volume'>('revenue')
  const { openPanel } = useProductPanel()

  const colors = Array.from({ length: 20 }, (_, i) => getChartColor(i))
  const titleSuffix = metricType === "revenue" ? "Revenue" : "Volume"

  // 检查是否有segments数据
  if (!data.segmentDistributions || !data.segmentNames || data.segmentNames.length === 0) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📦 Package Preference Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-center text-gray-500">Package distribution data is not available.</p>
          <p className="text-center text-gray-400 text-sm mt-2">Waiting for valid segment data...</p>
        </Card>
      </section>
    )
  }

  // 检查是否所有产品都是单包装
  const allSegmentsData = data.segmentNames.map(segmentName => data.segmentDistributions[segmentName] || [])
  const hasVariedPackaging = allSegmentsData.some(segmentData => 
    segmentData.length > 1 || (segmentData.length === 1 && segmentData[0].packSize !== "1")
  )
  
  // 计算总产品数
  const totalProducts = Object.values(productLists.bySegment).reduce((sum, products) => sum + products.length, 0)

  // 为每个segment生成图表数据
  const getSegmentChartData = (segmentName: string) => {
    if (!data.segmentDistributions || !data.segmentDistributions[segmentName]) {
      return []
    }
    
    return data.segmentDistributions[segmentName].map((item, index) => ({
      name: item.packSize,
      value: metricType === "revenue" ? item.salesRevenue || 0 : item.salesVolume,
      percentage: item.percentage,
      color: colors[index % colors.length]
    }))
  }

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percentage }: {
    cx: number; cy: number; midAngle: number; innerRadius: number; outerRadius: number; percentage: number;
  }) => {
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    // Only show label if percentage is significant enough
    if (percentage < 5) return null

    return (
      <text 
        x={x} 
        y={y} 
        fill="white" 
        textAnchor={x > cx ? 'start' : 'end'} 
        dominantBaseline="central"
        fontSize="12"
        fontWeight="bold"
      >
        {`${percentage.toFixed(1)}%`}
      </text>
    )
  }

  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: any[] }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-medium">{`Pack Size: ${data.name}`}</p>
          <p className="text-blue-600">{`${titleSuffix}: ${metricType === "revenue" ? `$${data.value.toLocaleString()}` : data.value.toLocaleString()}`}</p>
          <p className="text-gray-600">{`Percentage: ${data.percentage.toFixed(1)}%`}</p>
        </div>
      )
    }
    return null
  }

  const handlePieClick = (data: { name?: string }) => {
    if (data && data.name) {
      const packSize = data.name
      const products = productLists.byPackageSize[packSize] || []
      openPanel(
        products,
        `${packSize} Package`,
        `Products with ${packSize} packaging`,
        { brand: true, category: true, priceRange: true, packSize: false }
      )
    }
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📦 Package Preference Analysis</h2>

      <div className="mb-4">
        <MetricTypeSelector onChange={setMetricType} value={metricType} />
      </div>

      <div className="mb-8">
        <h3 className="text-xl font-semibold mb-4">Package Size Distribution by {titleSuffix}</h3>
        
        {/* 单包装提示信息 */}
        {!hasVariedPackaging && (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
            <div className="flex items-center">
              <div className="text-2xl mr-3">📦</div>
              <div>
                <h4 className="font-semibold text-blue-800">Uniform Single Packaging</h4>
                <p className="text-sm text-blue-700 mt-1">
                  All <strong>{totalProducts}</strong> products use single unit packaging across all segments.
                </p>
              </div>
            </div>
          </div>
        )}
        
        <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
          <p className="text-sm text-blue-700">
            <strong>Note:</strong> {metricType === "revenue" ? "Revenue shows total sales value for each package size." : "Volume shows total number of packages sold."}
          </p>
        </div>
      </div>
      
      {/* 按segment分开显示 - 动态渲染所有segments */}
      <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
        {data.segmentNames.map((segmentName, segmentIndex) => {
          const segmentData = getSegmentChartData(segmentName)
          if (segmentData.length === 0) return null
          
          const icons = ["🔆", "💡", "🔥", "⚡", "🌟", "🎯"]
          const icon = icons[segmentIndex % icons.length]
          
          return (
            <div key={segmentName} className="bg-gray-50 p-6 rounded-lg">
              <h4 className="text-lg font-medium mb-4 text-center">
                {icon} {segmentName} - Package Size by {titleSuffix}
              </h4>
              <div className="h-[400px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie
                      data={segmentData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={renderCustomizedLabel}
                      outerRadius={120}
                      fill="#8884d8"
                      dataKey="value"
                      onClick={handlePieClick}
                    >
                      {segmentData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                      ))}
                    </Pie>
                    <Tooltip content={<CustomTooltip />} />
                    <Legend 
                      verticalAlign="bottom" 
                      height={36}
                      formatter={(value) => {
                        const item = segmentData.find(d => d.name === value)
                        return `${value} (${item?.percentage.toFixed(1)}%)`
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
} 