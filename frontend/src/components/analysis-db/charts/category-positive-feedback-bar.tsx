"use client"

import { useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CategoryFeedback, ProductType } from '@/components/analysis-db/types/analysis'
import { useReviewPanelQuery } from '@/components/analysis-db/hooks/use-review-panel-query'
import { UnifiedStackedBarChart } from '@/components/analysis-db/shared/unified-stacked-bar-chart'
import { getColorConfig } from '@/components/analysis-db/shared/chart-colors'

interface CategoryPositiveFeedbackBarProps {
  data: CategoryFeedback[]
  productType?: ProductType
  onProductTypeChange?: (productType: ProductType) => void
  projectId?: string // Required: for getting review details
  filters?: {
    categories?: string[]
    brands?: string[]
    segments?: string[]
    extend_fields?: Record<string, unknown>
    asins?: string[]
  } // Required: filter parameters
}

type TooltipEntry = { payload: CategoryFeedback; dataKey: string }
const CustomTooltip = ({ active, payload, label }: { active?: boolean; payload?: TooltipEntry[]; label?: string }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg max-w-xs">
        <p className="font-semibold text-gray-800">{label}</p>
        <p className="text-sm text-gray-600">Total Reviews: {data.totalReviews}</p>
        <p className="text-sm text-green-700">Positive Mentions: {data.positiveReviews}</p>
        <p className="text-sm text-red-700">Negative Mentions: {data.negativeReviews}</p>
        <p className="text-sm text-blue-600">Satisfaction Rate: {Math.round(data.satisfactionRate)}%</p>
        <div className="mt-2">
          <p className="text-xs text-gray-500">Top Strength Details:</p>
          {data.topPositiveAspects && data.topPositiveAspects.slice(0, 3).map((aspect: string, index: number) => (
            <p key={index} className="text-xs text-gray-600">• {aspect}</p>
          ))}
        </div>
      </div>
    )
  }
  return null
}

export function CategoryPositiveFeedbackBar({ data, productType = 'dimmer', projectId, filters }: CategoryPositiveFeedbackBarProps) {
  const { handleCategoryClick, isLoading } = useReviewPanelQuery()

  // 同步外部的productType变化
  useEffect(() => {}, [productType])

  // 数据已经按正面评价数排序，直接使用前10个
  const filteredData = data.slice(0, 10)

  // Note: product type changes are handled by parent if needed

  type ChartDatum = CategoryFeedback & { categoryId?: number; category?: string }
  const handleBarClick = async (data: ChartDatum) => {
    if (data && data.categoryId && data.category && projectId) {
      // Use the new API to get review details
      await handleCategoryClick(
        projectId,
        data.categoryId,
        data.category,
        ['phy', 'perf'], // delights use physical and performance aspects
        filters
      )
    }
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
      <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
      
        
        </CardTitle>
        <CardDescription>
          Bars are sorted by positive reviews from left to right in descending order
        </CardDescription>
      </CardHeader>
      <CardContent>
        <UnifiedStackedBarChart
          data={filteredData}
          xAxisDataKey="category"
          positiveDataKey="positiveReviews"
          negativeDataKey="negativeReviews"
          onBarClick={handleBarClick}
          CustomTooltip={CustomTooltip}
          maxLabelLength={25} // 设置最大标签长度
          showFromBottom={true} // 从下往上显示，优先显示开头字符
          bottomBarType="positive" // 正面bar在底部
          colorConfig={getColorConfig('delights')}
        />
        
      </CardContent>
    </Card>
    </div>
  )
} 