"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { CustomerLike } from '@/components/analysis-db/data/review-insights'

interface CustomerLikesBarProps {
  data: CustomerLike[]
}

  const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-800">{data.feature}</p>
        <p className="text-sm text-gray-600">Category: {data.category}</p>
        <p className="text-sm text-green-600">Positive Mentions: {data.frequency}</p>
        <p className="text-sm text-blue-600">Satisfaction: {data.satisfactionLevel}</p>
      </div>
    )
  }
  return null
}

export function CustomerLikesBar({ data }: CustomerLikesBarProps) {
  const handleBarClick = (data: any) => {
    if (data && data.feature) {
      // For now, just log the click - this could be enhanced to show specific reviews
      console.log('Customer likes bar clicked:', data.feature)
    }
  }
  
  // 根据满意度级别分配颜色
  const getBarColor = (satisfactionLevel: string) => {
    switch (satisfactionLevel) {
      case 'High': return '#22c55e'      // 绿色
      case 'Medium': return '#eab308'    // 黄色  
      case 'Low': return '#94a3b8'       // 灰色
      default: return '#94a3b8'
    }
  }

  // 按频次降序排序
  const sortedData = [...data].sort((a, b) => b.frequency - a.frequency)

  return (
    <div className="w-full h-96">
      <div className="flex items-center justify-center mb-4 space-x-6">
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-green-500 rounded"></div>
          <span className="text-sm text-gray-600">High Satisfaction</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-yellow-500 rounded"></div>
          <span className="text-sm text-gray-600">Medium Satisfaction</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 bg-gray-400 rounded"></div>
          <span className="text-sm text-gray-600">Low Satisfaction</span>
        </div>
      </div>
      
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={sortedData}
          margin={{
            top: 20,
            right: 30,
            left: 20,
            bottom: 60,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            dataKey="feature"
            axisLine={{ stroke: '#9ca3af' }}
            tickLine={{ stroke: '#9ca3af' }}
            tick={{ fill: '#6b7280', fontSize: 11 }}
            angle={-45}
            textAnchor="end"
            height={80}
          />
          <YAxis
            axisLine={{ stroke: '#9ca3af' }}
            tickLine={{ stroke: '#9ca3af' }}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ 
              value: 'Positive Mention Count', 
              angle: -90, 
              position: 'left',
              offset: -5,
              style: { textAnchor: 'middle', fill: '#6b7280', fontSize: '12px' }
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Bar 
            dataKey="frequency" 
            radius={[4, 4, 0, 0]}
            onClick={handleBarClick}
            style={{ cursor: 'pointer' }}
          >
            {sortedData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={getBarColor(entry.satisfactionLevel)} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
      
      {/* 数据标签显示 */}
      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
        {sortedData.slice(0, 4).map((item, index) => (
          <div key={index} className="bg-gray-50 p-3 rounded-lg">
            <div className="text-lg font-bold" style={{color: getBarColor(item.satisfactionLevel)}}>
              {item.frequency}
            </div>
            <div className="text-xs text-gray-600 truncate">{item.feature}</div>
          </div>
        ))}
      </div>
    </div>
  )
} 