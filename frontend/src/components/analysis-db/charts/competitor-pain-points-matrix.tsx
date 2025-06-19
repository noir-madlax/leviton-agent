"use client"

import { useMemo } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { 
  ResponsiveContainer, 
  Scatter, 
  ScatterChart, 
  XAxis, 
  YAxis, 
  Tooltip
} from "recharts"
import { ProductPainPoint, getSatisfactionColor, getBubbleSize } from "@/components/analysis-db/data/competitor-analysis"

interface CompetitorPainPointsMatrixProps {
  data: ProductPainPoint[]
}

interface ProcessedDataPoint {
  product: string
  category: string
  categoryType: string
  mentions: number
  satisfactionRate: number
  positiveCount: number
  negativeCount: number
  totalReviews: number
  x: number  // 产品索引
  y: number  // 分类索引
  z: number  // 气泡大小
}

export function CompetitorPainPointsMatrix({ data }: CompetitorPainPointsMatrixProps) {
  const handleDotClick = (data: any) => {
    if (data && data.payload) {
      console.log('Competitor pain points matrix clicked:', data.payload)
    }
  }
  
  // 处理数据，转换为矩阵格式
  const processedData = useMemo(() => {
    if (!data || data.length === 0) return { chartData: [], products: [], categories: [], maxMentions: 1 }

    // 获取所有唯一的产品和分类
    const products = Array.from(new Set(data.map(d => d.product))).sort()
    const categories = Array.from(new Set(data.map(d => d.category))).sort()
    const maxMentions = Math.max(...data.map(d => d.mentions))

    // 创建矩阵数据点
    const chartData: ProcessedDataPoint[] = []
    
    products.forEach((product, productIndex) => {
      categories.forEach((category, categoryIndex) => {
        const dataPoint = data.find(d => d.product === product && d.category === category)
        if (dataPoint && dataPoint.mentions > 0) {
          chartData.push({
            ...dataPoint,
            x: productIndex,
            y: categoryIndex,
            z: getBubbleSize(dataPoint.mentions, maxMentions)
          })
        }
      })
    })

    return { chartData, products, categories, maxMentions }
  }, [data])

  // 自定义Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ProcessedDataPoint
      return (
        <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800">{data.product}</p>
          <p className="text-sm text-gray-600 mb-2">{data.category}</p>
          <div className="space-y-1 text-xs">
            <div className="flex justify-between">
              <span>Mentions:</span>
              <span className="font-medium">{data.mentions}</span>
            </div>
            <div className="flex justify-between">
              <span>Satisfaction:</span>
              <span className="font-medium">{data.satisfactionRate}%</span>
            </div>
            <div className="flex justify-between">
              <span>Positive:</span>
              <span className="font-medium text-green-600">{data.positiveCount}</span>
            </div>
            <div className="flex justify-between">
              <span>Negative:</span>
              <span className="font-medium text-red-600">{data.negativeCount}</span>
            </div>
            <div className="flex justify-between">
              <span>Total Reviews:</span>
              <span className="font-medium">{data.totalReviews}</span>
            </div>
            <div className="flex justify-between">
              <span>Type:</span>
              <span className="font-medium">{data.categoryType}</span>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  // 自定义点渲染
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props
    if (!payload) return null
    
    const color = getSatisfactionColor(payload.satisfactionRate)
    const size = payload.z
    
    return (
      <circle
        cx={cx}
        cy={cy}
        r={size / 2}
        fill={color}
        fillOpacity={0.7}
        stroke={color}
        strokeWidth={1}
        style={{ cursor: 'pointer' }}
      />
    )
  }

  // 格式化产品名称，显示简短但有意义的名称
  const formatProductName = (name: string) => {
    // 提取主要品牌和型号信息
    if (name.includes('Leviton D26HD')) return 'Leviton D26HD'
    if (name.includes('Leviton D215S')) return 'Leviton D215S'  
    if (name.includes('Lutron Caseta Diva')) return 'Lutron Caseta'
    if (name.includes('TP Link Switch')) return 'TP Link'
    if (name.includes('Lutron Diva')) return 'Lutron Diva'
    // 如果都不匹配，显示前15个字符
    return name.length > 15 ? name.substring(0, 15) + '...' : name
  }

  // 格式化分类名称，缩短过长的名称  
  const formatCategoryName = (name: string) => {
    if (name.length > 20) {
      return name.substring(0, 20) + '...'
    }
    return name
  }

  if (processedData.chartData.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-gray-500">No data available for the selected filter.</p>
        </CardContent>
      </Card>
    )
  }

  // 生成所有产品位置的ticks
  const xAxisTicks = processedData.products.map((_, index) => index)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Competitor Pain Points Matrix</span>
          <div className="text-sm text-gray-600">
            {processedData.chartData.length} data points
          </div>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {/* 图例说明 */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-sm text-gray-800 mb-3">How to Read This Chart:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <div className="flex items-center space-x-2 mb-2">
                <div className="w-4 h-4 rounded-full bg-gray-300"></div>
                <span><strong>Bubble Size:</strong> Number of mentions (larger = more mentions)</span>
              </div>
              <div className="flex items-center space-x-2">
                <div className="flex space-x-1">
                  <div className="w-3 h-3 rounded-full bg-red-500"></div>
                  <div className="w-3 h-3 rounded-full bg-orange-500"></div>
                  <div className="w-3 h-3 rounded-full bg-yellow-500"></div>
                  <div className="w-3 h-3 rounded-full bg-green-500"></div>
                </div>
                <span><strong>Color:</strong> Satisfaction rate (red=low, green=high)</span>
              </div>
            </div>
            <div className="text-gray-600">
              <p><strong>X-axis:</strong> Product names</p>
              <p><strong>Y-axis:</strong> Pain point categories</p>
            </div>
          </div>
        </div>

        {/* 图表 */}
        <div className="h-[700px] w-full flex justify-center">
          <div className="w-full max-w-6xl">
            <ResponsiveContainer width="100%" height="100%">
              <ScatterChart
                data={processedData.chartData}
                margin={{ top: 40, right: 100, bottom: 160, left: 10 }}
              >
                <XAxis
                  type="number"
                  dataKey="x"
                  domain={[-0.5, processedData.products.length - 0.5]}
                  ticks={xAxisTicks}
                  tickFormatter={(value) => {
                    const productIndex = Math.round(value)
                    const product = processedData.products[productIndex]
                    return product ? formatProductName(product) : ''
                  }}
                  interval={0}
                  angle={-45}
                  textAnchor="end"
                  height={140}
                  fontSize={12}
                  tick={{ fontSize: 12, fill: '#374151' }}
                />
                <YAxis
                  type="number"
                  dataKey="y"
                  domain={[-0.5, processedData.categories.length - 0.5]}
                  tickFormatter={(value) => {
                    const category = processedData.categories[Math.round(value)]
                    return category ? formatCategoryName(category) : ''
                  }}
                  interval={0}
                  width={190}
                  fontSize={12}
                  tick={{ fontSize: 12, fill: '#374151' }}
                />
                <Tooltip content={<CustomTooltip />} />
                <Scatter
                  dataKey="z"
                  data={processedData.chartData}
                  shape={<CustomDot />}
                  onClick={handleDotClick}
                  style={{ cursor: 'pointer' }}
                />
              </ScatterChart>
            </ResponsiveContainer>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 