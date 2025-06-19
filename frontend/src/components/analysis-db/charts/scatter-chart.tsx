"use client"

import {
  ScatterChart as ReChartsScatter,
  Scatter,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ZAxis,
} from "recharts"
import type { PriceType } from "@/components/analysis-db/shared/price-type-selector"
import type { MetricType } from "@/components/analysis-db/shared/metric-type-selector"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"

interface ScatterChartProps {
  dimmerData: {
    x: number
    y: number
    name: string
    brand: string
    volume: number
    revenue: number
    url?: string
    category: string
  }[]
  switchData: {
    x: number
    y: number
    name: string
    brand: string
    volume: number
    revenue: number
    url?: string
    category: string
  }[]
  xAxisLabel?: string
  yAxisLabel?: string
  priceType?: PriceType
  metricType?: MetricType
}

export function ScatterChart({ 
  dimmerData, 
  switchData, 
  xAxisLabel, 
  yAxisLabel, 
  priceType = "sku",
  metricType = "revenue"
}: ScatterChartProps) {
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

  const brandColors = {
    Kasa: "rgb(141,211,199)",
    Leviton: "#9B59B6",
    Lutron: "#E67E22",
    GE: "#3498DB",
    ELEGRP: "rgb(128,177,211)",
    BESTTEN: "rgb(253,180,98)",
    "ENERLITES Store": "rgb(179,222,105)",
    Amazon: "rgb(252,205,229)",
    Other: "#D3D3D3",
    TREATLIFE: "#FF6B6B",
    "TP-Link": "#4ECDC4",
  }

  const { openPanel } = useProductPanel()
  
  const handleDotClick = (data: any) => {
    if (data) {
      const product = {
        id: data.name,
        name: data.name,
        brand: data.brand,
        price: data.x,
        unitPrice: data.x,
        revenue: data.revenue,
        volume: data.volume,
        url: data.url || '',
        category: data.category
      }
      
      openPanel(
        [product],
        `Product Details`,
        `${data.name} • ${data.brand}`,
        { brand: false, category: false, priceRange: false, packSize: false }
      )
    }
  }

  const renderScatter = (data: any[], name: string, fill: string) => {
    return <Scatter 
      name={name} 
      data={data} 
      fill={fill} 
      shape="circle" 
      legendType="circle" 
      isAnimationActive={false}
      onClick={handleDotClick}
      style={{ cursor: 'pointer' }}
    />
  }

  // Group data by brand for better visualization
  const dimmerByBrand: Record<string, any[]> = {}
  const switchByBrand: Record<string, any[]> = {}

  dimmerData.forEach((item) => {
    if (!dimmerByBrand[item.brand]) {
      dimmerByBrand[item.brand] = []
    }
    dimmerByBrand[item.brand].push(item)
  })

  switchData.forEach((item) => {
    if (!switchByBrand[item.brand]) {
      switchByBrand[item.brand] = []
    }
    switchByBrand[item.brand].push(item)
  })

  const metricLabel = metricType === "revenue" ? "Revenue" : "Volume"
  const metricFormatter = metricType === "revenue" 
    ? (value: number) => `$${value.toLocaleString()}`
    : (value: number) => `${value.toLocaleString()}`

  return (
    <div className="flex flex-col h-full">
      <h3 className="text-center text-lg font-medium mb-2">
        Top 20 Products by {metricLabel}: {priceType === "sku" ? "SKU" : "Unit"} Price vs {metricLabel} Analysis
      </h3>

      <div className="flex-1">
        <h4 className="text-center text-base font-medium mb-1">🔆 Dimmer Switches - Price vs {metricLabel}</h4>
        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <ReChartsScatter
              margin={{
                top: 20,
                right: 30,
                left: 30,
                bottom: 20,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="x"
                name="Price"
                tickFormatter={(value) => `$${Number(value).toFixed(2)}`}
                label={{ value: xAxisLabel, position: "insideBottom", offset: 0 }}
                domain={["auto", "auto"]}
                height={50}
              />
              <YAxis
                type="number"
                dataKey="y"
                name={metricLabel}
                tickFormatter={metricFormatter}
                label={{ value: yAxisLabel, angle: -90, position: "insideLeft", offset: -5 }}
                width={90}
              />
              <ZAxis range={[100, 101]} />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                formatter={(value, name, props) => {
                  if (name === "Price") return `$${Number(value).toFixed(2)}`
                  if (name === metricLabel) return metricFormatter(Number(value))
                  return value
                }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    const brandColor = brandColors[data.brand as keyof typeof brandColors] || "#D3D3D3"
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
                          {data.name}
                        </p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Brand: {data.brand}</p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Category: {data.category}</p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Price: ${data.x.toFixed(2)}</p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Revenue: ${data.revenue.toLocaleString()}</p>
                        <p style={{ margin: '3px 0 0 0', color: '#333' }}>Volume: {data.volume.toLocaleString()}</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend verticalAlign="bottom" height={20} iconSize={10} />
              {Object.entries(dimmerByBrand).map(([brand, data]) =>
                renderScatter(data, brand, brandColors[brand as keyof typeof brandColors] || "#D3D3D3"),
              )}
            </ReChartsScatter>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="flex-1 mt-4">
        <h4 className="text-center text-base font-medium mb-1">💡 Light Switches - Price vs {metricLabel}</h4>
        <div className="h-[350px]">
          <ResponsiveContainer width="100%" height="100%">
            <ReChartsScatter
              margin={{
                top: 20,
                right: 30,
                left: 30,
                bottom: 20,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis
                type="number"
                dataKey="x"
                name="Price"
                tickFormatter={(value) => `$${Number(value).toFixed(2)}`}
                label={{ value: xAxisLabel, position: "insideBottom", offset: 0 }}
                domain={["auto", "auto"]}
                height={50}
              />
              <YAxis
                type="number"
                dataKey="y"
                name={metricLabel}
                tickFormatter={metricFormatter}
                label={{ value: yAxisLabel, angle: -90, position: "insideLeft", offset: -5 }}
                width={90}
              />
              <ZAxis range={[100, 101]} />
              <Tooltip
                cursor={{ strokeDasharray: "3 3" }}
                formatter={(value, name, props) => {
                  if (name === "Price") return `$${Number(value).toFixed(2)}`
                  if (name === metricLabel) return metricFormatter(Number(value))
                  return value
                }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload
                    const brandColor = brandColors[data.brand as keyof typeof brandColors] || "#D3D3D3"
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
                          {data.name}
                        </p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Brand: {data.brand}</p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Category: {data.category}</p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Price: ${data.x.toFixed(2)}</p>
                        <p style={{ margin: '3px 0', color: '#333' }}>Revenue: ${data.revenue.toLocaleString()}</p>
                        <p style={{ margin: '3px 0 0 0', color: '#333' }}>Volume: {data.volume.toLocaleString()}</p>
                      </div>
                    )
                  }
                  return null
                }}
              />
              <Legend verticalAlign="bottom" height={20} iconSize={10} />
              {Object.entries(switchByBrand).map(([brand, data]) =>
                renderScatter(data, brand, brandColors[brand as keyof typeof brandColors] || "#D3D3D3"),
              )}
            </ReChartsScatter>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
