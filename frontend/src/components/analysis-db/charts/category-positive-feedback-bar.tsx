"use client"

import { useEffect, useState } from 'react'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell, Legend } from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { CategoryFeedback, ProductType } from '@/components/analysis-db/types/analysis'
import { getSatisfactionColor, SatisfactionLegend } from '@/components/analysis-db/lib/satisfaction-colors'
import { useReviewPanel } from '@/components/analysis-db/contexts/review-panel-context'

interface CategoryPositiveFeedbackBarProps {
  data: CategoryFeedback[]
  productType?: ProductType
  onProductTypeChange?: (productType: ProductType) => void
  reviewData?: {
    reviewsByCategory?: Record<string, any[]>
  }
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
          <p className="text-xs text-gray-500">Top Strength Details:</p>
          {data.topPositiveAspects && data.topPositiveAspects.slice(0, 3).map((aspect: string, index: number) => (
            <p key={index} className="text-xs text-gray-600">• {aspect}</p>
          ))}
          {data.topPositiveReasons && data.topPositiveReasons.length > 0 && (
            <div className="mt-2">
              <p className="text-xs text-gray-500">Top Strength Reasons:</p>
              {data.topPositiveReasons.slice(0, 3).map((reason: string, index: number) => (
                <p key={index} className="text-xs text-green-600">• {reason}</p>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }
  return null
}

export function CategoryPositiveFeedbackBar({ data, productType = 'dimmer', onProductTypeChange, reviewData }: CategoryPositiveFeedbackBarProps) {
  const [selectedProductType, setSelectedProductType] = useState<ProductType>(productType)
  const { openPanel } = useReviewPanel()

  // 同步外部的productType变化
  useEffect(() => {
    setSelectedProductType(productType)
  }, [productType])

  // 数据已经按正面评价数排序，直接使用前10个
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
          `Positive reviews highlighting "${categoryName}" strengths`,
          { sentiment: true, brand: true, rating: true, verified: true }
        )
      }
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
         
        
        </CardTitle>
        <CardDescription>
          Bars are sorted by positive mentions from left to right in descending order
        </CardDescription>
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
                  value: 'Number of mentions', 
                  angle: -90, 
                  position: 'insideLeft'
                }}
                fontSize={12}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Bar 
                dataKey="positiveCount" 
                stackId="mentions"
                fill="#22c55e"
                name="Positive Mentions"
                radius={[0, 0, 0, 0]}
                style={{ cursor: 'pointer' }}
                onClick={handleBarClick}
              />
              <Bar 
                dataKey="negativeCount" 
                stackId="mentions"
                fill="#ef4444"
                name="Negative Mentions"
                radius={[4, 4, 0, 0]}
                style={{ cursor: 'pointer' }}
                onClick={handleBarClick}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* 统计摘要 */}
        <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          {filteredData.slice(0, 4).map((item, index) => (
            <div key={index} className="text-center">
              <div className="text-lg font-bold text-green-600">
                {item.positiveCount}
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
            <p className="text-sm text-gray-600">Avg Satisfaction</p>
            <p className="text-lg font-semibold text-green-600">
              {data.length > 0 ? 
                Math.round(data.reduce((sum, item) => sum + item.satisfactionRate, 0) / data.length) : 0
              }%
            </p>
          </div>
          <div className="text-center">
            <p className="text-sm text-gray-600">Total Positive</p>
            <p className="text-lg font-semibold text-green-600">
              {data.reduce((sum, item) => sum + item.positiveCount, 0)}
            </p>
          </div>
          <div className="text-center">
                          <p className="text-sm text-gray-600">Excellent Amazon Categories</p>
            <p className="text-lg font-semibold text-green-600">
              {data.filter(item => item.positiveCount >= 100).length}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
} 