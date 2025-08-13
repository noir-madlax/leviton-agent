"use client"

import { useMemo, useState, useRef, useLayoutEffect } from "react"
import type { PriceType } from "@/components/analysis-db/shared/price-type-selector"
import { useProductPanelQuery } from '@/components/analysis-db/hooks/use-product-panel-query'

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
  projectId: string
}

interface HoverState {
  x: number
  y: number
  price: number
  segmentName: string
  productCount: number
  priceRangeProductCount: number // 新增：当前价格区间内的产品数量
  priceRange: { min: number; max: number } // 新增：当前价格区间
  visible: boolean
  hoveredSegmentIndex?: number
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

// Function to count products in a price range
function countProductsInPriceRange(prices: number[], minPrice: number, maxPrice: number): number {
  return prices.filter(price => price >= minPrice && price <= maxPrice).length
}

export function MultiSegmentViolinChart({
  segments,
  priceType = "sku",
  projectId,
}: MultiSegmentViolinChartProps) {
  // 使用新的产品浮窗查询Hook
  const { handleViolinClick, handleMultipleFiltersClick, loading: panelLoading, error: panelError } = useProductPanelQuery()
  
  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _ = priceType // Acknowledge priceType parameter for future use
  const [hoverState, setHoverState] = useState<HoverState>({
    x: 0,
    y: 0,
    price: 0,
    segmentName: '',
    productCount: 0,
    priceRangeProductCount: 0,
    priceRange: { min: 0, max: 0 },
    visible: false,
    hoveredSegmentIndex: undefined,
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

  // 数据验证
  const validSegments = segments.filter(segment => 
    segment.prices && segment.prices.length > 0
  )

  const maxPrice = useMemo(() => {
    if (validSegments.length === 0) return 0
    return Math.max(...validSegments.map(s => s.stats.max || 0))
  }, [validSegments])
  
  const { margin, chartWidth, chartHeight, maxViolinHalfWidth, segmentPositions } = useMemo(() => {
    // Increase bottom margin to allow longer rotated x-axis labels
    const margin = { top: 30, right: 20, bottom: 80, left: 60 };
    const chartWidth = dimensions.width > 0 ? dimensions.width - margin.left - margin.right : 0;
    const chartHeight = dimensions.height > 0 ? dimensions.height - margin.top - margin.bottom : 0;
    const maxViolinHalfWidth = chartWidth / (validSegments.length * 3);
    const segmentPositions = validSegments.map((_, index) => 
      margin.left + (chartWidth / validSegments.length) * (index + 0.5)
    );
    return { margin, chartWidth, chartHeight, maxViolinHalfWidth, segmentPositions };
  }, [dimensions.width, dimensions.height, validSegments.length]);

  const segmentDensities = useMemo(() => {
    return validSegments.map(segment => {
      if (segment.prices.length < 2) return [];
      const density = normalizeDensity(
        kde(segment.prices, 1.5, segment.stats.min, segment.stats.max, 50), 
        maxViolinHalfWidth
      );
      density.sort((a, b) => a[0] - b[0]);
      return [[segment.stats.min, 0], ...density.filter(([p]) => p > segment.stats.min && p < segment.stats.max), [segment.stats.max, 0]] as [number, number][];
    });
  }, [validSegments, maxViolinHalfWidth]);

  const yAxisLabels = useMemo(() => {
    if (maxPrice === 0) return [];
    return Array.from({ length: 6 }, (_, i) => i * Math.ceil(maxPrice / 5 / 10) * 10);
  }, [maxPrice]);

  // 价格区间窗口大小，用于计算当前区间内的产品数量
  const priceWindowPercentage = 0.03 // 3% 的价格窗口

  const getSegmentWidth = (segmentIndex: number, price: number) => 
    getDensityWidth(segmentDensities[segmentIndex] || [], price)

  const handleMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return
    
    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const svgY = event.clientY - rect.top
    
    if (svgX >= margin.left && svgX <= margin.left + chartWidth && svgY >= margin.top && svgY <= margin.top + chartHeight) {
      const price = priceFromY(svgY)
      
      // 找到鼠标悬停的段落
      let hoveredSegmentIndex = -1
      for (let i = 0; i < validSegments.length; i++) {
        const segmentX = segmentPositions[i]
        if (svgX >= segmentX - maxViolinHalfWidth && svgX <= segmentX + maxViolinHalfWidth) {
          hoveredSegmentIndex = i
          break
        }
      }
      
      if (hoveredSegmentIndex >= 0) {
        const segment = validSegments[hoveredSegmentIndex]

        // 计算当前价格区间
        const priceWindow = Math.max(maxPrice * priceWindowPercentage, 1) // 最小窗口为1
        const priceRangeMin = Math.max(price - priceWindow / 2, segment.stats.min)
        const priceRangeMax = Math.min(price + priceWindow / 2, segment.stats.max)

        // 计算当前价格区间内的产品数量
        const priceRangeProductCount = countProductsInPriceRange(
          segment.prices,
          priceRangeMin,
          priceRangeMax
        )

        setHoverState({
          x: svgX,
          y: svgY,
          price: price,
          segmentName: segment.name,
          productCount: segment.productCount || segment.prices.length,
          priceRangeProductCount: priceRangeProductCount,
          priceRange: { min: priceRangeMin, max: priceRangeMax },
          visible: true,
          hoveredSegmentIndex: hoveredSegmentIndex,
        })
      } else {
        setHoverState(prev => ({ ...prev, visible: false, hoveredSegmentIndex: undefined }))
      }
    } else {
      setHoverState(prev => ({ ...prev, visible: false, hoveredSegmentIndex: undefined }))
    }
  }

  const handleMouseLeave = () => {
    setHoverState(prev => ({ ...prev, visible: false }))
  }

  const handleClick = async (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return

    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const svgY = event.clientY - rect.top

    if (svgX >= margin.left && svgX <= margin.left + chartWidth && svgY >= margin.top && svgY <= margin.top + chartHeight) {
      // 找到点击的段落
      for (let i = 0; i < validSegments.length; i++) {
        const segmentX = segmentPositions[i]
        if (svgX >= segmentX - maxViolinHalfWidth && svgX <= segmentX + maxViolinHalfWidth) {
          const segmentName = validSegments[i].name

          // 解析 segmentName，支持 "Category + Smart Capability" 格式
          const parts = segmentName.split(' + ')
          const filters: any = {}
          let title = `${segmentName} Products`
          let subtitle = `All products in ${segmentName}`

          if (parts.length === 2) {
            const category = parts[0].trim()
            const smartCapability = parts[1].trim()
            filters.categories = [category]
            filters.extend_fields = { smart_capability: smartCapability }
            subtitle = `Category: ${category}, Capability: ${smartCapability}`
          } else if (i < 2) {
            // 回退到旧逻辑：前两个按 category 筛选
            filters.categories = [segmentName]
          } else {
            // 回退到旧逻辑：后两个按 smart_capability 筛选
            filters.extend_fields = { smart_capability: segmentName }
            subtitle = `All ${segmentName.toLowerCase()} products`
          }

          await handleMultipleFiltersClick(
            projectId,
            filters,
            title,
            subtitle,
            { brand: true, category: true, priceRange: true, packSize: true }
          )
          
          break
        }
      }
    }
  }
  
  const segmentPath = (segmentIndex: number, side: 'left' | 'right') => {
    const density = segmentDensities[segmentIndex]
    if (!density || density.length === 0) return "";
    const sign = side === 'left' ? -1 : 1;
    const segment = validSegments[segmentIndex]
    const points = density.map(([price, densityValue]) => `L ${sign * densityValue},${yScale(price)}`).join(" ");
    return `M 0,${yScale(segment.stats.min)} ${points} Z`;
  }

  const yScale = (price: number) => margin.top + chartHeight - (price / maxPrice) * chartHeight
  const priceFromY = (y: number) => ((margin.top + chartHeight - y) / chartHeight) * maxPrice

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

  if (chartWidth === 0 || chartHeight === 0) {
    return (
      <div className="h-full w-full relative" ref={containerRef} />
    );
  }

  return (
    <div className="h-full w-full relative" ref={containerRef}>
      {/* 加载状态覆盖层 */}
      {panelLoading && (
        <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-20">
          <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-md">
            <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
            <span className="text-sm text-gray-600">Loading products...</span>
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {panelError && (
        <div className="absolute top-4 right-4 bg-red-50 border border-red-200 text-red-700 px-3 py-2 rounded-md text-sm z-20">
          Error: {panelError}
        </div>
      )}

      <svg
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className={`w-full h-full cursor-pointer ${panelLoading ? 'pointer-events-none' : ''}`}
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
          <text x={15} y={margin.top + chartHeight / 2} textAnchor="middle" fontSize="14" fill="#64748b" transform={`rotate(-90, 15, ${margin.top + chartHeight / 2})`}>
            Price (USD)
          </text>

          {/* X-axis */}
          <line x1={margin.left} y1={margin.top + chartHeight} x2={margin.left + chartWidth} y2={margin.top + chartHeight} stroke="#64748b" strokeWidth="1" />

          {/* Segment Violins */}
          {validSegments.map((segment, index) => (
            <g key={segment.name} transform={`translate(${segmentPositions[index]}, 0)`}>
              <path d={segmentPath(index, 'left')} fill={segment.color} fillOpacity="0.7" stroke={segment.color} strokeWidth="1" />
              <path d={segmentPath(index, 'right')} fill={segment.color} fillOpacity="0.7" stroke={segment.color} strokeWidth="1" />
              <line x1={-getSegmentWidth(index, segment.stats.median)} y1={yScale(segment.stats.median)} x2={getSegmentWidth(index, segment.stats.median)} y2={yScale(segment.stats.median)} stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
              <line x1={-getSegmentWidth(index, segment.stats.mean)} y1={yScale(segment.stats.mean)} x2={getSegmentWidth(index, segment.stats.mean)} y2={yScale(segment.stats.mean)} stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
            </g>
          ))}

          {/* Crosshair */}
          {hoverState.visible && hoverState.hoveredSegmentIndex !== undefined && (
            <g>
              <line 
                x1={segmentPositions[hoverState.hoveredSegmentIndex] - getSegmentWidth(hoverState.hoveredSegmentIndex, hoverState.price)} 
                y1={hoverState.y} 
                x2={segmentPositions[hoverState.hoveredSegmentIndex] + getSegmentWidth(hoverState.hoveredSegmentIndex, hoverState.price)} 
                y2={hoverState.y} 
                stroke="#dc2626" 
                strokeWidth="2" 
                opacity="0.9" 
              />
            </g>
          )}

          {/* X-axis labels - allow longer names and rotate slightly */}
          {validSegments.map((segment, index) => (
            <text 
              key={segment.name}
              x={segmentPositions[index]} 
              y={margin.top + chartHeight + 25} 
              textAnchor="middle" 
              fontSize="12" 
              fill="#64748b"
              transform={`rotate(0, ${segmentPositions[index]}, ${margin.top + chartHeight + 25})`}
            >
              {segment.name.length > 26 ? `${segment.name.substring(0, 24)}...` : segment.name}
            </text>
          ))}

          {/* Legend - widen container and allow longer names */}
          <g transform={`translate(${margin.left + 620}, ${margin.top - 35})`}>
            <rect x="0" y="0" width="240" height="65" fill="white" fillOpacity="0.9" stroke="#e5e7eb" strokeWidth="1" rx="4"/>
            {validSegments.slice(0, 2).map((segment, index) => (
              <g key={segment.name}>
                <rect x="10" y={10 + index * 20} width="15" height="15" fill={segment.color} fillOpacity="0.7" />
                <text x="30" y={22 + index * 20} fontSize="11" fill="#374151">
                  {segment.name.length > 26 ? `${segment.name.substring(0, 24)}...` : segment.name}
                </text>
              </g>
            ))}
            <line x1="10" y1="55" x2="25" y2="55" stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
            <text x="30" y="58" fontSize="11" fill="#374151">Median</text>
            <line x1="90" y1="55" x2="105" y2="55" stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
            <text x="110" y="58" fontSize="11" fill="#374151">Mean</text>
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
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-sm" style={{backgroundColor: validSegments[hoverState.hoveredSegmentIndex!]?.color}}></div>
                {hoverState.segmentName}
              </div>
              <div className="mt-1 text-xs">
                <div className="font-medium text-blue-600">
                  Price range ${hoverState.priceRange.min.toFixed(2)} - ${hoverState.priceRange.max.toFixed(2)}: {hoverState.priceRangeProductCount} products
                </div>
                <div className="text-gray-500">
                  Total in segment: {hoverState.productCount} products
                </div>
              </div>
            </div>
                   </div>
       )}
     </div>
   )
}

 