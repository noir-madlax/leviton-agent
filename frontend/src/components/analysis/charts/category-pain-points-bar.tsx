"use client"

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CategoryFeedback, ProductType } from '@/components/analysis/data/category-feedback'
import { getSatisfactionColor, SatisfactionLegend } from '@/components/analysis/lib/satisfaction-colors'
import { useReviewPanel } from '@/components/analysis/contexts/review-panel-context'

interface CategoryPainPointsBarProps {
  data: CategoryFeedback[]
  productType?: ProductType
  onProductTypeChange?: (productType: ProductType) => void
  reviewData?: {
    reviewsByCategory?: Record<string, any[]>
  }
}

  const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg max-w-xs">
        <p className="font-semibold text-gray-800">{data.category}</p>
        <p className="text-sm text-gray-600">Type: {data.categoryType}</p>
        <p className="text-sm text-red-600 font-semibold">Negative Reviews: {data.negativeCount}</p>
        <p className="text-sm text-blue-600">Total Reviews: {data.totalReviews}</p>
        <p className="text-sm text-orange-600">Negative Rate: {data.negativeRate}%</p>
        <p className="text-sm text-green-600">Satisfaction Rate: {data.satisfactionRate}%</p>
        <div className="mt-2">
          <p className="text-xs text-gray-500">Top Issue Details:</p>
          {data.topNegativeAspects.slice(0, 3).map((aspect: string, index: number) => (
            <p key={index} className="text-xs text-gray-600">• {aspect}</p>
          ))}
          {data.topNegativeReasons && data.topNegativeReasons.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-500">Top Issue Reasons:</p>
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

export function CategoryPainPointsBar({ data, productType = 'dimmer', onProductTypeChange, reviewData }: CategoryPainPointsBarProps) {
  const [selectedProductType, setSelectedProductType] = useState<ProductType>(productType)
  const { openPanel } = useReviewPanel()

  // 同步外部的productType变化
  useEffect(() => {
    setSelectedProductType(productType)
  }, [productType])

  // Use satisfaction rate for consistent coloring across all charts
  const getBarColor = (item: CategoryFeedback) => {
    return getSatisfactionColor(item.satisfactionRate)
  }

  // 数据已经按负面评价数排序，直接使用前10个
  const filteredData = data.slice(0, 10)

  const handleProductTypeChange = (value: ProductType) => {
    setSelectedProductType(value)
    if (onProductTypeChange) {
      onProductTypeChange(value)
    }
  }

    const handleBarClick = (data: any) => {
    if (data && data.category && reviewData?.reviewsByCategory) {
      const categoryName = data.category
      const reviews = reviewData.reviewsByCategory[categoryName] || []
      
      if (reviews.length > 0) {
        openPanel(
          reviews,
          `${categoryName} - Customer Reviews`,
          `Reviews mentioning "${categoryName}" issues and experiences`,
          { sentiment: true, brand: true, rating: true, verified: true }
        )
      }
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          Top 10 Most Critical Categories by Negative Reviews Count 🖱️
          <SatisfactionLegend />
        </CardTitle>
        <div className="flex items-center justify-between">
          <CardDescription>Categories ranked by absolute negative review count</CardDescription>
          {onProductTypeChange && (
            <div className="flex gap-2">
              <Button
                variant={selectedProductType === 'dimmer' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleProductTypeChange('dimmer')}
              >
                Dimmer Switches
              </Button>
              <Button
                variant={selectedProductType === 'light' ? 'default' : 'outline'}
                size="sm"
                onClick={() => handleProductTypeChange('light')}
              >
                Light Switches
              </Button>
            </div>
          )}
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-[450px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={filteredData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 80,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="category"
                angle={-45}
                textAnchor="end"
                height={80}
                interval={0}
                fontSize={12}
              />
              <YAxis
                label={{ 
                  value: 'Negative Reviews Count', 
                  angle: -90, 
                  position: 'insideLeft'
                }}
                fontSize={12}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="negativeCount" 
                radius={[4, 4, 0, 0]} 
                style={{ cursor: 'pointer' }}
                onClick={handleBarClick}
              >
                {filteredData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getBarColor(entry)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* 统计摘要 */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          {filteredData.slice(0, 4).map((item, index) => (
            <div key={index} className="text-center">
              <div className="text-lg font-bold" style={{color: getBarColor(item)}}>
                {item.negativeCount}
              </div>
              <div className="text-sm text-gray-600 truncate" title={item.category}>
                {item.category}
              </div>
              <div className="text-xs" style={{color: getBarColor(item)}}>
                {item.satisfactionRate}% satisfaction
              </div>
            </div>
          ))}
          <div className="text-center">
            <p className="text-sm text-gray-600">Total Categories</p>
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