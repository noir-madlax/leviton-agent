"use client"

import { useMemo, useState, useRef, useLayoutEffect, useEffect } from "react"
import type { PriceType } from "@/components/analysis-db/shared/price-type-selector"
import type { Product } from "@/components/analysis-db/types/analysis"
import { usePostHog } from 'posthog-js/react'
import { useAuth } from '@/contexts/auth-context'

interface ViolinChartProps {
  dimmerPrices: number[]
  switchPrices: number[]
  dimmerProducts: Product[]
  switchProducts: Product[]
  dimmerStats: {
    min: number
    q1: number
    median: number
    mean: number
    q3: number
    max: number
  }
  switchStats: {
    min: number
    q1: number
    median: number
    mean: number
    q3: number
    max: number
  }
  priceType?: PriceType
  onViolinClick?: (category: string, priceRange: { min: number; max: number }) => void
  productLists?: {
    byBrand: Record<string, Product[]>
    bySegment: Record<string, Product[]>
    byPackageSize: Record<string, Product[]>
  }
  category1Name?: string
  category2Name?: string
}

interface HoverState {
  x: number
  y: number
  price: number
  dimmerProducts: number
  switchProducts: number
  visible: boolean
  isDimmerHover?: boolean
  isSwitchHover?: boolean
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
  const minWidth = 0.5 // Small constant minimal width in pixels
  if (maxDensity === 0) return densityData.map(([x]) => [x, minWidth])
  return densityData.map(([x, y]) => [x, Math.max(minWidth, (y / maxDensity) * maxHalfWidth)])
}

// Simplified function to count products within a price range
function countProductsInRange(
  products: Product[],
  targetPrice: number,
  priceType: PriceType,
  tolerance: number
): number {
  if (!products) return 0
  return products.filter(product => {
    const price = priceType === 'unit' ? product.unitPrice : product.price
    if (price === null || price === undefined) return false
    return Math.abs(price - targetPrice) <= tolerance
  }).length
}

// Function to get density width at a specific price
function getDensityWidth(densityData: [number, number][], price: number): number {
  // Find the closest density point
  if (densityData.length === 0) return 0
  let closestPoint = densityData[0]
  let minDistance = Math.abs(densityData[0][0] - price)
  
  for (const point of densityData) {
    const distance = Math.abs(point[0] - price)
    if (distance < minDistance) {
      minDistance = distance
      closestPoint = point
    }
  }
  
  return closestPoint[1]
}

export function ViolinChart({
  dimmerPrices,
  switchPrices,
  dimmerProducts,
  switchProducts,
  dimmerStats,
  switchStats,
  priceType = "sku",
  onViolinClick,
  productLists: _productLists,
  category1Name = "Category A",
  category2Name = "Category B",
}: ViolinChartProps) {
  const posthog = usePostHog()
  const { user } = useAuth()
  const [hoverState, setHoverState] = useState<HoverState>({
    x: 0,
    y: 0,
    price: 0,
    dimmerProducts: 0,
    switchProducts: 0,
    visible: false,
  })
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  // 数据验证和默认值处理
  const safeStats = (stats: any) => ({
    min: !isNaN(stats?.min) ? stats.min : 0,
    q1: !isNaN(stats?.q1) ? stats.q1 : 0,
    median: !isNaN(stats?.median) ? stats.median : 0,
    mean: !isNaN(stats?.mean) ? stats.mean : 0,
    q3: !isNaN(stats?.q3) ? stats.q3 : 0,
    max: !isNaN(stats?.max) ? stats.max : 0,
  });

  const safeDimmerStats = safeStats(dimmerStats);
  const safeSwitchStats = safeStats(switchStats);
  
  // 价格数组验证
  const safeDimmerPrices = Array.isArray(dimmerPrices) ? dimmerPrices.filter(p => !isNaN(p) && p > 0) : [];
  const safeSwitchPrices = Array.isArray(switchPrices) ? switchPrices.filter(p => !isNaN(p) && p > 0) : [];

  // 如果没有有效数据，显示空状态
  if (safeDimmerPrices.length === 0 && safeSwitchPrices.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <div className="text-center text-gray-500">
          <div className="text-lg font-medium">No pricing data available</div>
          <div className="text-sm">Waiting for valid product data...</div>
        </div>
      </div>
    );
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

  const margin = { top: 40, right: 20, bottom: 60, left: 80 }
  const chartWidth = Math.max(0, dimensions.width - margin.left - margin.right - 320)
  const chartHeight = Math.max(0, dimensions.height - margin.top - margin.bottom)

  // 使用安全的统计数据计算最大价格
  const maxPrice = Math.max(
    safeDimmerStats.max || 0,
    safeSwitchStats.max || 0,
    100 // 最小默认值
  );
  
  const bandwidth = Math.max(1, maxPrice * 0.05);
  const steps = 50;

  const dimmerDensity = safeDimmerPrices.length > 0 ? 
    normalizeDensity(kde(safeDimmerPrices, bandwidth, 0, maxPrice, steps), chartWidth * 0.15) : [];
  const switchDensity = safeSwitchPrices.length > 0 ? 
    normalizeDensity(kde(safeSwitchPrices, bandwidth, 0, maxPrice, steps), chartWidth * 0.15) : [];

  const yAxisLabels = maxPrice > 0 ? 
    Array.from({ length: 6 }, (_, i) => Math.round((maxPrice / 5) * i)) : [0];
  
  const dimmerX = chartWidth * 0.3;
  const switchX = chartWidth * 0.7;

  const getDimmerWidth = (price: number) => getDensityWidth(dimmerDensity, price)
  const getSwitchWidth = (price: number) => getDensityWidth(switchDensity, price)

  const handleMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return
    
    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const svgY = event.clientY - rect.top
    
    if (svgX >= margin.left && svgX <= margin.left + chartWidth && svgY >= margin.top && svgY <= margin.top + chartHeight) {
      const price = priceFromY(svgY)
      
      const isDimmerHover = svgX >= dimmerX - chartWidth * 0.15 && svgX <= dimmerX + chartWidth * 0.15
      const isSwitchHover = svgX >= switchX - chartWidth * 0.15 && svgX <= switchX + chartWidth * 0.15
      
      const dimmerCount = countProductsInRange(dimmerProducts, price, priceType, maxPrice * 0.05)
      const switchCount = countProductsInRange(switchProducts, price, priceType, maxPrice * 0.05)
      
      setHoverState({
        x: svgX,
        y: svgY,
        price: price,
        dimmerProducts: dimmerCount,
        switchProducts: switchCount,
        visible: isDimmerHover || isSwitchHover,
        isDimmerHover: isDimmerHover,
        isSwitchHover: isSwitchHover,
      })
    } else {
      setHoverState(prev => ({ ...prev, visible: false, isDimmerHover: false, isSwitchHover: false }))
    }
  }

  const handleMouseLeave = () => {
    setHoverState(prev => ({ ...prev, visible: false }))
  }

  const handleClick = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current || !onViolinClick) return
    
    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const svgY = event.clientY - rect.top
    
    if (svgX >= margin.left && svgX <= margin.left + chartWidth && svgY >= margin.top && svgY <= margin.top + chartHeight) {
      const price = priceFromY(svgY)
      
      const isDimmerClick = svgX >= dimmerX - chartWidth * 0.15 && svgX <= dimmerX + chartWidth * 0.15
      const isSwitchClick = svgX >= switchX - chartWidth * 0.15 && svgX <= switchX + chartWidth * 0.15
      
      if (isDimmerClick || isSwitchClick) {
        const priceRange = {
          min: price - maxPrice * 0.05,
          max: price + maxPrice * 0.05
        }
        const category = isDimmerClick ? "Dimmer Switches" : "Light Switches"
        
        // PostHog 埋点：小提琴图点击
        posthog.capture('chart_interaction', {
          chart_type: 'violin',
          price_type: priceType,
          clicked_category: category,
          clicked_price: price,
          price_range: priceRange,
          category1_name: category1Name,
          category2_name: category2Name,
          user_id: user?.id,
          user_email: user?.email,
        })
        
        onViolinClick(category, priceRange)
      }
    }
  }
  
  const dimmerPath = (side: 'left' | 'right') => {
    if (dimmerDensity.length === 0) return "";
    const sign = side === 'left' ? -1 : 1;
    const points = dimmerDensity.map(([price, density]) => {
      const y = yScale(price);
      const x = sign * density;
      if (isNaN(x) || isNaN(y)) return "";
      return `L ${x},${y}`;
    }).filter(p => p !== "").join(" ");
    const startY = yScale(safeDimmerStats.min);
    if (isNaN(startY)) return "";
    return `M 0,${startY} ${points} Z`;
  }
  
  const switchPath = (side: 'left' | 'right') => {
    if (switchDensity.length === 0) return "";
    const sign = side === 'left' ? -1 : 1;
    const points = switchDensity.map(([price, density]) => {
      const y = yScale(price);
      const x = sign * density;
      if (isNaN(x) || isNaN(y)) return "";
      return `L ${x},${y}`;
    }).filter(p => p !== "").join(" ");
    const startY = yScale(safeSwitchStats.min);
    if (isNaN(startY)) return "";
    return `M 0,${startY} ${points} Z`;
  }

  const yScale = (price: number) => {
    if (isNaN(price) || maxPrice === 0) return margin.top + chartHeight;
    return margin.top + chartHeight - (price / maxPrice) * chartHeight;
  }
  
  const priceFromY = (y: number) => {
    if (maxPrice === 0) return 0;
    return ((margin.top + chartHeight - y) / chartHeight) * maxPrice;
  }

  if (chartWidth === 0 || chartHeight === 0) {
    return (
      <div className="h-full flex">
        <div className="flex-1 relative" ref={containerRef} />
        <StatsBox dimmerStats={safeDimmerStats} switchStats={safeSwitchStats} priceType={priceType} category1Name={category1Name} category2Name={category2Name} />
      </div>
    );
  }

  return (
    <div className="h-full flex">
      <div className="flex-1 relative" ref={containerRef}>
        <svg 
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="w-full h-full cursor-pointer"
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
        >
          {/* Background */}
          <rect x={margin.left} y={margin.top} width={chartWidth} height={chartHeight} fill="#f8fafc" />

          {/* Grid lines */}
          {yAxisLabels.map((y) => (
            <line
              key={y}
              x1={margin.left}
              y1={yScale(y)}
              x2={margin.left + chartWidth}
              y2={yScale(y)}
              stroke="#e2e8f0"
              strokeDasharray="2,2"
            />
          ))}

          {/* Y-axis */}
          <line x1={margin.left} y1={margin.top} x2={margin.left} y2={margin.top + chartHeight} stroke="#64748b" strokeWidth="1" />

          {/* Y-axis labels */}
          {yAxisLabels.map((y) => (
            <text
              key={y}
              x={margin.left - 5}
              y={yScale(y)}
              textAnchor="end"
              fontSize="12"
              fill="#64748b"
              dominantBaseline="middle"
            >
              ${y}
            </text>
          ))}

          {/* Y-axis title */}
          <text x={20} y={margin.top + chartHeight / 2} textAnchor="middle" fontSize="14" fill="#64748b" transform={`rotate(-90, 20, ${margin.top + chartHeight / 2})`}>
            Price (USD)
          </text>

          {/* X-axis */}
          <line x1={margin.left} y1={margin.top + chartHeight} x2={margin.left + chartWidth} y2={margin.top + chartHeight} stroke="#64748b" strokeWidth="1" />

          {/* Dimmer Switches Violin */}
          {safeDimmerPrices.length > 0 && (
            <g transform={`translate(${dimmerX}, 0)`}>
              <path d={dimmerPath('left')} fill="#FF6B6B" fillOpacity="0.7" stroke="#FF6B6B" strokeWidth="1" />
              <path d={dimmerPath('right')} fill="#FF6B6B" fillOpacity="0.7" stroke="#FF6B6B" strokeWidth="1" />
              <line x1={-getDimmerWidth(safeDimmerStats.median)} y1={yScale(safeDimmerStats.median)} x2={getDimmerWidth(safeDimmerStats.median)} y2={yScale(safeDimmerStats.median)} stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
              <line x1={-getDimmerWidth(safeDimmerStats.mean)} y1={yScale(safeDimmerStats.mean)} x2={getDimmerWidth(safeDimmerStats.mean)} y2={yScale(safeDimmerStats.mean)} stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
            </g>
          )}

          {/* Light Switches Violin */}
          {safeSwitchPrices.length > 0 && (
            <g transform={`translate(${switchX}, 0)`}>
              <path d={switchPath('left')} fill="#4ECDC4" fillOpacity="0.7" stroke="#4ECDC4" strokeWidth="1" />
              <path d={switchPath('right')} fill="#4ECDC4" fillOpacity="0.7" stroke="#4ECDC4" strokeWidth="1" />
              <line x1={-getSwitchWidth(safeSwitchStats.median)} y1={yScale(safeSwitchStats.median)} x2={getSwitchWidth(safeSwitchStats.median)} y2={yScale(safeSwitchStats.median)} stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
              <line x1={-getSwitchWidth(safeSwitchStats.mean)} y1={yScale(safeSwitchStats.mean)} x2={getSwitchWidth(safeSwitchStats.mean)} y2={yScale(safeSwitchStats.mean)} stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
            </g>
          )}

          {/* Crosshair */}
          {hoverState.visible && (
            <g>
              {hoverState.isDimmerHover && safeDimmerPrices.length > 0 && (
                <line x1={dimmerX - getDimmerWidth(hoverState.price)} y1={hoverState.y} x2={dimmerX + getDimmerWidth(hoverState.price)} y2={hoverState.y} stroke="#dc2626" strokeWidth="2" opacity="0.9" />
              )}
              {hoverState.isSwitchHover && safeSwitchPrices.length > 0 && (
                <line x1={switchX - getSwitchWidth(hoverState.price)} y1={hoverState.y} x2={switchX + getSwitchWidth(hoverState.price)} y2={hoverState.y} stroke="#0891b2" strokeWidth="2" opacity="0.9" />
              )}
            </g>
          )}

          {/* X-axis labels */}
          <text x={dimmerX} y={margin.top + chartHeight + 30} textAnchor="middle" fontSize="14" fill="#64748b">{category1Name}</text>
          <text x={switchX} y={margin.top + chartHeight + 30} textAnchor="middle" fontSize="14" fill="#64748b">{category2Name}</text>

          {/* Legend */}
          <g transform={`translate(${margin.left + 20}, ${margin.top})`}>
            <rect x="0" y="0" width="200" height="85" fill="white" fillOpacity="0.9" stroke="#e5e7eb" strokeWidth="1" rx="4"/>
            <rect x="10" y="10" width="15" height="15" fill="#FF6B6B" fillOpacity="0.7" />
            <text x="30" y="22" fontSize="11" fill="#374151">{category1Name.length > 15 ? category1Name.substring(0, 15) + '...' : category1Name}</text>
            <rect x="10" y="30" width="15" height="15" fill="#4ECDC4" fillOpacity="0.7" />
            <text x="30" y="42" fontSize="11" fill="#374151">{category2Name.length > 15 ? category2Name.substring(0, 15) + '...' : category2Name}</text>
            <line x1="10" y1="55" x2="25" y2="55" stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
            <text x="30" y="58" fontSize="11" fill="#374151">Median</text>
            <line x1="10" y1="70" x2="25" y2="70" stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
            <text x="30" y="73" fontSize="11" fill="#374151">Mean</text>
          </g>
        </svg>
        
        {/* Hover tooltip */}
        {hoverState.visible && (
          <div
            className="absolute bg-white border border-gray-300 rounded-md shadow-lg p-3 pointer-events-none z-10"
            style={{
              left: `${hoverState.x}px`,
              top: `${hoverState.y}px`,
              transform: 'translate(-50%, -100%)',
              marginTop: '-10px'
            }}
          >
            <div className="text-sm font-medium text-gray-800">Price: ${hoverState.price.toFixed(2)}</div>
            <div className="text-xs text-gray-600 mt-1">
              {hoverState.isDimmerHover && (
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-red-400 rounded-sm"></div>
                  {category1Name}: {hoverState.dimmerProducts} products
                </div>
              )}
              {hoverState.isSwitchHover && (
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-cyan-400 rounded-sm"></div>
                  {category2Name}: {hoverState.switchProducts} products
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      <StatsBox dimmerStats={safeDimmerStats} switchStats={safeSwitchStats} priceType={priceType} category1Name={category1Name} category2Name={category2Name} />
    </div>
  )
}

const StatsBox = ({ dimmerStats, switchStats, priceType, category1Name = "Category A", category2Name = "Category B" }: any) => {
  // 安全的统计数据显示
  const safeValue = (value: number) => isNaN(value) ? 0 : value;
  
  return (
    <div className="w-80 ml-4 bg-white border border-gray-200 rounded-md p-4">
      <div className="mb-4">
        <h4 className="font-medium text-sm mb-2" title={category1Name}>
          {category1Name.length > 20 ? category1Name.substring(0, 17) + '...' : category1Name} ({priceType === "sku" ? "Total Price (for a full pack)" : "Price per unit"}):
        </h4>
        <div className="text-xs space-y-1">
          <div>Min: ${safeValue(dimmerStats.min).toFixed(2)}</div>
          <div>Q1: ${safeValue(dimmerStats.q1).toFixed(2)}</div>
          <div>Median: ${safeValue(dimmerStats.median).toFixed(2)}</div>
          <div>Mean: ${safeValue(dimmerStats.mean).toFixed(2)}</div>
          <div>Q3: ${safeValue(dimmerStats.q3).toFixed(2)}</div>
          <div>Max: ${safeValue(dimmerStats.max).toFixed(2)}</div>
        </div>
      </div>
      <div>
        <h4 className="font-medium text-sm mb-2" title={category2Name}>
          {category2Name.length > 20 ? category2Name.substring(0, 17) + '...' : category2Name} ({priceType === "sku" ? "Total Price (for a full pack)" : "Price per unit"}):
        </h4>
        <div className="text-xs space-y-1">
          <div>Min: ${safeValue(switchStats.min).toFixed(2)}</div>
          <div>Q1: ${safeValue(switchStats.q1).toFixed(2)}</div>
          <div>Median: ${safeValue(switchStats.median).toFixed(2)}</div>
          <div>Mean: ${safeValue(switchStats.mean).toFixed(2)}</div>
          <div>Q3: ${safeValue(switchStats.q3).toFixed(2)}</div>
          <div>Max: ${safeValue(switchStats.max).toFixed(2)}</div>
        </div>
      </div>
    </div>
  );
};

