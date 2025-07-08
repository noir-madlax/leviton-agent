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
import { ProductPainPoint, getSatisfactionColor } from "@/components/analysis-db/types/analysis"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"

interface CustomerSentimentBarProps {
  data: ProductPainPoint[]
  productTotalReviews: Record<string, number>
  allReviewData?: Record<string, Array<{
    id: string
    productId: string
    text: string
    sentiment: 'positive' | 'negative' | 'neutral'
    category: string
    aspect: string
    rating: number
    verified: boolean
    date: string
    brand: string
  }>>
  asinToProductNameMap?: Record<string, string>;
}

interface SentimentData {
  product: string
  productName: string
  totalReviews: number
  avgSatisfactionRate: number
  color: string
  totalMentions: number
  useCaseMentions: number
}

export function CustomerSentimentBar({ data, productTotalReviews, allReviewData, asinToProductNameMap }: CustomerSentimentBarProps) {
  const { openPanel } = useReviewPanel()
  
  const handleBarClick = (sentimentData: SentimentData) => {
    // Add null check for allReviewData
    if (!allReviewData) {
      console.warn('No review data available')
      return
    }
    
    // Get reviews for this specific product using ASIN directly
    const allProductReviews: Array<{
      id: string
      productId: string
      text: string
      sentiment: 'positive' | 'negative' | 'neutral'
      category: string
      aspect: string
      rating: number
      verified: boolean
      date: string
      brand: string
    }> = []
    
    // Collect all reviews for this specific product from all categories
    Object.entries(allReviewData).forEach(([, reviews]) => {
      const productReviews = reviews.filter(review => review.productId === sentimentData.product)
      allProductReviews.push(...productReviews)
    })
    
    if (allProductReviews.length === 0) return
    
    const productName = asinToProductNameMap?.[sentimentData.product] || sentimentData.product
    
    openPanel(
      allProductReviews,
      `${productName} Reviews`,
      `All reviews • ${sentimentData.totalReviews} total reviews in dataset • ${allProductReviews.length} product-specific reviews found • ${sentimentData.avgSatisfactionRate}% avg satisfaction`,
      { sentiment: true, brand: true, rating: true, verified: true }
    )
  }
  
  const sentimentData = useMemo(() => {
    if (!data || data.length === 0) return []

    // Keep original order from productTotalReviews
    const allProducts = Object.keys(productTotalReviews)

    // Group pain point data by product
    const productGroups = data.reduce((groups, item) => {
      if (!groups[item.product]) {
        groups[item.product] = []
      }
      groups[item.product].push(item)
      return groups
    }, {} as Record<string, ProductPainPoint[]>)

    // Calculate sentiment data for each product in the specified order
    const sentimentArray: SentimentData[] = allProducts.map(productAsin => {
      const totalReviews = productTotalReviews[productAsin] || 0
      const painPointItems = productGroups[productAsin] || []
      const productName = asinToProductNameMap?.[productAsin] || productAsin
      
      // Calculate total mentions across all categories (pain points only for now)
      const painPointMentions = painPointItems.reduce((sum, item) => sum + item.mentions, 0)
      const totalMentions = painPointMentions
      
      // Calculate weighted average satisfaction across all aspects (pain points only)
      let weightedSatisfaction = 0
      let totalWeightedMentions = 0
      
      // Add pain point satisfaction (weighted by mentions)
      painPointItems.forEach(item => {
        if (item.mentions > 0 && item.totalReviews > 0) {
          weightedSatisfaction += item.satisfactionRate * item.mentions
          totalWeightedMentions += item.mentions
        }
      })
      
      const avgSatisfactionRate = totalWeightedMentions > 0 ? weightedSatisfaction / totalWeightedMentions : 0

      return {
        product: productAsin,
        productName,
        totalReviews,
        avgSatisfactionRate: Math.round(avgSatisfactionRate * 10) / 10,
        color: getSatisfactionColor(avgSatisfactionRate),
        totalMentions,
        useCaseMentions: 0 // No use case data for now
      }
    })

    return sentimentArray
  }, [data, productTotalReviews, asinToProductNameMap])

  // Format product names for display
  const formatProductName = (name: string) => {
    // Truncate long names and add line breaks for better display
    if (name.length > 25) {
      return name.substring(0, 25) + '...'
    }
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
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: SentimentData }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as SentimentData
      return (
        <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg">
          <p className="font-semibold text-gray-800">{data.productName}</p>
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
              <span>Total Mentions:</span>
              <span className="font-medium">{data.totalMentions}</span>
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
                dataKey="productName"
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
          {sentimentData.map((item) => (
            <div key={item.product} className={`text-center ${getHeaderColor(item.productName)}`}>
              <div className="font-semibold" title={item.productName}>{formatProductName(item.productName)}</div>
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
                return `${mostReviewed?.productName || ''} (${mostReviewed?.totalReviews || 0} reviews)`
              })()}
            </div>
          </div>
          <div className="p-3 bg-green-50 rounded-lg">
            <div className="font-semibold text-green-800 mb-1">Highest Satisfaction</div>
            <div className="text-green-600">
              {(() => {
                const bestSatisfaction = sentimentData.reduce((best, curr) => 
                  curr.avgSatisfactionRate > best.avgSatisfactionRate ? curr : best, sentimentData[0])
                return `${bestSatisfaction?.productName || ''} (${bestSatisfaction?.avgSatisfactionRate || 0}%)`
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