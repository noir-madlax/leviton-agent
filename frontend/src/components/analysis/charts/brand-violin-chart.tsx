"use client"

import { useMemo, useState, useRef, useLayoutEffect } from "react"
import type { PriceType } from "@/components/analysis/shared/price-type-selector"

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

interface ChartRendererProps extends BrandViolinChartProps {
  width?: number
  height?: number
}

interface HoverState {
  visible: boolean
  x: number
  y: number
  cursorX: number
  price: number
  products: number
  brand: string
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
function normalizeDensity(densityData: [number, number][], maxHeight: number): [number, number][] {
  const maxDensity = Math.max(...densityData.map((d) => d[1]))
  const minWidth = 0.5 // Small constant minimal width in pixels
  if (maxDensity === 0) return densityData.map(([x]) => [x, minWidth])
  return densityData.map(([x, y]) => [x, Math.max(minWidth, (y / maxDensity) * maxHeight)])
}

// Function to lighten colors for tooltip background
function lightenColor(color: string, percent: number): string {
  if (color.startsWith("#")) {
    const num = parseInt(color.slice(1), 16)
    const r = Math.min(255, Math.floor((num >> 16) + (255 - (num >> 16)) * percent))
    const g = Math.min(255, Math.floor(((num >> 8) & 0x00FF) + (255 - ((num >> 8) & 0x00FF)) * percent))
    const b = Math.min(255, Math.floor((num & 0x0000FF) + (255 - (num & 0x0000FF)) * percent))
    return `rgb(${r}, ${g}, ${b})`
  }
  
  const rgbMatch = color.match(/rgb\\((\\d+),\\s*(\\d+),\\s*(\\d+)\\)/)
  if (rgbMatch) {
    const r = Math.min(255, Math.floor(parseInt(rgbMatch[1]) + (255 - parseInt(rgbMatch[1])) * percent))
    const g = Math.min(255, Math.floor(parseInt(rgbMatch[2]) + (255 - parseInt(rgbMatch[2])) * percent))
    const b = Math.min(255, Math.floor(parseInt(rgbMatch[3]) + (255 - parseInt(rgbMatch[3])) * percent))
    return `rgb(${r}, ${g}, ${b})`
  }
  
  return color
}

function ChartRenderer({ brands, priceType, category, width = 800, height = 370, onViolinClick }: ChartRendererProps) {
  const svgRef = useRef<SVGSVGElement>(null)
  const containerRef = useRef<HTMLDivElement>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
  const [hoverState, setHoverState] = useState<HoverState>({
    visible: false,
    x: 0,
    y: 0,
    cursorX: 0,
    price: 0,
    products: 0,
    brand: ""
  })

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

  const layout = useMemo(() => ({
    width: dimensions.width || width,
    height: dimensions.height || height,
    marginTop: 30,
    marginBottom: 70,
    marginLeft: 70,
    marginRight: 25,
    get chartWidth() { return this.width - this.marginLeft - this.marginRight },
    get chartHeight() { return this.height - this.marginTop - this.marginBottom },
    get yAxisBottom() { return this.height - this.marginBottom },
    yAxisTickIncrement: 50,
  }), [dimensions.width, dimensions.height, width, height])

  const chartData = useMemo(() => {
    const filtered = brands
      .filter(brand => {
        const prices = priceType === "sku" ? brand.skuPrices : brand.unitPrices
        return prices.length >= 3
      })
      .slice(0, 8)

    const allPrices = filtered.flatMap(brand => (priceType === "sku" ? brand.skuPrices : brand.unitPrices))
    const maxPrice = Math.max(...allPrices, 0)
    const brandWidth = filtered.length > 0 ? layout.chartWidth / filtered.length : 0
    const maxViolinHalfWidth = (brandWidth / 2) * 0.9

    const data = filtered.map(brand => {
      const prices = priceType === "sku" ? brand.skuPrices : brand.unitPrices
      const bandwidth = 1.5
      const min = Math.max(0, Math.min(...prices) - 10)
      const max = Math.min(maxPrice, Math.max(...prices) + 10)
      const sortedPrices = [...prices].sort((a, b) => a - b)
      const median = sortedPrices[Math.floor(sortedPrices.length / 2)]
      const mean = prices.reduce((a, b) => a + b, 0) / prices.length

      return {
        name: brand.name,
        prices,
        density: normalizeDensity(kde(prices, bandwidth, min, max, 50), maxViolinHalfWidth),
        median,
        mean,
        count: prices.length,
      }
    })

    return { data, maxPrice, brandWidth }
  }, [brands, priceType, layout.chartWidth])

  const { data: brandData, maxPrice, brandWidth } = chartData
  
  const yAxisSteps = Math.ceil(maxPrice / layout.yAxisTickIncrement)
  const yAxisLabels = Array.from({ length: yAxisSteps + 1 }, (_, i) => i * layout.yAxisTickIncrement)

  const brandColors: Record<string, string> = {
    Lutron: "#E67E22",
    GE: "#3498DB", 
    Leviton: "#9B59B6",
    BESTTEN: "#FDB462",
    ELEGRP: "#80B1D3",
    Amazon: "#FCCDE5",
    TREATLIFE: "#FF6B6B",
    "ENERLITES Store": "#B3DE69",
    Legrand: "#2ECC71",
    "SOZULAMP Store": "#95A5A6",
    Kasa: "#8DD3C7",
    "TP-Link": "#4ECDC4",
    Other: "#D3D3D3",
  }

  const getViolinWidth = (density: [number, number][], price: number): number => {
    if (!density || density.length === 0) return 0
    
    let closestPoint = density[0]
    let minDistance = Math.abs(density[0][0] - price)
    
    for (const point of density) {
      const distance = Math.abs(point[0] - price)
      if (distance < minDistance) {
        minDistance = distance
        closestPoint = point
      }
    }
    
    return closestPoint[1]
  }

  const getDensityWidth = (density: [number, number][], price: number): number => {
    return getViolinWidth(density, price)
  }

  const handleMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return

    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const svgY = event.clientY - rect.top
    
    const brandIndex = Math.floor((svgX - layout.marginLeft) / brandWidth)

    if (brandIndex >= 0 && brandIndex < brandData.length && 
        svgX >= layout.marginLeft && svgX <= layout.marginLeft + layout.chartWidth && 
        svgY >= layout.marginTop && svgY <= layout.marginTop + layout.chartHeight) {
      const brand = brandData[brandIndex]
      const xCenter = layout.marginLeft + brandIndex * brandWidth + brandWidth / 2
      const price = ((layout.yAxisBottom - svgY) / layout.chartHeight) * maxPrice

      const violinHalfWidth = getViolinWidth(brand.density, price)
      
      if (Math.abs(svgX - xCenter) <= violinHalfWidth) {
        setHoverState({
          visible: true,
          x: xCenter,
          y: svgY,
          cursorX: svgX,
          price,
          products: brand.count,
          brand: brand.name,
        })
      } else {
        setHoverState(prev => ({ ...prev, visible: false }))
      }
    } else {
      setHoverState(prev => ({ ...prev, visible: false }))
    }
  }

  const handleMouseLeave = () => {
    setHoverState(prev => ({ ...prev, visible: false }))
  }

  const handleClick = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current || !onViolinClick) return

    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const brandIndex = Math.floor((svgX - layout.marginLeft) / brandWidth)

    if (brandIndex >= 0 && brandIndex < brandData.length) {
      const brand = brandData[brandIndex]
      onViolinClick(brand.name, category)
    }
  }

  if (layout.chartHeight <= 0 || dimensions.width === 0 || dimensions.height === 0) {
    return (
      <div className="h-full w-full relative" ref={containerRef}>
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">Chart is too small to display.</p>
        </div>
      </div>
    )
  }

  if (brandData.length === 0) {
    return (
      <div className="h-full w-full relative" ref={containerRef}>
        <div className="flex items-center justify-center h-full">
          <p className="text-gray-500">No sufficient data for violin plots</p>
        </div>
      </div>
    )
  }

  return (
    <div className="h-full w-full relative" ref={containerRef}>
      <svg 
        ref={svgRef}
        width={dimensions.width}
        height={dimensions.height}
        className="w-full h-full cursor-pointer"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        <rect x={layout.marginLeft} y={layout.marginTop} width={layout.chartWidth} height={layout.chartHeight} fill="#f8fafc" />

        {yAxisLabels.map((price) => (
          <line
            key={price}
            x1={layout.marginLeft}
            y1={layout.yAxisBottom - (price / maxPrice) * layout.chartHeight}
            x2={layout.width - layout.marginRight}
            y2={layout.yAxisBottom - (price / maxPrice) * layout.chartHeight}
            stroke="#e2e8f0"
            strokeDasharray="2,2"
          />
        ))}

        <line x1={layout.marginLeft} y1={layout.marginTop} x2={layout.marginLeft} y2={layout.yAxisBottom} stroke="#64748b" strokeWidth="1" />

        {yAxisLabels.map((price) => (
          <text 
            key={price} 
            x={layout.marginLeft - 5} 
            y={layout.yAxisBottom - (price / maxPrice) * layout.chartHeight + 4} 
            textAnchor="end" 
            fontSize="14" 
            fill="#64748b"
          >
            ${price}
          </text>
        ))}

        <text x={20} y={layout.height / 2} textAnchor="middle" fontSize="16" fill="#64748b" transform={`rotate(-90, 20, ${layout.height / 2})`}>
          Price (USD)
        </text>

        <line x1={layout.marginLeft} y1={layout.yAxisBottom} x2={layout.width - layout.marginRight} y2={layout.yAxisBottom} stroke="#64748b" strokeWidth="1" />

        {brandData.map((brand, index) => {
          if (brand.density.length === 0) return null

          const xPosition = layout.marginLeft + index * brandWidth + brandWidth / 2
          const color = brandColors[brand.name] || brandColors.Other

          return (
            <g key={brand.name}>
              <text 
                x={xPosition} 
                y={layout.yAxisBottom + 35} 
                textAnchor="middle" 
                fontSize="14" 
                fill="#64748b"
                transform={`rotate(-45, ${xPosition}, ${layout.yAxisBottom + 35})`}
              >
                {brand.name}
              </text>

              <g transform={`translate(${xPosition}, ${layout.yAxisBottom})`}>
                <path
                  d={`M 0,0 ${brand.density.map(([price, density]) => 
                    `L ${-density},${-(price / maxPrice) * layout.chartHeight}`
                  ).join(" ")} 
                     ${brand.density
                       .slice()
                       .reverse()
                       .map(([price, density]) => 
                         `L ${density},${-(price / maxPrice) * layout.chartHeight}`
                       )
                       .join(" ")} Z`}
                  fill={color}
                  fillOpacity="0.7"
                  stroke={color}
                  strokeWidth="1"
                />

                <line
                  x1={-getDensityWidth(brand.density, brand.median)}
                  y1={-(brand.median / maxPrice) * layout.chartHeight}
                  x2={getDensityWidth(brand.density, brand.median)}
                  y2={-(brand.median / maxPrice) * layout.chartHeight}
                  stroke="#7c3aed"
                  strokeWidth="2"
                  strokeDasharray="6,3"
                />

                <line
                  x1={-getDensityWidth(brand.density, brand.mean)}
                  y1={-(brand.mean / maxPrice) * layout.chartHeight}
                  x2={getDensityWidth(brand.density, brand.mean)}
                  y2={-(brand.mean / maxPrice) * layout.chartHeight}
                  stroke="#059669"
                  strokeWidth="1.5"
                  strokeDasharray="3,3"
                />
              </g>
            </g>
          )
        })}

        {hoverState.visible && (
          <g>
            <line
              x1={hoverState.x - getViolinWidth(brandData.find(b => b.name === hoverState.brand)?.density || [], hoverState.price)}
              y1={hoverState.y}
              x2={hoverState.x + getViolinWidth(brandData.find(b => b.name === hoverState.brand)?.density || [], hoverState.price)}
              y2={hoverState.y}
              stroke="#dc2626"
              strokeWidth="2"
              opacity="0.9"
            />
          </g>
        )}

        <text x={layout.width / 2} y={layout.height - 5} textAnchor="middle" fontSize="16" fill="#64748b">
          Brands
        </text>

        <g transform={`translate(${layout.width - 90}, ${layout.marginTop + 10})`}>
          <rect x="-5" y="-5" width="85" height="50" fill="white" stroke="#e2e8f0" strokeWidth="1" rx="4" />
          
          <line x1="5" y1="12" x2="22" y2="12" stroke="#7c3aed" strokeWidth="2" strokeDasharray="6,3" />
          <text x="27" y="16" fontSize="12" fill="#374151">Median</text>

          <line x1="5" y1="30" x2="22" y2="30" stroke="#059669" strokeWidth="1.5" strokeDasharray="3,3" />
          <text x="27" y="34" fontSize="12" fill="#374151">Mean</text>
        </g>
      </svg>

      {hoverState.visible && (
        <div
          className="absolute pointer-events-none z-10 p-3 rounded-lg shadow-lg border text-sm"
          style={{
            left: `${hoverState.cursorX}px`,
            top: `${hoverState.y}px`,
            transform: "translate(-50%, calc(-100% - 15px))",
            backgroundColor: lightenColor(brandColors[hoverState.brand] || brandColors.Other, 0.4),
            width: "33vw",
            maxWidth: "400px",
            minWidth: "250px",
            wordWrap: "break-word",
            lineHeight: "1.4"
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

export function BrandViolinChart({ brands, priceType, category, onViolinClick }: BrandViolinChartProps) {
  return (
    <ChartRenderer brands={brands} priceType={priceType} category={category} onViolinClick={onViolinClick} />
  )
}
