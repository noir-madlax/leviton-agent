"use client"

import { useState, useMemo } from "react"
import { Tooltip } from "@/components/ui/tooltip"
import { UseCaseFeedback, StandardizedInsightData } from "@/components/analysis-db/types/analysis"
import { useReviewPanel } from "@/components/analysis-db/contexts/review-panel-context"

interface UseCaseSentimentMatrixProps {
  data: UseCaseFeedback[]
  reviewData?: {
    reviewsByCategory?: Record<string, Array<{
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
  }
  // New prop for standardized data
  standardizedData?: StandardizedInsightData
  useStandardizedData?: boolean
}

type SortField = 'totalMentions' | 'positiveCount' | 'negativeCount' | 'positiveShare'
type SortDirection = 'asc' | 'desc'

// Transform standardized data to UseCaseFeedback format (only use 'use' aspect types)
const transformStandardizedDataForUseCases = (standardizedData: StandardizedInsightData): UseCaseFeedback[] => {
  return Object.entries(standardizedData)
    .filter(([categoryKey]) => categoryKey.includes('#use#')) // Only include 'use' aspect types
    .map(([categoryKey, categoryData]) => {
      const parts = categoryKey.split('#')
      const categoryName = parts[0] || 'Unknown'
      
      const positiveCount = categoryData["+"]?.count || 0
      const negativeCount = categoryData["-"]?.count || 0
      const totalMentions = categoryData.num_mentions || 0
      const positiveRatio = categoryData.positive_ratio || 0
      
      return {
        useCase: categoryName,
        totalMentions: totalMentions,
        positiveCount: positiveCount,
        negativeCount: negativeCount,
        satisfactionRate: positiveRatio * 100,
        categoryType: 'Performance' as const,
        topSatisfactionReasons: [`${Math.round(positiveRatio * 100)}% positive sentiment`],
        topGapReasons: [`${Math.round((1 - positiveRatio) * 100)}% negative sentiment`],
        relatedCategories: [categoryName],
        categoryDefinition: 'Use case scenario',
        productCount: categoryData.num_reviews || 0
      }
    })
}

export function UseCaseSentimentMatrix({ 
  data, 
  reviewData,
  standardizedData,
  useStandardizedData = false
}: UseCaseSentimentMatrixProps) {
  const { openPanel } = useReviewPanel()
  const [sortField, setSortField] = useState<SortField>('totalMentions')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

  // Use standardized data if available and enabled, otherwise use traditional data
  const processedData = useStandardizedData && standardizedData 
    ? transformStandardizedDataForUseCases(standardizedData) 
    : data

  // 处理排序
  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDirection('desc')
    }
  }

  // 获取排序后的数据
  const sortedData = useMemo(() => {
    if (!processedData || processedData.length === 0) return []

    const dataWithPositiveShare = processedData.map(item => ({
      ...item,
      positiveShare: item.totalMentions > 0 ? (item.positiveCount / item.totalMentions) * 100 : 0
    }))

    return [...dataWithPositiveShare].sort((a, b) => {
      let aValue: number, bValue: number

      switch (sortField) {
        case 'totalMentions':
          aValue = a.totalMentions
          bValue = b.totalMentions
          break
        case 'positiveCount':
          aValue = a.positiveCount
          bValue = b.positiveCount
          break
        case 'negativeCount':
          aValue = a.negativeCount
          bValue = b.negativeCount
          break
        case 'positiveShare':
          aValue = a.positiveShare
          bValue = b.positiveShare
          break
        default:
          aValue = a.totalMentions
          bValue = b.totalMentions
      }

      if (sortDirection === 'asc') {
        return aValue - bValue
      } else {
        return bValue - aValue
      }
    })
  }, [processedData, sortField, sortDirection])

  // 处理行点击
  const handleRowClick = (useCase: string) => {
    if (reviewData?.reviewsByCategory) {
      const reviews = reviewData.reviewsByCategory[useCase] || []
      if (reviews.length > 0) {
        openPanel(
          reviews,
          `${useCase} - Customer Reviews`,
          `Reviews related to "${useCase}" use case`,
          { sentiment: true, brand: true, rating: true, verified: true }
        )
      }
    }
  }

  // 获取排序图标
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return '↕️'
    return sortDirection === 'asc' ? '↑' : '↓'
  }

  // 获取满意度颜色
  const getSatisfactionColor = (satisfactionRate: number) => {
    if (satisfactionRate >= 85) return 'bg-green-100 text-green-800'
    if (satisfactionRate >= 70) return 'bg-yellow-100 text-yellow-800'
    if (satisfactionRate >= 60) return 'bg-orange-100 text-orange-800'
    return 'bg-red-100 text-red-800'
  }

  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">No use case data available.</p>
      </div>
    )
  }

  return (
    <div className="overflow-x-auto">
      <div className="min-w-full ">
        <table className="w-full ">
          <thead>
            <tr className="bg-gray-50 ">
              <th className="border border-gray-300 p-3 text-left font-semibold text-gray-900 min-w-[230px]">
                <Tooltip content="The specific use case or scenario mentioned in customer reviews">
                  <div>Use case</div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[150px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('totalMentions')}
              >
                <Tooltip content="Total number of reviews that mention this use case">
                  <div className="flex items-center justify-center gap-1">
                    Total Mentions
                    <span className="text-xs">{getSortIcon('totalMentions')}</span>
                  </div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[150px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('positiveCount')}
              >
                <Tooltip content="Number of reviews that mention this use case with positive sentiment">
                  <div className="flex items-center justify-center gap-1">
                    Positive Mentions
                    <span className="text-xs">{getSortIcon('positiveCount')}</span>
                  </div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[150px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('negativeCount')}
              >
                <Tooltip content="Number of reviews that mention this use case with negative sentiment">
                  <div className="flex items-center justify-center gap-1">
                    Negative Mentions
                    <span className="text-xs">{getSortIcon('negativeCount')}</span>
                  </div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[150px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('positiveShare')}
              >
                <Tooltip content="Positive Mentions / Total Mentions">
                  <div className="flex items-center justify-center gap-1">
                    Positive Share (%)
                    <span className="text-xs">{getSortIcon('positiveShare')}</span>
                  </div>
                </Tooltip>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row, index) => {
              const positiveShare = row.totalMentions > 0 ? (row.positiveCount / row.totalMentions) * 100 : 0
              
              return (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="border border-gray-300 p-3 bg-gray-50 font-medium text-gray-900">
                    <div className="text-sm">{row.useCase}</div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className="py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:bg-gray-100"
                      onClick={() => handleRowClick(row.useCase)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase)
                        }
                      }}
                    >
                      <div className="text-lg font-bold text-blue-600">
                        {row.totalMentions}
                      </div>
                    </div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className="py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:bg-gray-100"
                      onClick={() => handleRowClick(row.useCase)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase)
                        }
                      }}
                    >
                      <div className="text-lg font-bold text-green-600">
                        {row.positiveCount}
                      </div>
                    </div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className="py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:bg-gray-100"
                      onClick={() => handleRowClick(row.useCase)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase)
                        }
                      }}
                    >
                      <div className="text-lg font-bold text-red-600">
                        {row.negativeCount}
                      </div>
                    </div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className={`py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:opacity-80 ${getSatisfactionColor(positiveShare)}`}
                      onClick={() => handleRowClick(row.useCase)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase)
                        }
                      }}
                    >
                      <div className="text-lg font-bold">
                        {positiveShare.toFixed(1)}%
                      </div>
                    </div>
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>
    </div>
  )
} 