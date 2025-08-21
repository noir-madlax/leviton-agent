"use client"

import { useMemo } from "react"
import { Card, CardContent } from "@/components/ui/card"
import { 
  ResponsiveContainer, 
  ScatterChart, 
  Scatter, 
  XAxis, 
  YAxis, 
  CartesianGrid,
  Tooltip, 
  Legend
} from "recharts"
import { ProductPainPoint } from "@/components/analysis-db/types/analysis"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"
import { getChartColor } from "@/components/analysis-db/shared/chart-colors"

interface CustomerSentimentScatterProps {
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
  asinToProductNameMap?: Record<string, string>
  asinToBrandMap?: Record<string, string>
}

interface ScatterData {
  product: string
  productName: string
  reviewCount: number
  avgRating: number
  brand: string
  color: string
}

// Extract brand from product name or ASIN (fallback only)
const extractBrandFromProduct = (productAsin: string, productName: string): string => {
  // ASIN to brand mapping for common products
  const asinToBrand: Record<string, string> = {
    'B073H9Y7SH': 'Leviton',
    'B00A92MQ38': 'Leviton',
    'B0CHMQW45X': 'Kasa Smart',
    'B087CXBQZR': 'Kasa Smart',
    'B07HBQBG6R': 'Kasa Smart',
    'B08B1XLQG7': 'Kasa Smart',
    'B0C7KTMQGR': 'Kasa Smart',
    'B0CGQX7LV8': 'Kasa Smart',
    'B0C7KQK7KN': 'Kasa Smart',
  }
  
  if (asinToBrand[productAsin]) {
    return asinToBrand[productAsin]
  }
  
  // Try to extract brand from product name
  const lowerName = productName.toLowerCase()
  if (lowerName.includes('leviton')) return 'Leviton'
  if (lowerName.includes('kasa')) return 'Kasa Smart'
  if (lowerName.includes('treatlife')) return 'TREATLIFE'
  if (lowerName.includes('tp-link')) return 'TP-Link'
  if (lowerName.includes('lutron')) return 'Lutron'
  if (lowerName.includes('ge ')) return 'GE'
  if (lowerName.includes('elegrp')) return 'ELEGRP'
  if (lowerName.includes('bestten')) return 'BESTTEN'
  if (lowerName.includes('enerlites')) return 'ENERLITES Store'
  if (lowerName.includes('amazon')) return 'Amazon'
  
  return 'Other'
}

export default function CustomerSentimentScatter({ 
  data, 
  productTotalReviews, 
  allReviewData,
  asinToProductNameMap,
  asinToBrandMap
}: CustomerSentimentScatterProps) {
  const { openPanel } = useReviewPanel()
  
  const handleDotClick = (scatterData: ScatterData) => {
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
      const productReviews = reviews.filter(review => review.productId === scatterData.product)
      allProductReviews.push(...productReviews)
    })

    if (allProductReviews.length === 0) return

    const productName = asinToProductNameMap?.[scatterData.product] || scatterData.product
    
    // 🆕 为现有数据添加aspects字段并设置正确的category (参考图1实现)
    const reviewsWithAspects = allProductReviews.map(review => ({
      ...review,
      category: review.aspect || review.category, // ✅ 设置为具体的aspect名称作为category显示
      aspects: review.aspect ? [{
        description: review.aspect,
        sentiment: review.sentiment,
        aspect_type: review.category || 'general'
      }] : []
    }))
    
    openPanel(
      reviewsWithAspects,
      `${productName} Reviews`,
      `${scatterData.brand} • ${scatterData.reviewCount} reviews • ${scatterData.avgRating.toFixed(1)} avg rating`,
      { 
        showFilters: { 
          causeAnalysis: true, 
          aspectType: true, 
          rating: true, 
          verified: true, 
          brand: false 
        } 
      }
    )
  }
  
  const scatterData = useMemo(() => {
    if (!data || data.length === 0 || !allReviewData) return []

    // Keep original order from productTotalReviews
    const allProducts = Object.keys(productTotalReviews)

    // Create a mapping from brand to color index
    const brandToColorIndex: Record<string, number> = {}
    let colorIndex = 0

    // Calculate scatter data for each product
    const scatterArray: ScatterData[] = []

    allProducts.forEach(productAsin => {
      const reviewCount = productTotalReviews[productAsin] || 0
      const productName = asinToProductNameMap?.[productAsin] || productAsin
      
      // Don't skip products with no reviews - instead use default values
      
      // Calculate average rating from allReviewData
      const allProductReviews: Array<{rating: number, brand: string}> = []
      
      Object.entries(allReviewData).forEach(([, reviews]) => {
        const productReviews = reviews.filter(review => review.productId === productAsin)
        allProductReviews.push(...productReviews)
      })
      
      let avgRating: number
      let brand: string
      
      if (allProductReviews.length === 0) {
        // If no reviews found in allReviewData, use defaults
        avgRating = 3.0 // Default rating
        // Use brand from asinToBrandMap first, then fallback to extraction
        brand = asinToBrandMap?.[productAsin] || extractBrandFromProduct(productAsin, productName)
      } else {
        // Calculate average rating
        const validRatings = allProductReviews.filter(review => review.rating && review.rating > 0)
        if (validRatings.length === 0) {
          avgRating = 3.0 // Default rating if no valid ratings
        } else {
          avgRating = validRatings.reduce((sum, review) => sum + review.rating, 0) / validRatings.length
        }
        
        // Get brand from the first review or use asinToBrandMap
        brand = asinToBrandMap?.[productAsin] || allProductReviews[0]?.brand || extractBrandFromProduct(productAsin, productName)
      }
      
      // Assign color index for this brand if not already assigned
      if (!(brand in brandToColorIndex)) {
        brandToColorIndex[brand] = colorIndex
        colorIndex++
      }
      
      scatterArray.push({
        product: productAsin,
        productName,
        reviewCount,
        avgRating: Math.round(avgRating * 10) / 10, // Round to 1 decimal place
        brand,
        color: getChartColor(brandToColorIndex[brand])
      })
    })

    return scatterArray
  }, [data, productTotalReviews, allReviewData, asinToProductNameMap, asinToBrandMap])

  // Group data by brand for multiple scatter series
  const brandGroupedData = useMemo(() => {
    const groups: Record<string, ScatterData[]> = {}
    
    scatterData.forEach(item => {
      if (!groups[item.brand]) {
        groups[item.brand] = []
      }
      groups[item.brand].push(item)
    })
    
    // Create brand to color index mapping based on the order brands appear in scatterData
    const brandToColorIndex: Record<string, number> = {}
    let colorIndex = 0
    
    scatterData.forEach(item => {
      if (!(item.brand in brandToColorIndex)) {
        brandToColorIndex[item.brand] = colorIndex
        colorIndex++
      }
    })

    return Object.entries(groups).map(([brand, products]) => ({
      brand,
      products,
      color: getChartColor(brandToColorIndex[brand])
    }))
  }, [scatterData])

  // Custom Tooltip
  const CustomTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ payload: ScatterData }> }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload as ScatterData
      return (
        <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg">
          <h4 className="font-semibold text-gray-800 mb-2">{data.productName}</h4>
          <p className="text-sm text-gray-600">
            <strong>Brand:</strong> {data.brand}
          </p>
          <p className="text-sm text-gray-600">
            <strong>Review Count:</strong> {data.reviewCount}
          </p>
          <p className="text-sm text-gray-600">
            <strong>Avg Rating:</strong> {data.avgRating} ⭐
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <Card className="w-full">
      <CardContent className="p-6">
        <div className="w-full h-96">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart
              margin={{ top: 20, right: 20, bottom: 20, left: 20 }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                type="number" 
                dataKey="reviewCount" 
                name="Review Count"
                domain={[0, 'dataMax']}
              />
              <YAxis 
                type="number" 
                dataKey="avgRating" 
                name="Average Star Rating"
                domain={[0, 5]}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              {brandGroupedData.map(({ brand, products, color }) => (
                <Scatter
                  key={brand}
                  name={brand}
                  data={products}
                  fill={color}
                  stroke={color}
                  strokeWidth={2}
                  onClick={handleDotClick}
                  cursor="pointer"
                  r={6}
                />
              ))}
            </ScatterChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
} 