"use client"

import { useMemo } from "react"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"
import { allReviewData } from "@/components/analysis-db/data/review-data"

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
}

export function CompetitorMatrix({ data, targetProducts }: CompetitorMatrixProps) {
  const { openPanel } = useReviewPanel()
  
  // Map product names to their ASINs for precise filtering
  const productToAsin: Record<string, string> = {
    'Leviton D26HD': 'B08RRM8VH5',
    'Leviton D215S': 'B0BVKZLT3B', 
    'Lutron Caseta Diva': 'B0BSHKS26L',
    'TP Link Switch': 'B01EZV35QU',
    'Leviton DSL06': 'B00NG0ELL0',
    'Lutron Diva': 'B085D8M2MR'
  }
  
  const handleCellClick = (category: string, product: string, cellData: MatrixData | null) => {
    if (!cellData || cellData.mentions === 0) return
    
    // Add null check for allReviewData and the specific category
    if (!allReviewData || !allReviewData[category]) {
      console.warn(`No review data found for category: ${category}`)
      return
    }
    
    const categoryReviews = allReviewData[category] || []
    if (categoryReviews.length === 0) return
    
    // Filter reviews by specific product using ASIN
    const productAsin = productToAsin[product]
    const productReviews = productAsin 
      ? categoryReviews.filter(review => review.productId === productAsin)
      : []
    
    const reviewsToShow = productReviews.length > 0 ? productReviews : categoryReviews
    
    openPanel(
      reviewsToShow, 
      `${category} Reviews`, 
      `${product} • ${cellData.mentions} reviews • ${cellData.satisfactionRate}% satisfaction`,
      { sentiment: true, brand: true, rating: true, verified: true }
    )
  }
  
  const orderedProducts = useMemo(() => {
    // Group Leviton products first, then others
    const levitonProducts = targetProducts.filter(product => product.startsWith('Leviton'))
    const otherProducts = targetProducts.filter(product => !product.startsWith('Leviton'))
    return [...levitonProducts, ...otherProducts]
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

  const getHeaderColor = (product: string) => {
    if (product.startsWith('Leviton')) {
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
                Category Dimensions
              </th>
              {orderedProducts.map(product => (
                <th key={product} className={`border border-gray-300 p-3 text-center font-semibold min-w-[140px] ${getHeaderColor(product)}`}>
                  <div className="text-sm">{product}</div>
                </th>
              ))}
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
                {orderedProducts.map(product => {
                  const cellData = row.cells[product]
                  
                  // Show N/A only if no data exists or no mentions at all
                  if (!cellData || cellData.mentions === 0) {
                    return (
                      <td key={product} className="border border-gray-300 p-3 text-center">
                        <div className="bg-gray-100 text-gray-400 py-2 px-3 rounded text-sm">
                          N/A
                        </div>
                      </td>
                    )
                  }
                  
                  return (
                    <td key={product} className="border border-gray-300 p-3 text-center">
                      <div 
                        className={`matrix-cell py-2 px-3 rounded text-sm font-semibold ${getSatisfactionColor(cellData.satisfactionRate, cellData.totalReviews, cellData.mentions)}`}
                        onClick={() => handleCellClick(row.category, product, cellData)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault()
                            handleCellClick(row.category, product, cellData)
                          }
                        }}
                        tabIndex={0}
                        role="button"
                        aria-label={`View reviews for ${row.category} - ${product}: ${cellData.mentions} mentions, ${cellData.satisfactionRate}% satisfaction`}
                        title={`Click to view reviews for ${row.category} - ${product}`}
                      >
                        <div className="text-lg font-bold">
                          {cellData.mentions}
                        </div>
                        <div className="text-xs mt-1">
                          {cellData.totalReviews > 0 ? `${cellData.satisfactionRate}%` : '—'}
                        </div>
                      </div>
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