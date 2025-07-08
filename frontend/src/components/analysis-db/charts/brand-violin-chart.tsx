"use client"

import React, { useState, useEffect, useRef, useMemo } from 'react'
import { PriceType } from '../shared/price-type-selector'
import { getChartColor } from '../shared/chart-colors'

interface BrandViolinChartProps {
  brands: {
    name: string
    skuPrices: number[]
    unitPrices: number[]
  }[]
  priceType: PriceType
  category: string
  onViolinClick?: (brand: string, category: string) => void
}

interface HoverState {
  x: number
  y: number
  price: number
  brand: string
  products: number
  visible: boolean
}

// KDE function - 采用MultiSegmentViolinChart的实现
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

// Function to normalize density values - 采用MultiSegmentViolinChart的实现
function normalizeDensity(densityData: [number, number][], maxHalfWidth: number): [number, number][] {
  const maxDensity = Math.max(...densityData.map((d) => d[1]))
  const minWidth = 0.5
  if (maxDensity === 0) return densityData.map(([x]) => [x, minWidth])
  return densityData.map(([x, y]) => [x, Math.max(minWidth, (y / maxDensity) * maxHalfWidth)])
}

// Clean brand name to remove invisible characters
function cleanBrandName(brand: string): string {
  return brand.replace(/[\u200B-\u200D\uFEFF\u202C\u202D\u2066-\u2069]/g, '').trim()
}

export function BrandViolinChart({ brands, priceType, category, onViolinClick }: BrandViolinChartProps) {
  const [hoverState, setHoverState] = useState<HoverState>({
    x: 0,
    y: 0,
    price: 0,
    brand: '',
    products: 0,
    visible: false,
  })
  const containerRef = useRef<HTMLDivElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

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

  // 数据验证和过滤
  const validBrands = brands.filter(brand => {
    const prices = priceType === "sku" ? brand.skuPrices : brand.unitPrices
    return prices && prices.length > 0
  }).slice(0, 8) // 限制显示最多8个品牌

  const margin = { top: 40, right: 20, bottom: 80, left: 80 }
  const chartWidth = Math.max(0, dimensions.width - margin.left - margin.right)
  const chartHeight = Math.max(0, dimensions.height - margin.top - margin.bottom)

  // 计算全局价格范围
  const allPrices = validBrands.flatMap(brand => 
    priceType === "sku" ? brand.skuPrices : brand.unitPrices
  )
  const globalMin = Math.min(...allPrices)
  const globalMax = Math.max(...allPrices)
  const bandwidth = Math.max(1, (globalMax - globalMin) * 0.05)
  const steps = 50

  // 使用全局颜色配置

  // 计算每个品牌的violin数据
  const violinData = useMemo(() => {
    const brandWidth = chartWidth / validBrands.length
    const maxHalfWidth = brandWidth * 0.35

    return validBrands.map((brand, index) => {
      const prices = priceType === "sku" ? brand.skuPrices : brand.unitPrices
      const sortedPrices = [...prices].sort((a, b) => a - b)
      const centerX = (index + 0.5) * brandWidth
      
      // 计算统计信息
      const stats = {
        min: sortedPrices[0],
        median: sortedPrices[Math.floor(sortedPrices.length / 2)],
        mean: prices.reduce((a, b) => a + b, 0) / prices.length,
        max: sortedPrices[sortedPrices.length - 1],
        count: prices.length
      }

      const density = normalizeDensity(
        kde(prices, bandwidth, globalMin, globalMax, steps), 
        maxHalfWidth
      )

      const cleanName = cleanBrandName(brand.name)
      return {
        name: cleanName,
        prices,
        color: getChartColor(index), // 使用全局颜色配置
        stats,
        centerX,
        density,
        brandWidth
      }
    })
  }, [validBrands, priceType, chartWidth, globalMin, globalMax, bandwidth])

  if (validBrands.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="text-lg font-medium">No pricing data available</div>
          <div className="text-sm">Waiting for valid brand data...</div>
        </div>
      </div>
    )
  }

  const yScale = (price: number) => {
    if (globalMax <= globalMin) return chartHeight / 2
    return chartHeight - ((price - globalMin) / (globalMax - globalMin)) * chartHeight
  }

  const priceFromY = (y: number) => {
    return globalMin + ((chartHeight - y) / chartHeight) * (globalMax - globalMin)
  }

  // Y轴标签 - 修复key重复问题
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
    
    // 找到鼠标位置对应的品牌
    const brandIndex = Math.floor(mouseX / (chartWidth / validBrands.length))
    const targetBrand = violinData[brandIndex]
    
    if (targetBrand) {
      setHoverState({
        x: event.clientX,
        y: event.clientY,
        price,
        brand: targetBrand.name,
        products: targetBrand.stats.count,
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
    
    const brandIndex = Math.floor(mouseX / (chartWidth / validBrands.length))
    const targetBrand = violinData[brandIndex]
    
    if (targetBrand) {
      onViolinClick(targetBrand.name, category)
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
        {yAxisLabels.map((price, index) => {
          const y = margin.top + yScale(price)
          return (
            <g key={`grid-${index}-${price}`}>
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
                y={y}
                textAnchor="end"
                dominantBaseline="middle"
                fontSize="11"
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

        {/* Violin图形 */}
        {violinData.map((brand) => (
          <g key={brand.name} transform={`translate(${margin.left}, ${margin.top})`}>
            {/* Violin shape - 使用封闭路径 */}
            <path
              d={`${createViolinPath(brand.density, brand.centerX, 'left')} L${brand.centerX + (brand.density[0]?.[1] || 0)},${yScale(brand.density[0]?.[0] || 0)} ${createViolinPath(brand.density, brand.centerX, 'right')} Z`}
              fill={brand.color}
              fillOpacity={0.7}
              stroke={brand.color}
              strokeWidth="1"
            />

            {/* 中位线 - 添加固定宽度 */}
            <line
              x1={brand.centerX - 15}
              y1={yScale(brand.stats.median)}
              x2={brand.centerX + 15}
              y2={yScale(brand.stats.median)}
              stroke="#000"
              strokeWidth="2"
              strokeDasharray="5,5"
            />

            {/* 均值线 - 添加固定宽度 */}
            <line
              x1={brand.centerX - 12}
              y1={yScale(brand.stats.mean)}
              x2={brand.centerX + 12}
              y2={yScale(brand.stats.mean)}
              stroke="#000"
              strokeWidth="2"
              strokeDasharray="2,2"
            />

            {/* 品牌标签 */}
            <text
              x={brand.centerX}
              y={chartHeight + 20}
              textAnchor="middle"
              fontSize="11"
              fill="#666"
              transform={`rotate(-45, ${brand.centerX}, ${chartHeight + 20})`}
            >
              {brand.name}
            </text>
          </g>
        ))}

        {/* 图例 */}
        <g transform={`translate(${margin.left + chartWidth - 120}, ${margin.top + 10})`}>
          <rect x="0" y="0" width="110" height="40" fill="white" stroke="#ccc" strokeWidth="1" rx="3" />
          <line x1="10" y1="15" x2="25" y2="15" stroke="#000" strokeWidth="2" strokeDasharray="5,5" />
          <text x="30" y="18" fontSize="10" fill="#666">Median</text>
          <line x1="10" y1="28" x2="25" y2="28" stroke="#000" strokeWidth="2" strokeDasharray="2,2" />
          <text x="30" y="31" fontSize="10" fill="#666">Mean</text>
        </g>
      </svg>

      {/* 悬停提示 */}
      {hoverState.visible && (
        <div
          className="absolute bg-black text-white p-2 rounded shadow-lg text-sm pointer-events-none z-10"
          style={{
            left: hoverState.x + 10,
            top: hoverState.y - 10,
            transform: 'translateY(-100%)'
          }}
        >
          <div className="font-medium">{hoverState.brand}</div>
          <div>Price: ${hoverState.price.toFixed(2)}</div>
          <div>Products: {hoverState.products}</div>
        </div>
      )}
    </div>
  )
}
