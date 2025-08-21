'use client'

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
import { ChartContainer } from '../../shared/components/chart-container'
import { useSalesTrendData } from '../hooks/use-sales-trend-data'
import { transformSalesTrendData } from '../utils/data-transformer'
import { getChartColor } from '../../shared/utils/chart-colors'
import { formatMetricValue } from '../../shared/utils/number-formatter'
import type { SalesTrendChartProps, SalesTrendData } from '../types/sales-trend.types'

export function SalesTrendChart({ 
  projectId, 
  filters, 
  metricType = 'revenue',
  dateRange,
  onAreaClick,
  data: preloadedData
}: SalesTrendChartProps & { data?: SalesTrendData }) {
  const { data: fetchedData, loading, error } = useSalesTrendData(projectId, filters, dateRange, !preloadedData)
  
  const data = preloadedData || fetchedData
  
  if (loading && !preloadedData) {
    return (
      <ChartContainer 
        title=""
        loading={true}
        error={null}
      />
    )
  }

  if (error) {
    return (
      <ChartContainer 
        title=""
        loading={false}
        error={error}
      />
    )
  }

  // 检查是否有数据
  if (!data || !data.trend_data || data.trend_data.length === 0) {
    return (
      <ChartContainer title="">
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <p className="text-lg font-medium">No sales trend data available</p>
            <p className="text-sm mt-2">
              Try adjusting your filters or date range to see more data.
            </p>
          </div>
        </div>
      </ChartContainer>
    )
  }

  const chartData = transformSalesTrendData(data.trend_data, metricType)
  const colors = data.brands.map((_, index) => getChartColor(index))

  // 自定义Tooltip
  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { color: string; dataKey: string; value: number }[]; label?: string }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-gray-50 p-4  shadow-lg">
          <p className="font-medium text-gray-800 mb-2">{label}</p>
          {payload
            .sort((a, b) => a.value - b.value)
            .map((entry, index) => (
              <div key={index} className="flex items-center gap-2 text-sm">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: entry.color }}
                />
                <span className="text-gray-600">{entry.dataKey}:</span>
                <span className="font-medium text-gray-800">
                  {formatMetricValue(entry.value, metricType)}
                </span>
              </div>
            ))}
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

  const yAxisLabel = metricType === 'revenue' ? 'Revenue ($)' : 'Volume (Units)'

  return (
    <ChartContainer title="">
      <div className="h-[500px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={chartData}
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
              tickFormatter={(value) => formatMetricValue(value, metricType)}
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
            
            {data.brands.map((brand, index) => (
              <Area
                key={brand}
                type="monotone"
                dataKey={brand}
                stackId="1"
                stroke={colors[index % colors.length]}
                fill={colors[index % colors.length]}
                strokeWidth={1}
                style={{ cursor: 'pointer' }}
              />
            ))}
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </ChartContainer>
  )
} 