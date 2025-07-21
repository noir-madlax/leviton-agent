"use client"

import React, { useState, useRef, useLayoutEffect, useMemo } from 'react'
import { PriceType } from '../shared/price-type-selector'
import { getChartColor } from '../shared/chart-colors'
import { useProductPanelQuery } from '@/components/analysis-db/hooks/use-product-panel-query'

interface BrandViolinChartProps {
  brands: {
    name: string
    skuPrices: number[]
    unitPrices: number[]
  }[]
  priceType: PriceType
  category: string
  projectId: string
  // 新增：筛选模式配置
  filterMode?: 'category' | 'extend_fields'
  // 新增：扩展字段配置
  extendFieldsConfig?: {
    field: string  // 例如 'smart_capability'
    value: string  // 例如 'Smart' 或 'Non-Smart'
  }
}

interface HoverState {
  x: number
  y: number
  price: number
  brand: string
  products: number
  priceRangeProductCount: number // 新增：当前价格区间内的产品数量
  priceRange: { min: number; max: number } // 新增：当前价格区间
  visible: boolean
  brandIndex: number
}

/**
 * 核密度估计（KDE）函数 - 小提琴图的核心算法
 * 
 * 作用：将离散的价格数据点转换为连续的密度分布曲线
 * 原理：对每个价格点，使用高斯核函数计算其对整体密度分布的贡献
 * 
 * @param data 原始价格数据数组
 * @param bandwidth 带宽参数，控制平滑程度（越大越平滑）
 * @param min 计算范围的最小值
 * @param max 计算范围的最大值  
 * @param steps 将范围分成多少步来计算密度
 * @returns 返回 [价格, 密度] 对的数组，这就是小提琴的"轮廓"
 */
function kde(data: number[], bandwidth: number, min: number, max: number, steps: number): [number, number][] {
  const result: [number, number][] = []
  const range = max - min
  const step = range / steps // 每一步的价格间隔

  // 在价格范围内，每隔一个step计算一次密度值
  for (let i = 0; i <= steps; i++) {
    const x = min + i * step // 当前计算密度的价格点
    let density = 0

    // 对于当前价格点x，计算所有原始数据点对其密度的贡献
    for (const point of data) {
      const z = (x - point) / bandwidth // 标准化距离
      // 高斯核函数：离当前点越近的数据点，贡献越大
      density += Math.exp(-0.5 * z * z) / Math.sqrt(2 * Math.PI)
    }

    // 归一化密度值
    density /= data.length * bandwidth
    result.push([x, density]) // 保存这个价格点的密度值
  }

  return result // 返回密度分布数据，这就是小提琴的"形状"
}

/**
 * 密度值归一化函数 - 将密度转换为像素宽度
 * 
 * 作用：将KDE计算出的抽象密度值转换为SVG中实际的像素宽度
 * 这样我们就能知道小提琴在每个价格点应该有多"胖"
 * 
 * @param densityData KDE函数返回的密度数据
 * @param maxHalfWidth 小提琴最大半宽度（像素）
 * @returns 返回 [价格, 像素宽度] 对的数组
 */
function normalizeDensity(densityData: [number, number][], maxHalfWidth: number): [number, number][] {
  // 找到最大密度值，用于归一化
  const maxDensity = Math.max(...densityData.map((d) => d[1]))
  const minWidth = 0.5 // 最小宽度，确保即使密度为0也有可见的线条
  
  if (maxDensity === 0) return densityData.map(([x]) => [x, minWidth])
  
  // 将每个密度值按比例转换为像素宽度
  // 密度越大的地方，小提琴越宽
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

// Clean brand name to remove invisible characters
function cleanBrandName(brand: string): string {
  return brand.replace(/[\u200B-\u200D\uFEFF\u202C\u202D\u2066-\u2069]/g, '').trim()
}

export function BrandViolinChart({
  brands,
  priceType,
  category,
  projectId,
  filterMode = 'category',
  extendFieldsConfig
}: BrandViolinChartProps) {
  // 使用新的产品浮窗查询Hook
  const { handleBrandViolinClick, handleMultipleFiltersClick, loading: panelLoading, error: panelError } = useProductPanelQuery()
  const [hoverState, setHoverState] = useState<HoverState>({
    x: 0,
    y: 0,
    price: 0,
    brand: '',
    products: 0,
    priceRangeProductCount: 0,
    priceRange: { min: 0, max: 0 },
    visible: false,
    brandIndex: -1
  })
  
  const containerRef = useRef<HTMLDivElement>(null)
  const svgRef = useRef<SVGSVGElement>(null)
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 })

  useLayoutEffect(() => {
    if (containerRef.current) {
      const { width, height } = containerRef.current.getBoundingClientRect()
      setDimensions({ width, height })

      const resizeObserver = new ResizeObserver(entries => {
        if (!Array.isArray(entries) || !entries.length) {
          return
        }
        const entry = entries[0]
        setDimensions({ width: entry.contentRect.width, height: entry.contentRect.height })
      })

      resizeObserver.observe(containerRef.current)
      return () => resizeObserver.disconnect()
    }
  }, [])

  // 数据验证和过滤
  const validBrands = brands.filter(brand => {
    const prices = priceType === "sku" ? brand.skuPrices : brand.unitPrices
    return prices && prices.length > 0
  }).slice(0, 8) // 限制显示最多8个品牌

  // 计算全局价格范围
  const allPrices = validBrands.flatMap(brand => 
    priceType === "sku" ? brand.skuPrices : brand.unitPrices
  )
  const globalMin = Math.min(...allPrices)
  const globalMax = Math.max(...allPrices)

  const { margin, chartWidth, chartHeight, maxViolinHalfWidth, brandPositions } = useMemo(() => {
    const margin = { top: 30, right: 40, bottom: 60, left: 60 }
    const chartWidth = dimensions.width > 0 ? dimensions.width - margin.left - margin.right : 0
    const chartHeight = dimensions.height > 0 ? dimensions.height - margin.top - margin.bottom : 0
    const maxViolinHalfWidth = chartWidth / (validBrands.length * 2.5)
    
    const brandPositions = validBrands.map((_, index) => {
      return margin.left + (chartWidth / validBrands.length) * (index + 0.5)
    })
    
    return { margin, chartWidth, chartHeight, maxViolinHalfWidth, brandPositions }
  }, [dimensions.width, dimensions.height, validBrands.length])

  // 🎻 计算每个品牌的小提琴数据 - 这是小提琴图生成的关键步骤
  const violinData = useMemo(() => {
    return validBrands.map((brand, index) => {
      // 根据用户选择的价格类型获取数据
      const prices = priceType === "sku" ? brand.skuPrices : brand.unitPrices
      const sortedPrices = [...prices].sort((a, b) => a - b)
      
      // 📊 计算基础统计信息（中位数、均值等）
      const stats = {
        min: sortedPrices[0],
        median: sortedPrices[Math.floor(sortedPrices.length / 2)],
        mean: prices.reduce((a, b) => a + b, 0) / prices.length,
        max: sortedPrices[sortedPrices.length - 1],
        count: prices.length
      }

      // 🎨 计算小提琴的形状密度分布 - 修复分叉问题
      let density: [number, number][] = []
      if (prices.length >= 2) {
        // 关键修复：KDE的计算范围应限定在当前品牌的min/max内，防止分叉
        const bandwidth = Math.max(1, (stats.max - stats.min) * 0.05) || 1
        const rawDensity = normalizeDensity(kde(prices, bandwidth, stats.min, stats.max, 50), maxViolinHalfWidth)
        rawDensity.sort((a, b) => a[0] - b[0]) // 按价格排序
        
        // 构造完整的小提琴轮廓，确保首尾是尖的
        // 这是形成优美小提琴形状的关键
        density = [
          [stats.min, 0], // 底部尖端
          ...rawDensity.filter(([p]) => p > stats.min && p < stats.max), // 中间的密度曲线
          [stats.max, 0]  // 顶部尖端
        ]
      } else if (prices.length === 1) {
        // 如果只有一个数据点，创建一个简单的菱形
        density = [
          [stats.min, 0], // 底部尖端
          [stats.min, maxViolinHalfWidth * 0.5], // 中间最宽处
          [stats.max, 0]  // 顶部尖端
        ]
      }

      const cleanName = cleanBrandName(brand.name)
      return {
        name: cleanName,
        prices,
        color: getChartColor(index), // 每个品牌分配不同颜色
        stats,
        density, // 这就是小提琴的"形状数据"
        x: brandPositions[index], // 品牌在X轴上的位置
        getDensityWidth: (price: number) => getDensityWidth(density, price) // 获取指定价格处的宽度
      }
    })
  }, [validBrands, priceType, maxViolinHalfWidth, brandPositions])

  const yAxisLabels = useMemo(() => {
    if (globalMax === globalMin) return [0]
    return Array.from({ length: 6 }, (_, i) => i * Math.ceil(globalMax / 5 / 10) * 10)
  }, [globalMax, globalMin])

  // 价格区间窗口大小，用于计算当前区间内的产品数量
  const priceWindowPercentage = 0.03 // 3% 的价格窗口

  // 📏 Y轴坐标转换函数：将价格值转换为SVG的Y坐标
  // 注意：SVG坐标系Y轴向下，所以价格越高，Y坐标越小
  const yScale = (price: number) => margin.top + chartHeight - ((price - globalMin) / (globalMax - globalMin)) * chartHeight
  
  // 📏 反向转换：将SVG的Y坐标转换回价格值（用于鼠标交互）
  const priceFromY = (y: number) => globalMin + ((margin.top + chartHeight - y) / chartHeight) * (globalMax - globalMin)

  /**
   * 🎨 创建小提琴路径 - 完全按照示例代码的方式
   * 
   * 关键改进：
   * 1. 使用品牌自己的统计数据作为起始点，而不是密度数据的边界
   * 2. 从中心线开始，绘制到密度边缘，然后闭合回中心线
   * 3. 这样能确保小提琴的头部和底部更加平滑自然
   * 
   * @param density 密度数据数组 [价格, 宽度]
   * @param stats 品牌的统计数据，用于确定起始点
   * @param side 绘制左半边还是右半边
   * @returns SVG路径字符串
   */
  const createViolinPath = (density: [number, number][], stats: { min: number; max: number; median: number; mean: number; count: number }, side: 'left' | 'right') => {
    if (density.length === 0) return ""
    
    // 确定方向：左半边用负数，右半边用正数
    const sign = side === 'left' ? -1 : 1
    
    // 将每个密度点转换为SVG路径点
    // price -> Y坐标（通过yScale函数转换）
    // width -> X坐标（乘以方向符号）
    const points = density.map(([price, width]) => {
      const y = yScale(price)
      const x = sign * width
      if (isNaN(x) || isNaN(y)) return ""
      return `L ${x},${y}`
    }).filter(p => p !== "").join(" ")
    
    // 关键改进：使用品牌自己的最小值作为起始点
    // 这样确保小提琴的底部是尖的，头部也是尖的
    const startY = yScale(stats.min)
    const endY = yScale(stats.max) // 添加结束点
    if (isNaN(startY) || isNaN(endY)) return ""
    
    // 构建完整的SVG路径：从中心线的品牌最小值开始，到最大值结束
    return `M 0,${startY} ${points} L 0,${endY} Z`
  }

  const handleMouseMove = (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return
    
    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left
    const svgY = event.clientY - rect.top
    
    if (svgX >= margin.left && svgX <= margin.left + chartWidth && svgY >= margin.top && svgY <= margin.top + chartHeight) {
      const price = priceFromY(svgY)
      
      // 找到鼠标位置对应的品牌
      let hoveredBrandIndex = -1
      for (let i = 0; i < violinData.length; i++) {
        const brandX = violinData[i].x
        if (svgX >= brandX - maxViolinHalfWidth && svgX <= brandX + maxViolinHalfWidth) {
          hoveredBrandIndex = i
          break
        }
      }
      
      if (hoveredBrandIndex >= 0) {
        const brand = violinData[hoveredBrandIndex]

        // 计算当前价格区间
        const priceWindow = Math.max((globalMax - globalMin) * priceWindowPercentage, 1) // 最小窗口为1
        const priceRangeMin = Math.max(price - priceWindow / 2, brand.stats.min)
        const priceRangeMax = Math.min(price + priceWindow / 2, brand.stats.max)

        // 计算当前价格区间内的产品数量
        const priceRangeProductCount = countProductsInPriceRange(
          brand.prices,
          priceRangeMin,
          priceRangeMax
        )

        setHoverState({
          x: svgX,
          y: svgY,
          price: price,
          brand: brand.name,
          products: brand.stats.count,
          priceRangeProductCount: priceRangeProductCount,
          priceRange: { min: priceRangeMin, max: priceRangeMax },
          visible: true,
          brandIndex: hoveredBrandIndex
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

  const handleClick = async (event: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return

    const rect = svgRef.current.getBoundingClientRect()
    const svgX = event.clientX - rect.left

    if (svgX >= margin.left && svgX <= margin.left + chartWidth) {
      // 找到点击的品牌
      for (let i = 0; i < violinData.length; i++) {
        const brandX = violinData[i].x
        if (svgX >= brandX - maxViolinHalfWidth && svgX <= brandX + maxViolinHalfWidth) {
          const brandName = violinData[i].name

          // 根据筛选模式选择不同的处理方式
          if (filterMode === 'extend_fields' && extendFieldsConfig) {
            // 使用扩展字段筛选
            await handleMultipleFiltersClick(
              projectId,
              {
                brands: [brandName],
                extend_fields: {
                  [extendFieldsConfig.field]: extendFieldsConfig.value
                }
              },
              `${brandName} ${extendFieldsConfig.value} Products`,
              `${brandName} products with ${extendFieldsConfig.value} capability`,
              { brand: false, category: true, priceRange: true, packSize: true }
            )
          } else {
            // 使用传统的 category + brand 筛选
            await handleBrandViolinClick(
              projectId,
              brandName,
              category,
              `${brandName} Products`,
              `${brandName} products in ${category}`
            )
          }
          break
        }
      }
    }
  }

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

  if (chartWidth === 0 || chartHeight === 0) {
    return (
      <div className="h-full relative" ref={containerRef} />
    )
  }

  return (
    <div className="h-full relative" ref={containerRef}>
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

          {/* 🎻 绘制品牌小提琴图形 */}
          {violinData.map((brand) => (
            <g key={brand.name} transform={`translate(${brand.x}, 0)`}>
              {/* 绘制小提琴的左半边 */}
              <path 
                d={createViolinPath(brand.density, brand.stats, 'left')} 
                fill={brand.color} 
                fillOpacity="0.7" 
                stroke={brand.color} 
                strokeWidth="1" 
              />
              {/* 绘制小提琴的右半边 */}
              <path 
                d={createViolinPath(brand.density, brand.stats, 'right')} 
                fill={brand.color} 
                fillOpacity="0.7" 
                stroke={brand.color} 
                strokeWidth="1" 
              />
              {/* 📊 绘制中位数线（紫色虚线）- 长度根据该价格处的小提琴宽度调整 */}
              <line 
                x1={-brand.getDensityWidth(brand.stats.median)} 
                y1={yScale(brand.stats.median)} 
                x2={brand.getDensityWidth(brand.stats.median)} 
                y2={yScale(brand.stats.median)} 
                stroke="#7c3aed" 
                strokeWidth="3" 
                strokeDasharray="8,4" 
              />
              {/* 📈 绘制均值线（绿色虚线）- 长度根据该价格处的小提琴宽度调整 */}
              <line 
                x1={-brand.getDensityWidth(brand.stats.mean)} 
                y1={yScale(brand.stats.mean)} 
                x2={brand.getDensityWidth(brand.stats.mean)} 
                y2={yScale(brand.stats.mean)} 
                stroke="#059669" 
                strokeWidth="2" 
                strokeDasharray="4,4" 
              />
            </g>
          ))}

          {/* Crosshair */}
          {hoverState.visible && hoverState.brandIndex >= 0 && (
            <g>
              <line 
                x1={violinData[hoverState.brandIndex].x - violinData[hoverState.brandIndex].getDensityWidth(hoverState.price)} 
                y1={hoverState.y} 
                x2={violinData[hoverState.brandIndex].x + violinData[hoverState.brandIndex].getDensityWidth(hoverState.price)} 
                y2={hoverState.y} 
                stroke="#dc2626" 
                strokeWidth="2" 
                opacity="0.9" 
              />
            </g>
          )}

          {/* X-axis labels */}
          {violinData.map((brand) => (
            <text 
              key={brand.name}
              x={brand.x} 
              y={margin.top + chartHeight + 20} 
              textAnchor="middle" 
              fontSize="11" 
              fill="#64748b"
              transform={`rotate(-45, ${brand.x}, ${margin.top + chartHeight + 20})`}
            >
              {brand.name}
            </text>
          ))}

          {/* Legend */}
          <g transform={`translate(${margin.left + 620}, ${margin.top - 35})`}>
            <rect x="0" y="0" width="120" height="55" fill="white" fillOpacity="0.9" stroke="#e5e7eb" strokeWidth="1" rx="4" />
            <line x1="10" y1="20" x2="25" y2="20" stroke="#7c3aed" strokeWidth="3" strokeDasharray="8,4" />
            <text x="30" y="23" fontSize="11" fill="#374151">Median</text>
            <line x1="10" y1="35" x2="25" y2="35" stroke="#059669" strokeWidth="2" strokeDasharray="4,4" />
            <text x="30" y="38" fontSize="11" fill="#374151">Mean</text>
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
            <div className="text-sm font-medium text-gray-800">{hoverState.brand}</div>
            <div className="text-xs text-gray-600 mt-1">Price: ${hoverState.price.toFixed(2)}</div>
            <div className="mt-1 text-xs">
              <div className="font-medium text-blue-600">
                Price range ${hoverState.priceRange.min.toFixed(2)} - ${hoverState.priceRange.max.toFixed(2)}: {hoverState.priceRangeProductCount} products
              </div>
              <div className="text-gray-500">
                Total in brand: {hoverState.products} products
              </div>
            </div>
          </div>
        )}
    </div>
  )
}


