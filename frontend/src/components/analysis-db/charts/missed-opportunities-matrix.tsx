"use client"

import { useMemo } from "react"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"
import { Tooltip } from "@/components/ui/tooltip"
import { DetailedTooltip } from "@/components/ui/detailed-tooltip"
// allReviewData now passed as prop instead of imported

interface UseCaseData {
  product: string;
  useCase: string;
  mentions: number;
  satisfactionRate: number;
  positiveCount: number;
  negativeCount: number;
  totalReviews: number;
  gapLevel: number;
}

interface UseCaseMatrixProps {
  data: UseCaseData[];
  targetProducts: string[];
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
  reviewContent?: Record<string, Array<{
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
  asinToFullProductNameMap?: Record<string, string>;
}

export function MissedOpportunitiesMatrix({ data, targetProducts, allReviewData, reviewContent, asinToProductNameMap, asinToFullProductNameMap }: UseCaseMatrixProps) {
  const { openPanel } = useReviewPanel()
  
  const handleCellClick = (useCase: string, productAsin: string, cellData: UseCaseData | null) => {
    if (!cellData || cellData.mentions === 0) return
    
    // Try to get reviews from the new materialized view review content first
    const reviewKey = `${productAsin}_${useCase}`
    let reviewsToShow: Array<{
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
    
    if (reviewContent && reviewContent[reviewKey]) {
      // Use the new materialized view review content
      reviewsToShow = reviewContent[reviewKey]
      console.log(`Using materialized view reviews for ${reviewKey}: ${reviewsToShow.length} reviews`)
    } else if (allReviewData && allReviewData[useCase]) {
      // Fallback to the old allReviewData method
      const categoryReviews = allReviewData[useCase] || []
      if (categoryReviews.length > 0) {
        // Filter reviews by specific product using ASIN directly
        const productReviews = categoryReviews.filter(review => review.productId === productAsin)
        reviewsToShow = productReviews.length > 0 ? productReviews : categoryReviews
        console.log(`Using fallback allReviewData for ${useCase}: ${reviewsToShow.length} reviews`)
      }
    }
    
    if (reviewsToShow.length === 0) {
      console.warn(`No review data found for ${productAsin}-${useCase}`)
      return
    }
    
    const productName = asinToProductNameMap?.[productAsin] || productAsin
    
    openPanel(
      reviewsToShow, 
      `${useCase} Reviews`, 
      `${productName} • ${cellData.mentions} reviews • ${cellData.satisfactionRate}% satisfaction`,
      { sentiment: true, brand: true, rating: true, verified: true }
    )
  }
  
  const orderedProducts = useMemo(() => {
    // Keep original order from targetProducts
    return targetProducts
  }, [targetProducts])

  const useCaseMatrixData = useMemo(() => {
    // Get use cases in the order they appear in the data (already ranked by backend)
    const useCaseOrder: string[] = []
    const seenUseCases = new Set<string>()
    
    // Preserve the order from the first product (use cases are ranked by average mention ratio)
    const firstProduct = orderedProducts[0]
    data.filter(item => item.product === firstProduct).forEach(item => {
      if (!seenUseCases.has(item.useCase)) {
        useCaseOrder.push(item.useCase)
        seenUseCases.add(item.useCase)
      }
    })
    
    // Add any remaining use cases that might not be in the first product
    data.forEach(item => {
      if (!seenUseCases.has(item.useCase)) {
        useCaseOrder.push(item.useCase)
        seenUseCases.add(item.useCase)
      }
    })
    
    // Create matrix structure preserving the ranked order
    const matrix = useCaseOrder.map(useCase => {
      const row = { useCase, cells: {} as Record<string, UseCaseData | null> }
      
      // Fill cells for each product in the ordered list
      orderedProducts.forEach(product => {
        const cellData = data.find(item => item.product === product && item.useCase === useCase)
        row.cells[product] = cellData || null
      })
      
      return row
    })
    
    return matrix
  }, [data, orderedProducts])

  const getSatisfactionColor = (satisfactionRate: number, totalReviews: number, mentions: number) => {
    // If no mentions at all, show gray
    if (mentions === 0) return 'bg-gray-100 text-gray-400'
    
    // If mentions but no detailed reviews, show light blue
    if (totalReviews === 0) return 'bg-blue-50 text-blue-700'
    
    // If we have detailed reviews, use satisfaction-based colors
    if (satisfactionRate >= 85) return 'bg-green-100 text-green-800'
    else if (satisfactionRate >= 70) return 'bg-yellow-100 text-yellow-800'
    else if (satisfactionRate >= 60) return 'bg-orange-100 text-orange-800'
    else return 'bg-red-100 text-red-800'
  }

  const getHeaderColor = (productAsin: string) => {
    // Simple color scheme for differentiation
    const productName = asinToProductNameMap?.[productAsin] || productAsin
    if (productName.toLowerCase().includes('leviton')) {
      return 'bg-slate-100 text-slate-800' // Very light greyish blue for Leviton
    } else {
      return 'bg-amber-50 text-amber-800' // Light greyish yellow for other brands
    }
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-full">
        <table className="w-full border-collapse border border-gray-300">
          <thead>
            <tr className="bg-gray-50">
              <th className="border border-gray-300 p-3 text-left font-semibold text-gray-900 min-w-[250px]">
                Use Cases
              </th>
              {orderedProducts.map(productAsin => {
                const productName = asinToProductNameMap?.[productAsin] || productAsin
                const fullProductName = asinToFullProductNameMap?.[productAsin] || productName
                return (
                  <th key={productAsin} className={`border border-gray-300 p-3 text-center font-semibold min-w-[140px] ${getHeaderColor(productAsin)}`}>
                    <Tooltip content={fullProductName}>
                      <div className="text-sm">{productName}</div>
                    </Tooltip>
                  </th>
                )
              })}
            </tr>
          </thead>
          <tbody>
            {useCaseMatrixData.map((row) => (
              <tr key={row.useCase}>
                <td className="border border-gray-300 p-3 bg-gray-50 font-medium text-gray-900">
                  <div className="flex flex-col">
                    <span className="text-sm">{row.useCase}</span>
                  </div>
                </td>
                {orderedProducts.map(productAsin => {
                  const cellData = row.cells[productAsin]
                  
                  // Show N/A only if no data exists or no mentions at all
                  if (!cellData || cellData.mentions === 0) {
                    return (
                      <td key={productAsin} className="border border-gray-300 p-3 text-center">
                        <div className="bg-gray-100 text-gray-400 py-2 px-3 rounded text-sm">
                          N/A
                        </div>
                      </td>
                    )
                  }
                  
                  const productName = asinToProductNameMap?.[productAsin] || productAsin
                  
                  return (
                    <td key={productAsin} className="border border-gray-300 p-3 text-center">
                      <DetailedTooltip
                        content={{
                          title: row.useCase,
                          positiveCount: cellData.positiveCount,
                          negativeCount: cellData.negativeCount,
                          totalMentions: cellData.mentions,
                          satisfactionRate: cellData.satisfactionRate,
                          additionalInfo: [
                            `Product: ${productName}`,
                            `Total reviews analyzed: ${cellData.totalReviews}`,
                            `Gap Level: ${cellData.gapLevel}`
                          ]
                        }}
                      >
                        <div 
                          className={`matrix-cell py-2 px-3 rounded text-sm font-semibold ${getSatisfactionColor(cellData.satisfactionRate, cellData.totalReviews, cellData.mentions)} cursor-pointer`}
                          onClick={() => handleCellClick(row.useCase, productAsin, cellData)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              handleCellClick(row.useCase, productAsin, cellData)
                            }
                          }}
                          tabIndex={0}
                          role="button"
                          aria-label={`View reviews for ${row.useCase} - ${productName}: ${cellData.mentions} mentions, ${cellData.satisfactionRate}% satisfaction`}
                        >
                          <div className="text-lg font-bold">
                            {cellData.mentions}
                          </div>
                        </div>
                      </DetailedTooltip>
                    </td>
                  )
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
} 