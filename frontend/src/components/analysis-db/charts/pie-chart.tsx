"use client"

import { PieChart as ReChartsPie, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import { getChartColors } from "../shared/chart-colors"
import { usePostHog } from 'posthog-js/react'
import { useAuth } from '@/contexts/auth-context'

interface PieChartProps {
  data: {
    name: string
    value: number
  }[]
  title?: string
  colors?: string[]
  annotation?: string
}

export function PieChart({ data, title, colors = getChartColors(2), annotation }: PieChartProps) {
  const posthog = usePostHog()
  const { user } = useAuth()
  
  const handleSliceClick = (data: any) => {
    // PostHog 埋点：饼图片段点击
    posthog.capture('chart_interaction', {
      chart_type: 'pie',
      chart_title: title || 'Pie Chart',
      clicked_data: data,
      user_id: user?.id,
      user_email: user?.email,
    })
    
    // Since pie charts are typically high-level category data, 
    // we'll just log the click for now - specific implementations 
    // can override this behavior
    console.log('Pie slice clicked:', data)
  }
  
  return (
    <ResponsiveContainer width="100%" height="100%">
      <ReChartsPie
        data={data}
        margin={{
          top: 20,
          right: 30,
          left: 30,
          bottom: 20,
        }}
      >
        <text x="50%" y="20" textAnchor="middle" dominantBaseline="middle" className="text-base font-medium">
          {title}
        </text>
        {annotation && (
          <text x="10%" y="10%" width={100} className="text-xs" style={{ fill: "#333", fontWeight: "500" }}>
            {annotation.split("\n").map((line, i) => (
              <tspan key={i} x="10%" dy={i === 0 ? 0 : 15}>
                {line}
              </tspan>
            ))}
          </text>
        )}
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          labelLine={false}
          outerRadius={80}
          fill="#8884d8"
          dataKey="value"
          label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
          onClick={handleSliceClick}
          style={{ cursor: 'pointer' }}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[index % colors.length]} />
          ))}
        </Pie>
        <Tooltip formatter={(value) => `$${Number(value).toLocaleString()}`} />
        <Legend />
      </ReChartsPie>
    </ResponsiveContainer>
  )
}
