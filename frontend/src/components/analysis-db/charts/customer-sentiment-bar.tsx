"use client"

import { useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { 
  ResponsiveContainer, 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  Tooltip, 
  Cell
} from "recharts"
import { ProductPainPoint, getSatisfactionColor, getUseCaseAnalysisData } from "@/components/analysis-db/data/competitor-analysis"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"
import { allReviewData } from "@/components/analysis-db/data/review-data"

interface CustomerSentimentBarProps {
  data: ProductPainPoint[]
  productTotalReviews: Record<string, number>
}

interface SentimentData {
  product: string
  totalReviews: number
  avgSatisfactionRate: number
  color: string
  totalMentions: number
  useCaseMentions: number
}

export function CustomerSentimentBar({ data, productTotalReviews }: CustomerSentimentBarProps) {
  const { openPanel } = useReviewPanel()
  
  // Map product names to their ASINs for precise filtering
  const productToAsin: Record<string, string> = {
    'Leviton D26HD': 'B0BVKYKKRK',
    'Leviton D215S': 'B0BVKZLT3B', 
    'Lutron Caseta Diva': 'B0BSHKS26L',
    'TP Link Switch': 'B01EZV35QU',
    'Leviton DSL06': 'B00NG0ELL0',
    'Lutron Diva': 'B085D8M2MR'
  }
  
  const handleBarClick = (sentimentData: SentimentData) => {
    // Add null check for allReviewData
    if (!allReviewData) {
      console.warn('No review data available')
      return
    }
    
    // Get reviews for this specific product using ASIN
    const productAsin = productToAsin[sentimentData.product]
    const allProductReviews: any[] = []
    
    if (productAsin) {
      // Collect all reviews for this specific product from all categories
      Object.entries(allReviewData).forEach(([, reviews]) => {
        const productReviews = reviews.filter(review => review.productId === productAsin)
        allProductReviews.push(...productReviews)
      })
    }
    
    if (allProductReviews.length === 0) return
    
    openPanel(
      allProductReviews,
      `${sentimentData.product} Reviews`,
      `All reviews • ${sentimentData.totalReviews} total reviews in dataset • ${allProductReviews.length} product-specific reviews found • ${sentimentData.avgSatisfactionRate}% avg satisfaction`,
      { sentiment: true, brand: true, rating: true, verified: true }
    )
  }
  
  const sentimentData = useMemo(() => {
    if (!data || data.length === 0) return []

    // Get use case data to include in satisfaction calculation
    const useCaseData = getUseCaseAnalysisData()
    
    // Group products in the same order as matrices: Leviton first, then others
    const allProducts = Object.keys(productTotalReviews)
    const levitonProducts = allProducts.filter(product => product.startsWith('Leviton'))
    const otherProducts = allProducts.filter(product => !product.startsWith('Leviton'))
    const orderedProducts = [...levitonProducts, ...otherProducts]

    // Group pain point data by product
    const productGroups = data.reduce((groups, item) => {
      if (!groups[item.product]) {
        groups[item.product] = []
      }
      groups[item.product].push(item)
      return groups
    }, {} as Record<string, ProductPainPoint[]>)

    // Group use case data by product
    const useCaseGroups = useCaseData.matrixData.reduce((groups, item) => {
      if (!groups[item.product]) {
        groups[item.product] = []
      }
      groups[item.product].push(item)
      return groups
    }, {} as Record<string, any[]>)

    // Calculate sentiment data for each product in the specified order
    const sentimentArray: SentimentData[] = orderedProducts.map(product => {
      const totalReviews = productTotalReviews[product] || 0
      const painPointItems = productGroups[product] || []
      const useCaseItems = useCaseGroups[product] || []
      
      // Calculate total mentions across all categories (pain points + use cases)
      const painPointMentions = painPointItems.reduce((sum, item) => sum + item.mentions, 0)
      const useCaseMentions = useCaseItems.reduce((sum, item) => sum + item.mentions, 0)
      const totalMentions = painPointMentions + useCaseMentions
      
      // Calculate weighted average satisfaction across all aspects (pain points + use cases)
      let weightedSatisfaction = 0
      let totalWeightedMentions = 0
      
      // Add pain point satisfaction (weighted by mentions)
      painPointItems.forEach(item => {
        if (item.mentions > 0 && item.totalReviews > 0) {
          weightedSatisfaction += item.satisfactionRate * item.mentions
          totalWeightedMentions += item.mentions
        }
      })
      
      // Add use case satisfaction (weighted by mentions)
      useCaseItems.forEach(item => {
        if (item.mentions > 0 && item.totalReviews > 0) {
          weightedSatisfaction += item.satisfactionRate * item.mentions
          totalWeightedMentions += item.mentions
        }
      })
      
      const avgSatisfactionRate = totalWeightedMentions > 0 ? weightedSatisfaction / totalWeightedMentions : 0

      return {
        product,
        totalReviews,
        avgSatisfactionRate: Math.round(avgSatisfactionRate * 10) / 10,
        color: getSatisfactionColor(avgSatisfactionRate),
        totalMentions,
        useCaseMentions
      }
    })

    return sentimentArray
  }, [data, productTotalReviews])

  // Format product names for display
  const formatProductName = (name: string) => {
    if (name.includes('Leviton D26HD')) return 'Leviton\nD26HD'
    if (name.includes('Leviton D215S')) return 'Leviton\nD215S'  
    if (name.includes('Leviton DSL06')) return 'Leviton\nDSL06'
    if (name.includes('Lutron Caseta Diva')) return 'Lutron\nCaseta Diva'
    if (name.includes('TP Link Switch')) return 'TP Link\nSwitch'
    if (name.includes('Lutron Diva')) return 'Lutron\nDiva'
    return name
  }

  // Get header color based on product type
  const getHeaderColor = (product: string) => {
    if (product.startsWith('Leviton')) {
      return 'text-slate-700' // Leviton products
    } else {
      return 'text-amber-700' // Other brands
    }
  }

  // Custom Tooltip
  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as SentimentData
      return (
        <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800">{data.product}</p>
          <div className="space-y-1 text-xs mt-2">
            <div className="flex justify-between">
              <span>Total Reviews:</span>
              <span className="font-medium">{data.totalReviews}</span>
            </div>
            <div className="flex justify-between">
              <span>Pain Point Mentions:</span>
              <span className="font-medium">{data.totalMentions - data.useCaseMentions}</span>
            </div>
            <div className="flex justify-between">
              <span>Use Case Mentions:</span>
              <span className="font-medium">{data.useCaseMentions}</span>
            </div>
            <div className="flex justify-between">
              <span>Avg Satisfaction:</span>
              <span className="font-medium">{data.avgSatisfactionRate}%</span>
            </div>
          </div>
        </div>
      )
    }
    return null
  }

  if (sentimentData.length === 0) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <p className="text-gray-500">No sentiment data available.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardContent className="p-6">
        {/* Color Legend */}
        <div className="mb-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold text-sm text-gray-800 mb-3">How to Read This Chart:</h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div>
              <p><strong>X-axis:</strong> Products (grouped by brand)</p>
              <p><strong>Y-axis:</strong> Total number of reviews</p>
              <p><strong>Bar Color:</strong> Average satisfaction rate across all aspects</p>
            </div>
            <div>
              <p className="font-medium mb-2">Color Legend - Satisfaction Rate:</p>
              <div className="flex flex-wrap gap-2">
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 rounded bg-green-500"></div>
                  <span>85%+ (Green)</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 rounded bg-yellow-500"></div>
                  <span>70-84% (Yellow)</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 rounded bg-orange-500"></div>
                  <span>60-69% (Orange)</span>
                </div>
                <div className="flex items-center space-x-1">
                  <div className="w-4 h-4 rounded bg-red-500"></div>
                  <span>&lt;60% (Red)</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Vertical bar chart with products on X-axis, review count on Y-axis */}
        <div className="h-[500px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={sentimentData}
              margin={{ top: 20, right: 30, bottom: 80, left: 40 }}
            >
              <XAxis 
                dataKey="product"
                tickFormatter={formatProductName}
                tick={{ fontSize: 11, fill: '#374151' }}
                angle={0}
                textAnchor="middle"
                height={70}
                interval={0}
              />
              <YAxis 
                tick={{ fontSize: 12, fill: '#374151' }}
                label={{ value: 'Total Reviews', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="totalReviews" 
                radius={[4, 4, 0, 0]}
                onClick={(data) => handleBarClick(data)}
                style={{ cursor: 'pointer' }}
              >
                {sentimentData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Product headers with brand grouping */}
        <div className="mt-4 flex flex-wrap justify-center gap-4 text-xs">
          {sentimentData.map((item, index) => (
            <div key={item.product} className={`text-center ${getHeaderColor(item.product)}`}>
              <div className="font-semibold">{item.product}</div>
              <div className="text-gray-500">
                {item.totalReviews} reviews • {item.avgSatisfactionRate}% satisfaction
              </div>
            </div>
          ))}
        </div>

        {/* Summary statistics */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="font-semibold text-blue-800 mb-1">Most Reviewed Product</div>
            <div className="text-blue-600">
              {(() => {
                const mostReviewed = sentimentData.reduce((best, curr) => 
                  curr.totalReviews > best.totalReviews ? curr : best, sentimentData[0])
                return `${mostReviewed?.product || ''} (${mostReviewed?.totalReviews || 0} reviews)`
              })()}
            </div>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <div className="font-semibold text-green-800 mb-1">Highest Satisfaction</div>
            <div className="text-green-600">
              {(() => {
                const bestSatisfaction = sentimentData.reduce((best, curr) => 
                  curr.avgSatisfactionRate > best.avgSatisfactionRate ? curr : best, sentimentData[0])
                return `${bestSatisfaction?.product || ''} (${bestSatisfaction?.avgSatisfactionRate || 0}%)`
              })()}
            </div>
          </div>
          <div className="p-3 bg-purple-50 rounded-lg">
            <div className="font-semibold text-purple-800 mb-1">Total Analysis</div>
            <div className="text-purple-600">
              {sentimentData.reduce((sum, item) => sum + item.totalReviews, 0)} reviews • {' '}
              {sentimentData.reduce((sum, item) => sum + item.totalMentions, 0)} mentions
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 