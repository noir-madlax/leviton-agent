"use client"

import {
  BarChart as ReChartsBar,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from "recharts"
import type { ChartDataItem } from "../types/chart-data"
import { getChartColors } from "../shared/chart-colors"

interface BarChartProps {
  data: ChartDataItem[]
  index: string
  categories: string[]
  colors?: string[]
  yAxisLabel?: string
  metricType?: "revenue" | "volume"
  onBarClick?: (data: unknown) => void
}

export function BarChart({
  data,
  index,
  categories,
  colors = getChartColors(2),
  yAxisLabel,
  metricType = "revenue",
  onBarClick,
}: BarChartProps) {
  const formatValue = (value: number) => {
    return metricType === "revenue" ? `$${value.toLocaleString()}` : value.toLocaleString()
  }

  // 自定义Tooltip - 只显示有数据的segment信息
  const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: { value?: number; color?: string }[]; label?: string }) => {
    if (active && payload && payload.length && label) {
      // 找到当前悬停的品牌数据
      const brandData = data.find(item => item[index] === label)
      if (!brandData) return null

      // 过滤出有数据的segments
      const nonZeroSegments = categories
        .map((category, categoryIndex) => ({
          category,
          value: Number(brandData[category] || 0),
          color: colors[categoryIndex % colors.length]
        }))
        .filter(segment => segment.value > 0)

      // 如果没有数据，不显示tooltip
      if (nonZeroSegments.length === 0) return null

      return (
        <div 
          style={{ 
            backgroundColor: 'white', 
            border: '1px solid #ccc', 
            borderRadius: '6px',
            padding: '12px',
            boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
            maxWidth: '350px',
            minWidth: '200px'
          }}
        >
          <p style={{ 
            fontWeight: 'bold', 
            margin: '0 0 8px 0', 
            color: '#333',
            fontSize: '14px'
          }}>
            {label}
          </p>
          
          {/* 只显示有数据的segments */}
          {nonZeroSegments.map((segment) => (
            <div key={segment.category} style={{ 
              margin: '4px 0', 
              color: '#333', 
              display: 'flex', 
              alignItems: 'center',
              fontSize: '12px'
            }}>
              <div 
                style={{ 
                  width: '10px', 
                  height: '10px', 
                  backgroundColor: segment.color, 
                  marginRight: '8px',
                  borderRadius: '2px',
                  flexShrink: 0
                }} 
              />
              <span style={{ flex: 1 }}>
                {segment.category}: <strong>{formatValue(segment.value)}</strong>
              </span>
            </div>
          ))}
          
          {/* 显示总计 */}
          {nonZeroSegments.length > 1 && (
            <div style={{ 
              marginTop: '8px', 
              paddingTop: '6px', 
              borderTop: '1px solid #eee',
              fontSize: '12px',
              fontWeight: 'bold',
              color: '#333'
            }}>
              Total: {formatValue(nonZeroSegments.reduce((sum, seg) => sum + seg.value, 0))}
            </div>
          )}
        </div>
      )
    }
    return null
  }

  // 判断是否为单一类别（隐藏图例和简化布局）
  const isSingleCategory = categories.length === 1

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ReChartsBar
        data={data}
        margin={{
          top: 20,
          right: 20,
          left: 20,
          bottom: isSingleCategory ? 20 : 20,
        }}
        onClick={onBarClick}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey={index}
          angle={-45}
          textAnchor="end"
          tick={{ fontSize: 12 }}
          height={60}
          interval={0}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          tickFormatter={formatValue}
          axisLine={false}
          tickLine={false}
          tick={{ fontSize: 11 }}
          label={{
            value: yAxisLabel,
            angle: -90,
            offset: -10,
            position: 'insideLeft',
            style: { textAnchor: 'middle', fontSize: '12px', fill: '#666' }
          }}
        />
        <Tooltip content={<CustomTooltip />} />
        
        {/* 只在多类别时显示图例 */}
        {!isSingleCategory && (
          <Legend
            verticalAlign="bottom"
            iconSize={12}
            wrapperStyle={{
              paddingTop: 20,
            }}
          />
        )}

        {categories.map((category, index) => (
          <Bar 
            key={category} 
            dataKey={category} 
            fill={colors[index % colors.length]} 
            name={isSingleCategory ? "" : category}
            style={{ cursor: 'pointer' }}
            radius={[2, 2, 0, 0]}
            maxBarSize={120}
          />
        ))}
      </ReChartsBar>
    </ResponsiveContainer>
  )
}
