"use client"

import { useMemo, useState } from "react"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"
import { Tooltip } from "@/components/ui/tooltip"
import { DetailedTooltip } from "@/components/ui/detailed-tooltip"
// allReviewData now passed as prop instead of imported

// 新的数据结构接口
interface MatrixViewData {
  status: string
  message?: string
  timestamp: string
  data: {
    aspect_categories: Array<{
      category_id: number
      category_name: string
      definition: string
    }>
    product_aspect_data: Array<{
      asin: string
      aspect_data: Array<{
        category_pk: number
        mentions: number
        reviews: number
        sentiment_counts: {
          positive: number
          negative: number
          neutral: number
        }
      }>
    }>
    selected_asins: string[]
    aspect_type: string
    total_categories: number
  }
}

interface CompetitorMatrixProps {
  matrixViewData: MatrixViewData | null;
  projectId: string;
  asinToProductNameMap?: Record<string, string>;
  asinToFullProductNameMap?: Record<string, string>;
}

export function CompetitorMatrix({ matrixViewData, projectId, asinToProductNameMap, asinToFullProductNameMap }: CompetitorMatrixProps) {
  const { openPanel } = useReviewPanel()
  const [cellClickLoading, setCellClickLoading] = useState(false)

  // 从新数据结构中提取产品列表
  const orderedProducts = useMemo(() => {
    if (!matrixViewData?.data?.selected_asins) return []
    return matrixViewData.data.selected_asins
  }, [matrixViewData])

  // 从新数据结构中构建矩阵数据
  const matrixData = useMemo(() => {
    if (!matrixViewData?.data) return []

    const { aspect_categories, product_aspect_data } = matrixViewData.data

    // 创建矩阵结构，每个类别作为一行
    const matrix = aspect_categories.map(category => {
      const row = {
        category: category.category_name,
        categoryId: category.category_id,
        definition: category.definition,
        cells: {} as Record<string, {
          // 数据字段
          mentions: number
          reviews: number
          satisfactionRate: number
          positiveCount: number
          negativeCount: number
          neutralCount: number
          // 坐标信息，用于后续查询评论明细
          productAsin: string
          categoryId: number
          categoryName: string
        } | null>
      }

      // 为每个产品填充单元格数据
      orderedProducts.forEach(productAsin => {
        const productData = product_aspect_data.find(p => p.asin === productAsin)
        const aspectData = productData?.aspect_data.find(a => a.category_pk === category.category_id)

        if (aspectData) {
          const { positive, negative, neutral } = aspectData.sentiment_counts
          const totalSentiments = positive + negative + neutral
          const satisfactionRate = totalSentiments > 0 ? (positive / totalSentiments) * 100 : 0

          row.cells[productAsin] = {
            // 数据字段
            mentions: aspectData.mentions,
            reviews: aspectData.reviews,
            satisfactionRate: Math.round(satisfactionRate * 10) / 10,
            positiveCount: positive,
            negativeCount: negative,
            neutralCount: neutral,
            // 坐标信息，用于后续查询评论明细
            productAsin: productAsin,
            categoryId: category.category_id,
            categoryName: category.category_name
          }
        } else {
          row.cells[productAsin] = null
        }
      })

      return row
    })

    return matrix
  }, [matrixViewData, orderedProducts])

  // 🆕 工具函数：将后端sentiment格式映射到frontend格式
  const mapSentiment = (backendSentiment: string): 'positive' | 'negative' | 'neutral' => {
    if (backendSentiment === '+') return 'positive'
    if (backendSentiment === '-') return 'negative'
    return 'neutral'
  }

  // 🆕 工具函数：基于aspects计算总体sentiment
  const calculateOverallSentiment = (aspects: Array<{ sentiment: string }>): 'positive' | 'negative' | 'neutral' => {
    if (!aspects.length) return 'neutral'
    const positiveCount = aspects.filter(a => a.sentiment === '+').length
    const negativeCount = aspects.filter(a => a.sentiment === '-').length
    
    if (positiveCount > negativeCount) return 'positive'
    if (negativeCount > positiveCount) return 'negative'
    return 'neutral'
  }

  // 如果没有数据，显示加载状态
  if (!matrixViewData) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-gray-500">Loading matrix data...</div>
      </div>
    )
  }

  const handleCellClick = async (cellData: {
    mentions: number
    reviews: number
    satisfactionRate: number
    positiveCount: number
    negativeCount: number
    neutralCount: number
    productAsin: string
    categoryId: number
    categoryName: string
  }) => {
    if (cellData.mentions === 0) return

    const productName = asinToProductNameMap?.[cellData.productAsin] || cellData.productAsin

    try {
      setCellClickLoading(true)
      console.log(`Fetching reviews for category ${cellData.categoryName} (ID: ${cellData.categoryId}) and product ${cellData.productAsin}`)

      // 导入 databaseService
      const { databaseService } = await import('@/components/analysis-db/data/database-service')

      // 调用新的评论获取 API
      const reviewsResponse = await databaseService.getCompetitorReviews(
        projectId,
        cellData.categoryId,
        cellData.productAsin,
        100, // limit
        0,   // offset
        'review_id', // sort_by
        'desc' // sort_order
      )

      // 转换数据格式以适配 ReviewPanel
      const reviewsToShow = reviewsResponse.data.reviews.map(review => ({
        id: review.review_id,
        productId: cellData.productAsin,
        text: review.review_text,
        sentiment: calculateOverallSentiment(review.aspects),
        category: cellData.categoryName,
        aspect: review.aspects.map(a => a.aspect_description).join(', '),
        rating: review.rating,
        verified: review.verified,
        date: review.review_date,
        brand: productName, // 使用产品名称作为品牌
        // 🆕 新增：完整的aspects信息
        aspects: review.aspects.map(aspect => ({
          description: aspect.aspect_description,
          sentiment: mapSentiment(aspect.sentiment),
          aspect_type: aspect.aspect_type
        }))
      }))

      console.log(`Found ${reviewsToShow.length} reviews`)

      openPanel(
        reviewsToShow,
        `${cellData.categoryName} Reviews`,
        `${productName} • ${cellData.mentions} mentions • ${cellData.satisfactionRate}% satisfaction • ${reviewsResponse.data.total_reviews} total reviews`,
        { sentiment: true, brand: true, rating: true, verified: true }
      )
    } catch (error) {
      console.error('Error fetching reviews:', error)

      // 如果出错，显示错误信息
      openPanel(
        [],
        `${cellData.categoryName} Reviews`,
        `${productName} • Error loading reviews`,
        { sentiment: true, brand: true, rating: true, verified: true }
      )
    } finally {
      setCellClickLoading(false)
    }
  }

  const getSatisfactionColor = (satisfactionRate: number, totalReviews: number, mentions: number) => {
    // If no reviews at all, show gray
    if (totalReviews === 0) return 'bg-gray-100 text-gray-400'
    
    // If reviews but no detailed mentions, show light blue
    if (mentions === 0) return 'bg-blue-50 text-blue-700'
    
    // If we have detailed reviews, use satisfaction-based colors
    if (satisfactionRate >= 75) return 'bg-green-100 text-green-800'
    else if (satisfactionRate >= 50) return 'bg-yellow-100 text-yellow-800'
    else if (satisfactionRate >= 25) return 'bg-orange-100 text-orange-800'
    else return 'bg-red-100 text-red-800'
  }



  return (
    <div className="relative">
      {cellClickLoading && (
        <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-10 rounded-lg">
        <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
          <span className="text-gray-700 font-medium">Loading review details...</span>
        </div>
      </div>
      )}
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
                    <th key={productAsin} className={`border border-gray-300 p-3 text-center font-semibold min-w-[140px] `}>
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
                        Physical/Performance
                      </span>
                    </div>
                  </td>
                  {orderedProducts.map(productAsin => {
                    const cellData = row.cells[productAsin]
                    
                    // Show N/A only if no data exists or no reviews at all
                    if (!cellData || cellData.reviews === 0) {
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
                            type: 'Physical/Performance',
                            positiveCount: cellData.positiveCount,
                            negativeCount: cellData.negativeCount,
                            totalMentions: cellData.reviews,
                            satisfactionRate: cellData.satisfactionRate,
                            additionalInfo: [
                              `Product: ${productName}`,
                              `Total reviews analyzed: ${cellData.reviews}`
                            ]
                          }}
                        >
                          <div
                            className={`matrix-cell py-2 px-3 rounded text-sm font-semibold ${getSatisfactionColor(cellData.satisfactionRate, cellData.reviews, cellData.mentions)} cursor-pointer`}
                            onClick={() => handleCellClick(cellData)}
                            onKeyDown={(e) => {
                              if (e.key === 'Enter' || e.key === ' ') {
                                e.preventDefault()
                                handleCellClick(cellData)
                              }
                            }}
                            tabIndex={0}
                            role="button"
                            aria-label={`View reviews for ${row.category} - ${productName}: ${cellData.reviews} reviews, ${cellData.satisfactionRate}% satisfaction`}
                          >
                            <div className="text-lg font-bold">
                              {cellData.reviews}
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
    </div>
  )
} 