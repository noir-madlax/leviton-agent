"use client"

import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from "recharts"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"

interface HorizontalBarChartProps {
  data: {
    name: string
    value: number
    brand: string
    price?: number
    url?: string
  }[]
  colors: Record<string, string>
  valueLabel?: string
  metricType?: "revenue" | "volume"
}

export function HorizontalBarChart({ data, colors, valueLabel, metricType = "revenue" }: HorizontalBarChartProps) {
  const { openPanel } = useProductPanel()
  
  const handleBarClick = (barData: any) => {
    if (barData && barData.activePayload) {
      const clickedData = barData.activePayload[0].payload
      
      // If there's a URL, open it in a new tab
      if (clickedData.url) {
        window.open(clickedData.url, '_blank', 'noopener,noreferrer')
      } else {
        // Otherwise, open the product panel
        const product = {
          id: clickedData.name,
          name: clickedData.name,
          brand: clickedData.brand,
          price: clickedData.price || 0,
          unitPrice: clickedData.price || 0,
          revenue: metricType === "revenue" ? clickedData.value : 0,
          volume: metricType === "volume" ? clickedData.value : 0,
          url: clickedData.url || '',
          category: "Product"
        }
        
        openPanel(
          [product],
          `Product Details`,
          `${clickedData.name}`,
          { brand: false, category: false, priceRange: false, packSize: false }
        )
      }
    }
  }
  
  const formatValue = (value: number) => {
    return metricType === "revenue" ? `$${value.toLocaleString()}` : value.toLocaleString()
  }

  // Function to lighten a color
  const lightenColor = (color: string, amount: number = 0.4) => {
    // Handle rgb() format
    if (color.startsWith('rgb(')) {
      const rgbMatch = color.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/)
      if (rgbMatch) {
        const r = parseInt(rgbMatch[1])
        const g = parseInt(rgbMatch[2])
        const b = parseInt(rgbMatch[3])
        
        const newR = Math.min(255, Math.floor(r + (255 - r) * amount))
        const newG = Math.min(255, Math.floor(g + (255 - g) * amount))
        const newB = Math.min(255, Math.floor(b + (255 - b) * amount))
        
        return `rgb(${newR}, ${newG}, ${newB})`
      }
    }
    
    // Handle hex format
    const hex = color.replace('#', '')
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    
    const newR = Math.min(255, Math.floor(r + (255 - r) * amount))
    const newG = Math.min(255, Math.floor(g + (255 - g) * amount))
    const newB = Math.min(255, Math.floor(b + (255 - b) * amount))
    
    return `#${newR.toString(16).padStart(2, '0')}${newG.toString(16).padStart(2, '0')}${newB.toString(16).padStart(2, '0')}`
  }

  return (
    <ResponsiveContainer width="100%" height="100%">
      <BarChart
        layout="vertical"
        data={data}
        margin={{
          top: 5,
          right: 30,
          left: 150,
          bottom: 5,
        }}
        onClick={handleBarClick}
        style={{ cursor: 'pointer' }}
      >
        <CartesianGrid strokeDasharray="3 3" horizontal={false} />
        <XAxis
          type="number"
          tickFormatter={formatValue}
          label={{
            value: valueLabel,
            position: "insideBottom",
            offset: -5,
          }}
        />
        <YAxis
          type="category"
          dataKey="name"
          width={150}
          tickFormatter={(value) => (value.length > 25 ? `${value.substring(0, 25)}...` : value)}
          tick={{ fontSize: 11 }}
        />
        <Tooltip
          content={({ active, payload, label }) => {
            if (active && payload && payload.length) {
              const item = payload[0].payload
              const brandColor = colors[item.brand] || colors.Other || "#D3D3D3"
              const lightColor = lightenColor(brandColor, 0.5)
              
              return (
                <div 
                  style={{ 
                    backgroundColor: lightColor, 
                    border: `2px solid ${brandColor}`, 
                    borderRadius: '6px',
                    padding: '12px',
                    boxShadow: '0 2px 8px rgba(0,0,0,0.15)',
                    width: '33vw',
                    maxWidth: '400px',
                    minWidth: '250px'
                  }}
                >
                  <p style={{ 
                    fontWeight: 'bold', 
                    margin: '0 0 6px 0', 
                    color: '#333',
                    wordWrap: 'break-word',
                    lineHeight: '1.4'
                  }}>
                    {label}
                  </p>
                  <p style={{ margin: '3px 0', color: '#333' }}>Brand: {item.brand}</p>
                  <p style={{ margin: '3px 0', color: '#333' }}>
                    {metricType === "revenue" ? "Revenue" : "Volume"}: {formatValue(Number(item.value))}
                  </p>
                  {item.price && (
                    <p style={{ margin: '3px 0 0 0', color: '#333' }}>Price: ${item.price.toFixed(2)}</p>
                  )}
                </div>
              )
            }
            return null
          }}
        />
        <Bar dataKey="value" radius={[0, 4, 4, 0]}>
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={colors[entry.brand] || colors.Other} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
