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

interface BarChartProps {
  data: ChartDataItem[]
  index: string
  categories: string[]
  colors?: string[]
  yAxisLabel?: string
  xAxisLabel?: string
  metricType?: "revenue" | "volume"
  onBarClick?: (data: unknown) => void
}

export function BarChart({
  data,
  index,
  categories,
  colors = ["#FF6B6B", "#4ECDC4"],
  yAxisLabel,
  xAxisLabel,
  metricType = "revenue",
  onBarClick,
}: BarChartProps) {
  const formatValue = (value: number) => {
    return metricType === "revenue" ? `$${value.toLocaleString()}` : value.toLocaleString()
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <ReChartsBar
        data={data}
        margin={{
          top: 20,
          right: 30,
          left: 90,
          bottom: 20,
        }}
        onClick={onBarClick}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis
          dataKey={index}
          angle={-45}
          textAnchor="end"
          tick={{ fontSize: 12 }}
          height={110} // Allocate a generous, fixed height for the entire X-axis block
          interval={0}
          label={{
            value: xAxisLabel,
            position: "bottom",
            offset: 10,
          }}
        />
        <YAxis
          tickFormatter={formatValue}
        />
        <Tooltip formatter={formatValue} />
        <Legend
          verticalAlign="bottom"
          iconSize={12}
          wrapperStyle={{
            paddingTop: 30, // Push legend down from X-axis
          }}
        />

        {/* Custom Y-axis label */}
        <text
          x={35}
          y={250}
          transform={`rotate(-90, 35, 250)`}
          textAnchor="middle"
          fontSize="18"
          fontWeight="500"
          fill="#374151"
        >
          {yAxisLabel}
        </text>
        {categories.map((category, index) => (
          <Bar 
            key={category} 
            dataKey={category} 
            fill={colors[index % colors.length]} 
            name={category}
            style={{ cursor: 'pointer' }}
          />
        ))}
      </ReChartsBar>
    </ResponsiveContainer>
  )
}
