'use client'

import React, { useState, useEffect } from 'react'
import { PieChart, Pie, Cell, Legend, ResponsiveContainer, Tooltip } from 'recharts'
import { Card } from "@/components/ui/card"
import type { Product } from "@/components/analysis-db/types/analysis"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"
import { databaseService } from "@/components/analysis-db/data/database-service"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"

interface PackagePreferenceData {
  packageDistribution: Array<{
    name: string;
    packSize: string;
    value: number;
    salesRevenue: number;
    count: number;
    percentage: number;
  }>;
  segmentDistributions: Record<string, Array<{
    packSize: string;
    name: string;
    value: number;
    salesRevenue: number;
    count: number;
    percentage: number;
  }>>;
  segmentNames: string[];
}


export function PackagePreferenceAnalysis({ 
  data: initialData, 
  productLists,
  projectId,
  categoryFilters,
  packagingTypeFilters,
  segmentFilters,
  extendFields
}: { 
  data: PackagePreferenceData
  productLists: {
    byBrand: Record<string, Product[]>
    bySegment: Record<string, Product[]>
    byPackageSize: Record<string, Product[]>
  }
  projectId?: string
  categoryFilters?: string[]
  packagingTypeFilters?: string[]
  segmentFilters?: string[]
  extendFields?: Record<string, any>
}) {
  const [metricType, setMetricType] = useState<'revenue' | 'count'>('revenue')
  const [data, setData] = useState<PackagePreferenceData>(initialData)
  const [loading, setLoading] = useState(false)

  // Effect to refetch data when metric type changes
  useEffect(() => {
    if (!projectId) return
    
    const fetchData = async () => {
      setLoading(true)
      try {
        const newData = await databaseService.getPackagePreferenceDataByProject(
          projectId,
          categoryFilters,
          packagingTypeFilters,
          segmentFilters,
          extendFields,
          metricType
        )
        setData(newData)
      } catch (error) {
        console.error('Error fetching package preference data:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchData()
  }, [metricType, projectId, categoryFilters, packagingTypeFilters, segmentFilters, extendFields])

  const colors = Array.from({ length: 20 }, (_, i) => getChartColor(i))
  const titleSuffix = metricType === "revenue" ? "Revenue" : "Product Count"

 

  if (!data.packageDistribution || data.packageDistribution.length === 0) {
    return (
      <section className="mb-10">
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📦 Package Preference Analysis</h2>
        <Card className="p-6 bg-gray-50">
          <p className="text-center text-gray-500">Package distribution data is not available.</p>
          <p className="text-center text-gray-400 text-sm mt-2">Waiting for package type data...</p>
        </Card>
      </section>
    )
  }

  // 生成饼图数据
  const chartData = data.packageDistribution.map((item, index) => {
    const value = metricType === "revenue" ? item.value : item.count;
    return {
      name: item.name || item.packSize,
      value: value,
      percentage: item.percentage, // 现在后端会根据metric_type返回正确的百分比
      color: colors[index % colors.length],
      revenue: item.salesRevenue || item.value,
      count: item.count
    }
  }).filter(item => item.value > 0) // 只显示有真实数据的项目

  // 计算总计
  const totalValue = chartData.reduce((sum, item) => sum + item.value, 0)
  const totalProducts = chartData.reduce((sum, item) => sum + item.count, 0)

  const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, name }: {
    cx: number; cy: number; midAngle: number; innerRadius: number; outerRadius: number; name: string;
  }) => {
    const RADIAN = Math.PI / 180
    const radius = innerRadius + (outerRadius - innerRadius) * 0.5
    const x = cx + radius * Math.cos(-midAngle * RADIAN)
    const y = cy + radius * Math.sin(-midAngle * RADIAN)

    // Find the correct percentage from our data (not Recharts calculated)
    const item = chartData.find(d => d.name === name)
    const correctPercentage = item ? item.percentage : 0

    // Only show label if percentage is significant enough
    if (correctPercentage < 5) return null

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
        {`${correctPercentage.toFixed(1)}%`}
      </text>
    )
  }

  const CustomTooltip = ({ active, payload }: { 
    active?: boolean; 
    payload?: Array<{
      payload: {
        name: string;
        value: number;
        percentage: number;
        revenue: number;
        count: number;
      }
    }> 
  }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload
      return (
        <div className="bg-white p-3 border border-gray-300 rounded shadow-lg">
          <p className="font-medium">{`Package Type: ${data.name}`}</p>
          <p className="text-blue-600">{`Revenue: $${data.revenue.toLocaleString()}`}</p>
          <p className="text-green-600">{`Product Count: ${data.count}`}</p>
          <p className="text-gray-600">{`Percentage: ${data.percentage.toFixed(1)}%`}</p>
        </div>
      )
    }
    return null
  }

  return (
    <section className="mb-10">
      <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">📦 Package Preference Analysis</h2>

      <ChartWithFilters
        chartId="package-preference"
        chartType="pie"
        projectId={projectId || ''}
        title={`Package Type Distribution by ${titleSuffix}`}
        projectFilters={{
          categories: categoryFilters || [],
          packaging_types: packagingTypeFilters || [],
          segments: segmentFilters || [],
          extend_fields: extendFields || {},
          asins: []
        }}
      >
       

        <div className="mb-8">
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-4">
          
            {metricType === "revenue" && (
              <p className="text-sm text-blue-700 mt-1">
                <strong>Total addressable market (TAM): </strong> ${totalValue.toLocaleString()} with {totalProducts} products 
                
                <p className="text-sm text-blue-700 mt-1">
                Approximated by the total Revenue of all products within this category in the current project within the selected time period
                </p>
                
              </p>
            )}
          </div>
          
         
        </div>
      
      {/* 单一饼图显示 */}
      <div className="bg-gray-50 p-6 rounded-lg">
        <h4 className="text-lg font-medium mb-4 text-center">
          📦 Package Type Distribution by {titleSuffix}
        </h4>
        <div className="h-[500px]">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={chartData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={renderCustomizedLabel}
                outerRadius={160}
                fill="#8884d8"
                dataKey="value"
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
              <Legend 
                verticalAlign="bottom" 
                height={36}
                formatter={(value) => {
                  const item = chartData.find(d => d.name === value)
                  return `${value} (${item?.percentage.toFixed(1)}%)`
                }}
              />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>
      </ChartWithFilters>
    </section>
  )
} 