"use client"

import { useEffect, useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { CategoryFeedback, ProductType } from '@/components/analysis-db/types/analysis'
import { useReviewPanelQuery } from '@/components/analysis-db/hooks/use-review-panel-query'
import { UnifiedStackedBarChart } from '@/components/analysis-db/shared/unified-stacked-bar-chart'
import { getColorConfig } from '@/components/analysis-db/shared/chart-colors'

interface CategoryPainPointsBarProps {
  data: CategoryFeedback[]
  productType?: ProductType
  onProductTypeChange?: (productType: ProductType) => void
  reviewData?: {
    reviewsByCategory?: Record<string, any[]>
  }
  projectId?: string // 新增：用于获取评论详情
  filters?: {
    categories?: string[]
    brands?: string[]
    segments?: string[]
    extend_fields?: Record<string, any>
    asins?: string[]
  } // 新增：过滤器参数
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg max-w-xs">
        <p className="font-semibold text-gray-800">{label}</p>
        <p className="text-sm text-gray-600">Type: {data.categoryType}</p>
        <p className="text-sm text-green-600 font-semibold">Positive Mentions: {data.positiveCount}</p>
        <p className="text-sm text-red-600 font-semibold">Negative Mentions: {data.negativeCount}</p>
        <p className="text-sm text-blue-600">Total Mentions: {data.positiveCount + data.negativeCount}</p>
        <p className="text-sm text-gray-600">Satisfaction Rate: {Math.round(data.satisfactionRate)}%</p>
        <div className="mt-2">
          <p className="text-xs text-gray-500">Top Pain Details:</p>
          {data.topNegativeAspects && data.topNegativeAspects.slice(0, 3).map((aspect: string, index: number) => (
            <p key={index} className="text-xs text-gray-600">• {aspect}</p>
          ))}
          {data.topNegativeReasons && data.topNegativeReasons.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-500">Top Pain Reasons:</p>
              {data.topNegativeReasons.slice(0, 3).map((reason: string, index: number) => (
                <p key={index} className="text-xs text-red-600">• {reason}</p>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }
  return null
}

export function CategoryPainPointsBar({ data, productType = 'dimmer', onProductTypeChange, reviewData, projectId, filters }: CategoryPainPointsBarProps) {
  const [selectedProductType, setSelectedProductType] = useState<ProductType>(productType)
  const { handleCategoryClick } = useReviewPanelQuery()

  // 同步外部的productType变化
  useEffect(() => {
    setSelectedProductType(productType)
  }, [productType])

  // 数据已经按负面评价数排序，直接使用前10个
  const filteredData = data.slice(0, 10)

  const handleProductTypeChange = (value: ProductType) => {
    setSelectedProductType(value)
    if (onProductTypeChange) {
      onProductTypeChange(value)
    }
  }

  const handleBarClick = async (data: any) => {
    if (data && data.categoryId && data.category && projectId) {
      // 使用新的 API 获取评论详情
      await handleCategoryClick(
        projectId,
        data.categoryId,
        data.category,
        'pain-points',
        filters // 传递过滤器参数
      )
    } else if (data && data.category && reviewData?.reviewsByCategory) {
      // 降级到旧的逻辑（如果没有 categoryId 或 projectId）
      const categoryName = data.category
      const reviews = reviewData.reviewsByCategory[categoryName] || []

      if (reviews.length > 0) {
        // 需要导入 useReviewPanel 作为降级方案
        console.warn('Using fallback review data - consider updating to use categoryId')
      }
    }
  }

  return (
    
    <Card className="w-full">
      
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
       
         
        </CardTitle>
        <CardDescription>
          Bars are sorted by negative mentions from left to right in descending order
        </CardDescription>
      </CardHeader>
      <CardContent>
        <UnifiedStackedBarChart
          data={filteredData}
          xAxisDataKey="category"
          positiveDataKey="positiveCount"
          negativeDataKey="negativeCount"
          onBarClick={handleBarClick}
          CustomTooltip={CustomTooltip}
          maxLabelLength={25} // 设置最大标签长度
          showFromBottom={true} // 从下往上显示，优先显示开头字符
          bottomBarType="negative" // 负面bar在底部
          colorConfig={getColorConfig('painPoints')}
        />
        
        {/* 统计摘要 */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          {filteredData.slice(0, 4).map((item, index) => (
            <div key={index} className="text-center">
              <div className="text-lg font-bold text-red-600">
                {item.negativeCount}
              </div>
              <div className="text-sm text-gray-600 truncate" title={item.category}>
                {item.category}
              </div>
              <div className="text-xs text-gray-600">
                {Math.round(item.satisfactionRate)}% satisfaction
              </div>
            </div>
          ))}
          <div className="text-center">
                          <p className="text-sm text-gray-600">Total Amazon Categories</p>
            <p className="text-lg font-semibold">{data.length}</p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Avg Negative Rate</p>
            <p className="text-lg font-semibold">
              {data.length > 0 ? 
                Math.round(data.reduce((sum, item) => sum + item.negativeRate, 0) / data.length) : 0
              }%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Total Negative</p>
            <p className="text-lg font-semibold text-red-600">
              {data.reduce((sum, item) => sum + item.negativeCount, 0)}
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Critical Issues</p>
            <p className="text-lg font-semibold text-red-600">
              {data.filter(item => item.negativeCount >= 30).length}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 