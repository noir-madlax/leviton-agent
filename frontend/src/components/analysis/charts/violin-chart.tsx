"use client"

import { useMemo, useState, useRef, useLayoutEffect } from "react"
import type { PriceType } from "@/components/analysis/shared/price-type-selector"
import type { Product } from "@/components/analysis/types/analysis"

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
}: ViolinChartProps) {
  const [hoverState, setHoverState] = useState<HoverState>({
    x: 0,
    y: 0,
    price: 0,
    dimmerProducts: 0,
    switchProducts: 0,
    visible: false,
    isDimmerHover: false,
    isSwitchHover: false,
  })
  
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useLayoutEffect(() => {
    if (containerRef.current) {
      const { width, height } = containerRef.current.getBoundingClientRect();
      setDimensions({ width, height });

      const resizeObserver = new ResizeObserver(entries => {
        if (!Array.isArray(entries) || !entries.length) {
          return;
        }
        const entry = entries[0];
        setDimensions({ width: entry.contentRect.width, height: entry.contentRect.height });
      });

      resizeObserver.observe(containerRef.current);
      return () => resizeObserver.disconnect();
    }
  }, []);

  const svgRef = useRef<SVGSVGElement>(null)

  const maxPrice = useMemo(() => Math.max(dimmerStats.max || 0, switchStats.max || 0), [dimmerStats.max, switchStats.max])
  
  const { margin, chartWidth, chartHeight, maxViolinHalfWidth, dimmerX, switchX } = useMemo(() => {
    const margin = { top: 50, right: 20, bottom: 50, left: 80 };
    const chartWidth = dimensions.width > 0 ? dimensions.width - margin.left - margin.right : 0;
    const chartHeight = dimensions.height > 0 ? dimensions.height - margin.top - margin.bottom : 0;
    const maxViolinHalfWidth = chartWidth / 12;
    const dimmerX = margin.left + chartWidth / 3;
    const switchX = margin.left + (chartWidth * 2) / 3;
    return { margin, chartWidth, chartHeight, maxViolinHalfWidth, dimmerX, switchX };
  }, [dimensions.width, dimensions.height]);

  const dimmerDensity = useMemo(() => {
    if (dimmerPrices.length < 2) return [];
    const density = normalizeDensity(kde(dimmerPrices, 1.5, dimmerStats.min, dimmerStats.max, 50), maxViolinHalfWidth);
    density.sort((a, b) => a[0] - b[0]);
    return [[dimmerStats.min, 0], ...density.filter(([p]) => p > dimmerStats.min && p < dimmerStats.max), [dimmerStats.max, 0]] as [number, number][];
  }, [dimmerPrices, dimmerStats, maxViolinHalfWidth]);
  
  const switchDensity = useMemo(() => {
    if (switchPrices.length < 2) return [];
    const density = normalizeDensity(kde(switchPrices, 1.5, switchStats.min, switchStats.max, 50), maxViolinHalfWidth);
    density.sort((a, b) => a[0] - b[0]);
    return [[switchStats.min, 0], ...density.filter(([p]) => p > switchStats.min && p < switchStats.max), [switchStats.max, 0]] as [number, number][];
  }, [switchPrices, switchStats, maxViolinHalfWidth]);

  const yAxisLabels = useMemo(() => {
    if (maxPrice === 0) return [];
    return Array.from({ length: 6 }, (_, i) => i * Math.ceil(maxPrice / 5 / 10) * 10);
  }, [maxPrice]);

  const fixedTolerance = maxPrice * 0.05

  const getDimmerWidth = (price: number) => getDensityWidth(dimmerDensity, price)
  const getSwitchWidth = (price: number) => getDensityWidth(switchDensity, price)

  const handleMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return
    
    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const svgY = event.clientY - rect.top
    
    if (svgX >= margin.left && svgX <= margin.left + chartWidth && svgY >= margin.top && svgY <= margin.top + chartHeight) {
      const price = priceFromY(svgY)
      
      const isDimmerHover = svgX >= dimmerX - maxViolinHalfWidth && svgX <= dimmerX + maxViolinHalfWidth
      const isSwitchHover = svgX >= switchX - maxViolinHalfWidth && svgX <= switchX + maxViolinHalfWidth
      
      const dimmerCount = countProductsInRange(dimmerProducts, price, priceType, fixedTolerance)
      const switchCount = countProductsInRange(switchProducts, price, priceType, fixedTolerance)
      
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
      
      const isDimmerClick = svgX >= dimmerX - maxViolinHalfWidth && svgX <= dimmerX + maxViolinHalfWidth
      const isSwitchClick = svgX >= switchX - maxViolinHalfWidth && svgX <= switchX + maxViolinHalfWidth
      
      if (isDimmerClick || isSwitchClick) {
        const priceRange = {
          min: price - fixedTolerance,
          max: price + fixedTolerance
        }
        const category = isDimmerClick ? "Dimmer Switches" : "Light Switches"
        onViolinClick(category, priceRange)
      }
    }
  }
  
  const dimmerPath = (side: 'left' | 'right') => {
    if (dimmerDensity.length === 0) return "";
    const sign = side === 'left' ? -1 : 1;
    const points = dimmerDensity.map(([price, density]) => `L ${sign * density},${yScale(price)}`).join(" ");
    return `M 0,${yScale(dimmerStats.min)} ${points} Z`;
  }
  
  const switchPath = (side: 'left' | 'right') => {
    if (switchDensity.length === 0) return "";
    const sign = side === 'left' ? -1 : 1;
    const points = switchDensity.map(([price, density]) => `L ${sign * density},${yScale(price)}`).join(" ");
    return `M 0,${yScale(switchStats.min)} ${points} Z`;
  }

  const yScale = (price: number) => margin.top + chartHeight - (price / maxPrice) * chartHeight
  const priceFromY = (y: number) => ((margin.top + chartHeight - y) / chartHeight) * maxPrice

  if (chartWidth === 0 || chartHeight === 0) {
    return (
      <div className="h-full flex">
        <div className="flex-1 relative" ref={containerRef} />
        <StatsBox dimmerStats={dimmerStats} switchStats={switchStats} priceType={priceType} />
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
          <g transform={`translate(${dimmerX}, 0)`}>
            <path d={dimmerPath('left')} fill="#FF6B6B" fillOpacity="0.7" stroke="#FF6B6B" strokeWidth="1" />
            <path d={dimmerPath('right')} fill="#FF6B6B" fillOpacity="0.7" stroke="#FF6B6B" strokeWidth="1" />
            <line x1={-getDimmerWidth(dimmerStats.median)} y1={yScale(dimmerStats.median)} x2={getDimmerWidth(dimmerStats.median)} y2={yScale(dimmerStats.median)} stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
            <line x1={-getDimmerWidth(dimmerStats.mean)} y1={yScale(dimmerStats.mean)} x2={getDimmerWidth(dimmerStats.mean)} y2={yScale(dimmerStats.mean)} stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
          </g>

          {/* Light Switches Violin */}
          <g transform={`translate(${switchX}, 0)`}>
            <path d={switchPath('left')} fill="#4ECDC4" fillOpacity="0.7" stroke="#4ECDC4" strokeWidth="1" />
            <path d={switchPath('right')} fill="#4ECDC4" fillOpacity="0.7" stroke="#4ECDC4" strokeWidth="1" />
            <line x1={-getSwitchWidth(switchStats.median)} y1={yScale(switchStats.median)} x2={getSwitchWidth(switchStats.median)} y2={yScale(switchStats.median)} stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
            <line x1={-getSwitchWidth(switchStats.mean)} y1={yScale(switchStats.mean)} x2={getSwitchWidth(switchStats.mean)} y2={yScale(switchStats.mean)} stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
          </g>

          {/* Crosshair */}
          {hoverState.visible && (
            <g>
              {hoverState.isDimmerHover && (
                <line x1={dimmerX - getDimmerWidth(hoverState.price)} y1={hoverState.y} x2={dimmerX + getDimmerWidth(hoverState.price)} y2={hoverState.y} stroke="#dc2626" strokeWidth="2" opacity="0.9" />
              )}
              {hoverState.isSwitchHover && (
                <line x1={switchX - getSwitchWidth(hoverState.price)} y1={hoverState.y} x2={switchX + getSwitchWidth(hoverState.price)} y2={hoverState.y} stroke="#0891b2" strokeWidth="2" opacity="0.9" />
              )}
            </g>
          )}

          {/* X-axis labels */}
          <text x={dimmerX} y={margin.top + chartHeight + 30} textAnchor="middle" fontSize="14" fill="#64748b">Dimmer Switches</text>
          <text x={switchX} y={margin.top + chartHeight + 30} textAnchor="middle" fontSize="14" fill="#64748b">Light Switches</text>

          {/* Legend */}
          <g transform={`translate(${margin.left + 20}, ${margin.top})`}>
            <rect x="0" y="0" width="160" height="85" fill="white" fillOpacity="0.9" stroke="#e5e7eb" strokeWidth="1" rx="4"/>
            <rect x="10" y="10" width="15" height="15" fill="#FF6B6B" fillOpacity="0.7" />
            <text x="30" y="22" fontSize="11" fill="#374151">Dimmer Switches</text>
            <rect x="10" y="30" width="15" height="15" fill="#4ECDC4" fillOpacity="0.7" />
            <text x="30" y="42" fontSize="11" fill="#374151">Light Switches</text>
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
                  Dimmers: {hoverState.dimmerProducts} products
                </div>
              )}
              {hoverState.isSwitchHover && (
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-cyan-400 rounded-sm"></div>
                  Switches: {hoverState.switchProducts} products
                </div>
              )}
            </div>
          </div>
        )}
      </div>
      <StatsBox dimmerStats={dimmerStats} switchStats={switchStats} priceType={priceType} />
    </div>
  )
}

const StatsBox = ({ dimmerStats, switchStats, priceType }: any) => (
  <div className="w-80 ml-4 bg-white border border-gray-200 rounded-md p-4">
    <div className="mb-4">
      <h4 className="font-medium text-sm mb-2">
        Dimmer Switches ({priceType === "sku" ? "Total Price (for a full pack)" : "Price per unit"}):
      </h4>
      <div className="text-xs space-y-1">
        <div>Min: ${dimmerStats.min.toFixed(2)}</div>
        <div>Q1: ${dimmerStats.q1.toFixed(2)}</div>
        <div>Median: ${dimmerStats.median.toFixed(2)}</div>
        <div>Mean: ${dimmerStats.mean.toFixed(2)}</div>
        <div>Q3: ${dimmerStats.q3.toFixed(2)}</div>
        <div>Max: ${dimmerStats.max.toFixed(2)}</div>
      </div>
    </div>
    <div>
      <h4 className="font-medium text-sm mb-2">
        Light Switches ({priceType === "sku" ? "Total Price (for a full pack)" : "Price per unit"}):
      </h4>
      <div className="text-xs space-y-1">
        <div>Min: ${switchStats.min.toFixed(2)}</div>
        <div>Q1: ${switchStats.q1.toFixed(2)}</div>
        <div>Median: ${switchStats.median.toFixed(2)}</div>
        <div>Mean: ${switchStats.mean.toFixed(2)}</div>
        <div>Q3: ${switchStats.q3.toFixed(2)}</div>
        <div>Max: ${switchStats.max.toFixed(2)}</div>
      </div>
    </div>
  </div>
);

