'use client';

import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { UseCaseFeedback, ProductType } from '@/components/analysis/data/category-feedback';
import { getSatisfactionColor, getSatisfactionLevel, SatisfactionLegend } from '@/components/analysis/lib/satisfaction-colors';
import { useReviewPanel } from '@/components/analysis/contexts/review-panel-context';

interface CategoryUseCaseBarProps {
  data: UseCaseFeedback[];
  title?: string;
  description?: string;
  productType?: ProductType;
  onProductTypeChange?: (productType: ProductType) => void;
  reviewData?: {
    reviewsByCategory?: Record<string, any[]>
  }
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg min-w-[300px]">
        <p className="font-semibold text-gray-900 mb-2">{data.useCase}</p>
        
        {/* 基本统计信息 */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <p className="text-sm text-gray-600">Total Mentions:</p>
            <p className="font-semibold">{data.totalMentions}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Satisfaction Rate:</p>
            <div className="flex items-center gap-2">
              <p className="font-semibold">{data.satisfactionRate}%</p>
              <Badge 
                variant="outline" 
                style={{ 
                  borderColor: getSatisfactionColor(data.satisfactionRate),
                  color: getSatisfactionColor(data.satisfactionRate)
                }}
              >
                {getSatisfactionLevel(data.satisfactionRate)}
              </Badge>
            </div>
          </div>
        </div>

        {/* 正负面统计 */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <p className="text-sm text-green-600">Positive Reviews: {data.positiveCount}</p>
          </div>
          <div>
            <p className="text-sm text-red-600">Negative Reviews: {data.negativeCount}</p>
          </div>
        </div>

        {/* Top满意原因 */}
        {data.topSatisfactionReasons && data.topSatisfactionReasons.length > 0 && (
          <div className="mb-3">
            <p className="text-sm font-medium text-green-700 mb-1">Top Satisfaction Reasons:</p>
            <ul className="text-xs text-green-600 space-y-1">
              {data.topSatisfactionReasons.slice(0, 3).map((reason: string, index: number) => (
                <li key={index} className="pl-2 border-l-2 border-green-200">• {reason}</li>
              ))}
            </ul>
          </div>
        )}

        {/* Top不满意原因 */}
        {data.topGapReasons && data.topGapReasons.length > 0 && (
          <div className="mb-3">
            <p className="text-sm font-medium text-red-700 mb-1">Top Gap Reasons:</p>
            <ul className="text-xs text-red-600 space-y-1">
              {data.topGapReasons.slice(0, 3).map((reason: string, index: number) => (
                <li key={index} className="pl-2 border-l-2 border-red-200">• {reason}</li>
              ))}
            </ul>
          </div>
        )}

      </div>
    );
  }
  return null;
};

export default function CategoryUseCaseBar({ 
  data, 
  title = "Use Case Satisfaction Analysis",
  description = "Bars show mention count, colors indicate satisfaction levels",
  productType = 'dimmer',
  onProductTypeChange,
  reviewData
}: CategoryUseCaseBarProps) {
  const { openPanel } = useReviewPanel()
  
  // 添加数据安全检查，防止预渲染时 data 为 undefined
  if (!data || !Array.isArray(data) || data.length === 0) {
    return (
      <Card className="w-full">
        <CardContent className="p-8 text-center">
          <p className="text-gray-500">No use case data available.</p>
        </CardContent>
      </Card>
    )
  }
  
  const chartData = data.map(item => ({
    ...item,
    // 用于X轴显示的短名称
    displayName: item.useCase.length > 15 ? 
      item.useCase.substring(0, 15) + '...' : 
      item.useCase
  }));

  const handleBarClick = (data: any, index: number) => {
    if (data && data.displayName && reviewData?.reviewsByCategory) {
      // Find the full use case name from the display name
      const displayName = data.displayName
      const useCaseItem = chartData.find(item => item.displayName === displayName)
      
      if (useCaseItem) {
        const reviews = reviewData.reviewsByCategory[useCaseItem.useCase] || []
        
        if (reviews.length > 0) {
          openPanel(
            reviews,
            `${useCaseItem.useCase} - Customer Reviews`,
            `Reviews related to "${useCaseItem.useCase}" use case`,
            { sentiment: true, brand: true, rating: true, verified: true }
          )
        }
      }
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          {title}
          <SatisfactionLegend />
        </CardTitle>
        <div className="flex items-center justify-between">
          <CardDescription>{description}</CardDescription>
          {onProductTypeChange && (
            <div className="flex gap-2">
              <Button
                variant={productType === 'dimmer' ? 'default' : 'outline'}
                size="sm"
                onClick={() => onProductTypeChange('dimmer')}
              >
                Dimmer Switches
              </Button>
              <Button
                variant={productType === 'light' ? 'default' : 'outline'}
                size="sm"
                onClick={() => onProductTypeChange('light')}
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
              data={chartData}
              margin={{
                top: 20,
                right: 30,
                left: 20,
                bottom: 80,
              }}
            >
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="displayName" 
                angle={-45}
                textAnchor="end"
                height={80}
                interval={0}
                fontSize={12}
              />
              <YAxis 
                label={{ value: 'Total Mentions', angle: -90, position: 'insideLeft' }}
                fontSize={12}
              />
              <Tooltip content={<CustomTooltip />} />
              <Bar 
                dataKey="totalMentions" 
                radius={[4, 4, 0, 0]} 
                style={{ cursor: 'pointer' }}
                onClick={handleBarClick}
              >
                {chartData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getSatisfactionColor(entry.satisfactionRate)} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        
        {/* 图表下方的统计信息 */}
        <div className="mt-4 pt-4 border-t">
          {/* 主要使用场景展示 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {data.slice(0, 4).map((item, index) => (
              <div key={index} className="text-center">
                <div className="text-lg font-bold" style={{color: getSatisfactionColor(item.satisfactionRate)}}>
                  {item.totalMentions}
                </div>
                <div className="text-sm text-gray-600 truncate" title={item.useCase}>
                  {item.useCase}
                </div>
                <div className="text-xs" style={{color: getSatisfactionColor(item.satisfactionRate)}}>
                  {item.satisfactionRate}% satisfaction
                </div>
              </div>
            ))}
          </div>
          
          {/* 汇总统计 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Use Cases</p>
              <p className="text-lg font-semibold">{data.length}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Avg Satisfaction</p>
              <p className="text-lg font-semibold">
                {data.length > 0 ? 
                  Math.round(data.reduce((sum, item) => sum + item.satisfactionRate, 0) / data.length) : 0
                }%
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Mentions</p>
              <p className="text-lg font-semibold">
                {data.reduce((sum, item) => sum + item.totalMentions, 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">High Satisfaction</p>
              <p className="text-lg font-semibold text-green-600">
                {data.filter(item => item.satisfactionRate >= 65).length}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 