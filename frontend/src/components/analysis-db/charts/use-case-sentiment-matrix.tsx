"use client"

import { useState, useMemo } from "react"
import { Tooltip } from "@/components/ui/tooltip"
import { useChartsT } from '@/i18n/hooks'
import { UseCaseFeedback } from "@/components/analysis-db/types/analysis"
import { useReviewPanelQuery } from "@/components/analysis-db/hooks/use-review-panel-query"

interface UseCaseSentimentMatrixProps {
  data: UseCaseFeedback[]
  projectId?: string // Required: for getting review details
  filters?: {
    categories?: string[]
    brands?: string[]
    segments?: string[]
    extend_fields?: Record<string, unknown>
    asins?: string[]
  } // Required: filter parameters
}

type SortField = 'totalReviews' | 'positiveReviews' | 'negativeReviews' | 'positiveShare'
type SortDirection = 'asc' | 'desc'

export function UseCaseSentimentMatrix({ data, projectId, filters }: UseCaseSentimentMatrixProps) {
  const chartsT = useChartsT()
  const { handleCategoryClick, isLoading } = useReviewPanelQuery()
  const [sortField, setSortField] = useState<SortField>('totalReviews')
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc')

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
    if (!data || data.length === 0) return []

    const dataWithPositiveShare = data.map(item => ({
      ...item,
      positiveShare: item.totalReviews > 0 ? (item.positiveReviews / item.totalReviews) * 100 : 0
    }))

    return [...dataWithPositiveShare].sort((a, b) => {
      let aValue: number, bValue: number

      switch (sortField) {
        case 'totalReviews':
          aValue = a.totalReviews
          bValue = b.totalReviews
          break
        case 'positiveReviews':
          aValue = a.positiveReviews
          bValue = b.positiveReviews
          break
        case 'negativeReviews':
          aValue = a.negativeReviews
          bValue = b.negativeReviews
          break
        case 'positiveShare':
          aValue = a.positiveShare
          bValue = b.positiveShare
          break
        default:
          aValue = a.totalReviews
          bValue = b.totalReviews
      }

      if (sortDirection === 'asc') {
        return aValue - bValue
      } else {
        return bValue - aValue
      }
    })
  }, [data, sortField, sortDirection])

  // 处理行点击
  const handleRowClick = async (useCase: string, categoryId?: number) => {
    if (categoryId && projectId) {
      // Use the new API to get review details
      await handleCategoryClick(
        projectId,
        categoryId,
        useCase,
        ['use'], // use cases use usability aspects
        filters
      )
    }
  }

  // 获取排序图标
  const getSortIcon = (field: SortField) => {
    if (sortField !== field) return '↕️'
    return sortDirection === 'asc' ? '↑' : '↓'
  }

  // 获取满意度颜色
  const getSatisfactionColor = (satisfactionRate: number) => {
    if (satisfactionRate >= 75) return 'bg-green-100 text-green-800'
    if (satisfactionRate >= 50) return 'bg-yellow-100 text-yellow-800'
    if (satisfactionRate >= 25) return 'bg-orange-100 text-orange-800'
    return 'bg-red-100 text-red-800'
  }

  if (!data || data.length === 0) {
    return (
      <div className="p-8 text-center">
        <p className="text-gray-500">{chartsT('noUseCaseDataAvailable')}</p>
      </div>
    )
  }

  return (
    <div className="relative">
      {isLoading && (
        <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-10 rounded-lg">
          <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
            <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
            <span className="text-gray-700 font-medium">Loading review details...</span>
          </div>
        </div>
      )}
      <div className="overflow-x-auto">
      <div className="min-w-full ">
        <table className="w-full ">
          <thead>
            <tr className="bg-gray-50 ">
              <th className="border border-gray-300 p-3 text-left font-semibold text-gray-900 min-w-[230px]">
                <Tooltip content={chartsT('useCaseTooltip')}>
                  <div>{chartsT('useCase')}</div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[150px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('totalReviews')}
              >
                <Tooltip content={chartsT('totalReviewsTooltip')}>
                  <div className="flex items-center justify-center gap-1">
                    {chartsT('totalReviews')}
                    <span className="text-xs">{getSortIcon('totalReviews')}</span>
                  </div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[135px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('positiveReviews')}
              >
                <Tooltip content={chartsT('positiveAspectsTooltip')}>
                  <div className="flex items-center justify-center gap-1">
                    {chartsT('positiveMentionedAspectsHeader')}
                    <span className="text-xs">{getSortIcon('positiveReviews')}</span>
                  </div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[135px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('negativeReviews')}
              >
                <Tooltip content={chartsT('negativeAspectsTooltip')}>
                  <div className="flex items-center justify-center gap-1">
                    {chartsT('negativeMentionedAspectsHeader')}
                    <span className="text-xs">{getSortIcon('negativeReviews')}</span>
                  </div>
                </Tooltip>
              </th>
              <th 
                className="border border-gray-300 p-3 text-center font-semibold text-gray-900 min-w-[135px] cursor-pointer hover:bg-gray-100"
                onClick={() => handleSort('positiveShare')}
              >
                <Tooltip content={chartsT('positiveShareTooltip')}>
                  <div className="flex items-center justify-center gap-1">
                  {chartsT('satisfactionRateHeader')}
                    <span className="text-xs">{getSortIcon('positiveShare')}</span>
                  </div>
                </Tooltip>
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map((row, index) => {
              const positiveShare = row.totalReviews > 0 ? (row.positiveReviews / row.totalReviews) * 100 : 0
              
              return (
                <tr key={index} className="hover:bg-gray-50">
                  <td className="border border-gray-300 p-3 bg-gray-50 font-medium text-gray-900">
                    <div className="text-sm">{row.useCase}</div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className="py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:bg-gray-100"
                      onClick={() => handleRowClick(row.useCase, row.categoryId)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase, row.categoryId)
                        }
                      }}
                    >
                      <div className="text-lg font-bold text-blue-600">
                        {row.totalReviews}
                      </div>
                    </div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className="py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:bg-gray-100"
                      onClick={() => handleRowClick(row.useCase, row.categoryId)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase, row.categoryId)
                        }
                      }}
                    >
                      <div className="text-lg font-bold text-green-600">
                        {row.positiveReviews || 0}
                      </div>
                    </div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className="py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:bg-gray-100"
                      onClick={() => handleRowClick(row.useCase, row.categoryId)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase, row.categoryId)
                        }
                      }}
                    >
                      <div className="text-lg font-bold text-red-600">
                        {row.negativeReviews || 0}
                      </div>
                    </div>
                  </td>
                  <td className="border border-gray-300 p-3 text-center">
                    <div 
                      className={`py-2 px-3 rounded text-sm font-semibold cursor-pointer hover:opacity-80 ${getSatisfactionColor(positiveShare)}`}
                      onClick={() => handleRowClick(row.useCase, row.categoryId)}
                      role="button"
                      tabIndex={0}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter' || e.key === ' ') {
                          e.preventDefault()
                          handleRowClick(row.useCase, row.categoryId)
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
    </div>
  )
} 