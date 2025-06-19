"use client"

import { ScatterChart, Scatter, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from 'recharts'
import { PainPoint } from '@/components/analysis-db/data/review-insights'

interface PainPointsScatterProps {
  data: PainPoint[]
}

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
        <p className="font-semibold text-gray-800">{data.aspect}</p>
        <p className="text-sm text-gray-600">Category: {data.category}</p>
        <p className="text-sm text-blue-600">Severity: {data.severity.toFixed(1)}</p>
        <p className="text-sm text-red-600">Frequency: {data.frequency}</p>
        <p className="text-sm text-gray-500">Products Affected: {data.impactedProducts}</p>
      </div>
    )
  }
  return null
}

export function PainPointsScatter({ data }: PainPointsScatterProps) {
  const handleDotClick = (data: any) => {
    if (data && data.payload) {
      console.log('Pain point scatter clicked:', data.payload)
    }
  }
  
  // 根据类型分组数据，并添加颜色
  const processedData = data.map(item => ({
    ...item,
    x: item.severity,
    y: item.frequency,
    z: item.impactedProducts,
    fill: item.type === 'Physical' ? '#ef4444' : 
          item.type === 'Performance' ? '#f97316' : '#dc2626'
  }))

  const physicalData = processedData.filter(item => item.type === 'Physical')
  const performanceData = processedData.filter(item => item.type === 'Performance')  
  const usabilityData = processedData.filter(item => item.type === 'Usability')

  return (
    <div className="w-full h-96">
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart
          margin={{
            top: 20,
            right: 20,
            bottom: 60,
            left: 60,
          }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
          <XAxis 
            type="number" 
            dataKey="x" 
            name="Severity" 
            domain={[3, 5]}
            axisLine={{ stroke: '#9ca3af' }}
            tickLine={{ stroke: '#9ca3af' }}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ 
              value: 'Severity Level (1-5)', 
              position: 'bottom',
              offset: -40,
              style: { textAnchor: 'middle', fill: '#6b7280', fontSize: '12px' }
            }}
          />
          <YAxis 
            type="number" 
            dataKey="y" 
            name="Frequency"
            axisLine={{ stroke: '#9ca3af' }}
            tickLine={{ stroke: '#9ca3af' }}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            label={{ 
              value: 'Comment Volume', 
              angle: -90, 
              position: 'left',
              offset: -40,
              style: { textAnchor: 'middle', fill: '#6b7280', fontSize: '12px' }
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend 
            verticalAlign="top" 
            height={36}
            iconType="circle"
            wrapperStyle={{ paddingBottom: '20px' }}
          />
          
          <Scatter 
            name="Physical Issues" 
            data={physicalData} 
            fill="#ef4444"
            onClick={handleDotClick}
            style={{ cursor: 'pointer' }}
          />
          <Scatter 
            name="Performance Issues" 
            data={performanceData} 
            fill="#f97316"
            onClick={handleDotClick}
            style={{ cursor: 'pointer' }}
          />
          <Scatter 
            name="Usability Issues" 
            data={usabilityData} 
            fill="#dc2626"
            onClick={handleDotClick}
            style={{ cursor: 'pointer' }}
          />
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  )
} 