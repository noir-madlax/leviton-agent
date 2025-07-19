"use client"

import React from 'react'
import { 
  AreaChart, 
  Area, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer 
} from 'recharts'
import { getChartColor } from '../shared/chart-colors'

interface StackedAreaChartProps {
  data: Array<{
    month: string
    [brandName: string]: string | number
  }>
  brands: string[]
  colors?: string[]
  yAxisLabel?: string
  onAreaClick?: (data: unknown) => void
}

export function StackedAreaChart({
  data,
  brands,
  colors,
  yAxisLabel = "Revenue ($)",
  onAreaClick,
}: StackedAreaChartProps) {
  
  // 生成颜色数组（灰色遮罩用于假数据）
  const chartColors = colors || brands.map((_, index) => {
    const originalColor = getChartColor(index)
    // 添加半透明灰色遮罩，使颜色变淡
    return `${originalColor}80` // 添加80的透明度（50%透明）
  })

  // 格式化数值
  const formatValue = (value: number) => {
    if (value >= 1000000) {
      return `$${(value / 1000000).toFixed(1)}M`
    } else if (value >= 1000) {
      return `$${(value / 1000).toFixed(0)}K`
    }
    return `$${value.toLocaleString()}`
  }

  // 自定义Tooltip
  const CustomTooltip = ({ active, payload, label }: {active?: boolean, payload?: any[], label?: string}) => {
    if (active && payload && payload.length) {
      const total = payload.reduce((sum: number, item: any) => sum + (item.value || 0), 0)
      
      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg min-w-[250px]">
          <p className="font-semibold text-gray-900 mb-2">{label}</p>
          <div className="space-y-1">
            {payload
              .sort((a: any, b: any) => (b.value || 0) - (a.value || 0))
              .map((item: any, index: number) => {
                const percentage = total > 0 ? ((item.value || 0) / total * 100) : 0
                return (
                  <div key={index} className="flex items-center justify-between gap-4">
                    <div className="flex items-center gap-2">
                      <div 
                        className="w-3 h-3 rounded" 
                        style={{ backgroundColor: item.color }}
                      />
                      <span className="text-sm text-gray-700">{item.dataKey}</span>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-gray-900">
                        {formatValue(item.value || 0)}
                      </div>
                      <div className="text-xs text-gray-600">
                        {percentage.toFixed(1)}%
                      </div>
                    </div>
                  </div>
                )
              })}
          </div>
          <div className="border-t mt-2 pt-2">
            <div className="flex justify-between items-center">
              <span className="text-sm font-medium text-gray-700">Total:</span>
              <span className="text-sm font-bold text-gray-900">
                {formatValue(total)}
              </span>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  const handleAreaClick = (data: unknown) => {
    if (onAreaClick) {
      onAreaClick(data)
    }
  }

  return (
    <div className="relative">
      {/* 假数据遮罩层 */}
      <div className="absolute inset-0 bg-gray-500 bg-opacity-20 z-10 rounded-lg pointer-events-none" />
      
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart
          data={data}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 20,
          }}
          onClick={handleAreaClick}
        >
        <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
        <XAxis
          dataKey="month"
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 12, fill: '#6b7280' }}
        />
        <YAxis
          tickFormatter={formatValue}
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11, fill: '#6b7280' }}
          label={{
            value: yAxisLabel,
            angle: -90,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fontSize: '12px', fill: '#666' }
          }}
        />
        <Tooltip content={<CustomTooltip />} />
        <Legend 
          verticalAlign="bottom"
          height={36}
          iconSize={12}
          wrapperStyle={{
            paddingTop: 20,
          }}
        />
        
        {brands.map((brand, index) => (
          <Area
            key={brand}
            type="monotone"
            dataKey={brand}
            stackId="1"
            stroke={chartColors[index % chartColors.length]}
            fill={chartColors[index % chartColors.length]}
            strokeWidth={1}
            style={{ cursor: 'pointer' }}
          />
        ))}
      </AreaChart>
    </ResponsiveContainer>
    </div>
  )
} 