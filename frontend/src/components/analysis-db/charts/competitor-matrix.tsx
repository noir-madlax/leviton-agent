"use client"

import { useMemo } from "react"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"
import { Tooltip } from "@/components/ui/tooltip"
import { DetailedTooltip } from "@/components/ui/detailed-tooltip"
// allReviewData now passed as prop instead of imported

interface MatrixData {
  product: string;
  category: string;
  categoryType: 'Physical' | 'Performance';
  mentions: number;
  satisfactionRate: number;
  positiveCount: number;
  negativeCount: number;
  totalReviews: number;
}

interface CompetitorMatrixProps {
  data: MatrixData[];
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
  asinToProductNameMap?: Record<string, string>;
  asinToFullProductNameMap?: Record<string, string>;
}

export function CompetitorMatrix({ data, targetProducts, allReviewData, asinToProductNameMap, asinToFullProductNameMap }: CompetitorMatrixProps) {
  const { openPanel } = useReviewPanel()
  
  const handleCellClick = (category: string, productAsin: string, cellData: MatrixData | null) => {
    if (!cellData || cellData.mentions === 0) return
    
    // Add null check for allReviewData and the specific category
    if (!allReviewData || !allReviewData[category]) {
      console.warn(`No review data found for category: ${category}`)
      return
    }
    
    const categoryReviews = allReviewData[category] || []
    if (categoryReviews.length === 0) return
    
    // Filter reviews by specific product using ASIN directly
    const productReviews = categoryReviews.filter(review => review.productId === productAsin)
    
    const reviewsToShow = productReviews.length > 0 ? productReviews : categoryReviews
    const productName = asinToProductNameMap?.[productAsin] || productAsin
    
    openPanel(
      reviewsToShow, 
      `${category} Reviews`, 
      `${productName} • ${cellData.mentions} reviews • ${cellData.satisfactionRate}% satisfaction`,
      { sentiment: true, brand: true, rating: true, verified: true }
    )
  }

  const orderedProducts = useMemo(() => {
    // Keep original order from targetProducts
    return targetProducts
  }, [targetProducts])

  const matrixData = useMemo(() => {
    // Get categories in the order they appear in the data (already ranked by backend)
    const categoryOrder: string[] = []
    const seenCategories = new Set<string>()
    
    // Preserve the order from the first product (categories are ranked by average mention ratio)
    const firstProduct = orderedProducts[0]
    data.filter(item => item.product === firstProduct).forEach(item => {
      if (!seenCategories.has(item.category)) {
        categoryOrder.push(item.category)
        seenCategories.add(item.category)
      }
    })
    
    // Add any remaining categories that might not be in the first product
    data.forEach(item => {
      if (!seenCategories.has(item.category)) {
        categoryOrder.push(item.category)
        seenCategories.add(item.category)
      }
    })
    
    // Create matrix structure preserving the ranked order
    const matrix = categoryOrder.map(category => {
      const row = { category, categoryType: '', cells: {} as Record<string, MatrixData | null> }
      
      // Find category type
      const categoryData = data.find(item => item.category === category)
      row.categoryType = categoryData?.categoryType || 'Physical'
      
      // Fill cells for each product in the new order
      orderedProducts.forEach(product => {
        const cellData = data.find(item => item.product === product && item.category === category)
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
                Dimensions
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
            {matrixData.map((row) => (
              <tr key={row.category}>
                <td className="border border-gray-300 p-3 bg-gray-50 font-medium text-gray-900">
                  <div className="flex flex-col">
                    <span className="text-sm">{row.category}</span>
                    <span className="text-xs text-gray-500 mt-1">
                      {row.categoryType}
                    </span>
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
                          title: row.category,
                          type: row.categoryType,
                          positiveCount: cellData.positiveCount,
                          negativeCount: cellData.negativeCount,
                          totalMentions: cellData.mentions,
                          satisfactionRate: cellData.satisfactionRate,
                          additionalInfo: [
                            `Product: ${productName}`,
                            `Total reviews analyzed: ${cellData.totalReviews}`
                          ]
                        }}
                      >
                        <div 
                          className={`matrix-cell py-2 px-3 rounded text-sm font-semibold ${getSatisfactionColor(cellData.satisfactionRate, cellData.totalReviews, cellData.mentions)} cursor-pointer`}
                          onClick={() => handleCellClick(row.category, productAsin, cellData)}
                          onKeyDown={(e) => {
                            if (e.key === 'Enter' || e.key === ' ') {
                              e.preventDefault()
                              handleCellClick(row.category, productAsin, cellData)
                            }
                          }}
                          tabIndex={0}
                          role="button"
                          aria-label={`View reviews for ${row.category} - ${productName}: ${cellData.mentions} mentions, ${cellData.satisfactionRate}% satisfaction`}
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