"use client"

import { useMemo, useState, useRef, useEffect } from "react"
import type { PriceType } from "@/components/analysis-db/shared/price-type-selector"

interface SegmentData {
  name: string
  prices: number[]
  color: string
  productCount?: number
  stats: {
    min: number
    q1: number
    median: number
    mean: number
    q3: number
    max: number
  }
}

interface MultiSegmentViolinChartProps {
  segments: SegmentData[]
  priceType?: PriceType
  onViolinClick?: (segmentName: string) => void
}

interface HoverState {
  x: number
  y: number
  price: number
  segmentName: string
  productCount: number
  visible: boolean
}

// Function to create kernel density estimation
function kde(data: number[], bandwidth: number, min: number, max: number, steps: number): [number, number][] {
  const result: [number, number][] = []
  const range = max - min
  const step = range / steps

  for (let i = 0; i <= steps; i++) {
    const x = min + i * step
    let density = 0

    for (const point of data) {
      const z = (x - point) / bandwidth
      density += Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI)
    }

    density /= data.length * bandwidth
    result.push([x, density])
  }

  return result
}

// Function to normalize density values to a specific range
function normalizeDensity(densityData: [number, number][], maxHalfWidth: number): [number, number][] {
  const maxDensity = Math.max(...densityData.map((d) => d[1]))
  const minWidth = 0.5
  if (maxDensity === 0) return densityData.map(([x]) => [x, minWidth])
  return densityData.map(([x, y]) => [x, Math.max(minWidth, (y / maxDensity) * maxHalfWidth)])
}

export function MultiSegmentViolinChart({
  segments,
  priceType = "sku",
  onViolinClick
}: MultiSegmentViolinChartProps) {
  const [hoverState, setHoverState] = useState<HoverState>({
    x: 0,
    y: 0,
    price: 0,
    segmentName: '',
    productCount: 0,
    visible: false,
  })
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  // 数据验证
  const validSegments = segments.filter(segment => 
    segment.prices && segment.prices.length > 0
  )

  if (validSegments.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="text-lg font-medium">No pricing data available</div>
          <div className="text-sm">Waiting for valid segment data...</div>
        </div>
      </div>
    )
  }

  useEffect(() => {
    const updateDimensions = () => {
      if (containerRef.current) {
        const { width, height } = containerRef.current.getBoundingClientRect()
        setDimensions({ width, height })
      }
    }

    updateDimensions()
    window.addEventListener('resize', updateDimensions)
    return () => window.removeEventListener('resize', updateDimensions)
  }, [])

  const margin = { top: 40, right: 20, bottom: 80, left: 80 }
  const chartWidth = Math.max(0, dimensions.width - margin.left - margin.right)
  const chartHeight = Math.max(0, dimensions.height - margin.top - margin.bottom)

  // 计算全局价格范围
  const allPrices = validSegments.flatMap(s => s.prices)
  const globalMin = Math.min(...allPrices)
  const globalMax = Math.max(...allPrices)
  const bandwidth = Math.max(1, (globalMax - globalMin) * 0.05)
  const steps = 50

  // 计算每个segment的violin数据
  const violinData = useMemo(() => {
    const segmentWidth = chartWidth / validSegments.length
    const maxHalfWidth = segmentWidth * 0.35

    return validSegments.map((segment, index) => {
      const centerX = (index + 0.5) * segmentWidth
      const density = normalizeDensity(
        kde(segment.prices, bandwidth, globalMin, globalMax, steps), 
        maxHalfWidth
      )
      
      return {
        segment,
        centerX,
        density,
        segmentWidth
      }
    })
  }, [validSegments, chartWidth, globalMin, globalMax, bandwidth])

  const yScale = (price: number) => {
    if (globalMax <= globalMin) return chartHeight / 2
    return chartHeight - ((price - globalMin) / (globalMax - globalMin)) * chartHeight
  }

  const priceFromY = (y: number) => {
    return globalMin + ((chartHeight - y) / chartHeight) * (globalMax - globalMin)
  }

  // Y轴标签
  const yAxisLabels = globalMax > globalMin ? 
    Array.from({ length: 6 }, (_, i) => Math.round(globalMin + ((globalMax - globalMin) / 5) * i)) : 
    [0]

  const createViolinPath = (density: [number, number][], centerX: number, side: 'left' | 'right') => {
    if (density.length === 0) return ''
    
    const points = density.map(([price, width]) => {
      const y = yScale(price)
      const x = side === 'left' ? centerX - width : centerX + width
      return `${x},${y}`
    })

    return `M${points.join(' L')}`
  }

  const handleMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    const svgRect = event.currentTarget.getBoundingClientRect()
    const mouseX = event.clientX - svgRect.left - margin.left
    const mouseY = event.clientY - svgRect.top - margin.top

    if (mouseX < 0 || mouseX > chartWidth || mouseY < 0 || mouseY > chartHeight) {
      setHoverState(prev => ({ ...prev, visible: false }))
      return
    }

    const price = priceFromY(mouseY)
    
    // 找到鼠标位置对应的segment
    const segmentIndex = Math.floor(mouseX / (chartWidth / validSegments.length))
    const targetSegment = violinData[segmentIndex]
    
    if (targetSegment) {
      setHoverState({
        x: event.clientX,
        y: event.clientY,
        price,
        segmentName: targetSegment.segment.name,
        productCount: targetSegment.segment.productCount || targetSegment.segment.prices.length,
        visible: true
      })
    }
  }

  const handleMouseLeave = () => {
    setHoverState(prev => ({ ...prev, visible: false }))
  }

  const handleClick = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!onViolinClick) return
    
    const svgRect = event.currentTarget.getBoundingClientRect()
    const mouseX = event.clientX - svgRect.left - margin.left
    const mouseY = event.clientY - svgRect.top - margin.top
    
    const segmentIndex = Math.floor(mouseX / (chartWidth / validSegments.length))
    const targetSegment = violinData[segmentIndex]
    
    if (targetSegment) {
      onViolinClick(targetSegment.segment.name)
    }
  }

  return (
    <div ref={containerRef} className="w-full h-full relative">
      <svg
        width={dimensions.width}
        height={dimensions.height}
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
        className="cursor-pointer"
      >
        {/* Y轴 */}
        <line
          x1={margin.left}
          y1={margin.top}
          x2={margin.left}
          y2={margin.top + chartHeight}
          stroke="#000"
          strokeWidth="1"
        />

        {/* Y轴标签 */}
        {yAxisLabels.map((price) => {
          const y = margin.top + yScale(price)
          return (
            <g key={price}>
              <line
                x1={margin.left - 5}
                y1={y}
                x2={margin.left}
                y2={y}
                stroke="#000"
                strokeWidth="1"
              />
              <text
                x={margin.left - 10}
                y={y + 4}
                textAnchor="end"
                fontSize="12"
                fill="#666"
              >
                ${price}
              </text>
            </g>
          )
        })}

        {/* X轴 */}
        <line
          x1={margin.left}
          y1={margin.top + chartHeight}
          x2={margin.left + chartWidth}
          y2={margin.top + chartHeight}
          stroke="#000"
          strokeWidth="1"
        />

        {/* 绘制每个segment的violin */}
        {violinData.map(({ segment, centerX, density }, index) => (
          <g key={segment.name} transform={`translate(${margin.left}, ${margin.top})`}>
            {/* Violin shape */}
            <path
              d={`${createViolinPath(density, centerX, 'left')} L${centerX + density[0]?.[1] || 0},${yScale(density[0]?.[0] || 0)} ${createViolinPath(density, centerX, 'right')} Z`}
              fill={segment.color}
              fillOpacity={0.7}
              stroke={segment.color}
              strokeWidth="1"
            />

            {/* 中位线 */}
            <line
              x1={centerX - 15}
              y1={yScale(segment.stats.median)}
              x2={centerX + 15}
              y2={yScale(segment.stats.median)}
              stroke="#000"
              strokeWidth="2"
            />

            {/* X轴标签 */}
            <text
              x={centerX}
              y={chartHeight + 25}
              textAnchor="middle"
              fontSize="11"
              fill="#666"
              className="max-w-20"
            >
              {segment.name.length > 15 ? `${segment.name.substring(0, 12)}...` : segment.name}
            </text>
          </g>
        ))}

        {/* Y轴标题 */}
        <text
          x={20}
          y={margin.top + chartHeight / 2}
          textAnchor="middle"
          fontSize="14"
          fill="#666"
          transform={`rotate(-90, 20, ${margin.top + chartHeight / 2})`}
        >
          Price (USD)
        </text>
      </svg>

      {/* Hover tooltip */}
      {hoverState.visible && (
        <div
          className="absolute bg-white border border-gray-300 rounded shadow-lg p-3 pointer-events-none z-10"
          style={{
            left: hoverState.x + 10,
            top: hoverState.y - 10,
          }}
        >
          <div className="font-medium">{hoverState.segmentName}</div>
          <div className="text-blue-600">Price: ${hoverState.price.toFixed(2)}</div>
          <div className="text-gray-600">Products: {hoverState.productCount}</div>
        </div>
      )}
    </div>
  )
} 