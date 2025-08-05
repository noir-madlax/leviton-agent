'use client';

import React from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { UseCaseFeedback, ProductType } from '@/components/analysis-db/types/analysis';
import { getSatisfactionColor, getSatisfactionLevel } from '@/components/analysis-db/lib/satisfaction-colors';
import { useReviewPanel } from '@/components/analysis-db/contexts/review-panel-context';
import { UnifiedStackedBarChart } from '@/components/analysis-db/shared/unified-stacked-bar-chart';
import { useReviewPanelQuery } from '@/components/analysis-db/hooks/use-review-panel-query';

interface CategoryUseCaseBarProps {
  data: UseCaseFeedback[];
  title?: string;
  description?: string;
  productType?: ProductType;
  onProductTypeChange?: (productType: ProductType) => void;
  projectId?: string // Required: for getting review details
  filters?: {
    categories?: string[]
    brands?: string[]
    segments?: string[]
    extend_fields?: Record<string, any>
    asins?: string[]
  } // Required: filter parameters
  totalUseMentions?: number;
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
            <p className="text-sm text-gray-600">Total Reviews:</p>
            <p className="font-semibold">{data.totalReviews}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Satisfaction Rate:</p>
            <div className="flex items-center gap-2">
              <p className="font-semibold">{Math.round(data.satisfactionRate)}%</p>
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

        {/* 统计信息 */}
        <div className="grid grid-cols-2 gap-2 mb-3">
          <div>
            <p className="text-sm text-gray-600">Total Mentions:</p>
            <p className="font-semibold">{data.positiveReviews + data.negativeReviews}</p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Unique Reviews:</p>
            <p className="font-semibold">{data.totalReviews}</p>
          </div>
        </div>

        {/* Top满意原因 */}
        {data.topSatisfactionReasons && data.topSatisfactionReasons.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-gray-500">Top Satisfaction Reasons:</p>
            {data.topSatisfactionReasons.slice(0, 3).map((reason: string, index: number) => (
              <p key={index} className="text-xs text-green-600">• {reason}</p>
            ))}
          </div>
        )}

        {/* Gap原因 */}
        {data.topGapReasons && data.topGapReasons.length > 0 && (
          <div className="mt-2">
            <p className="text-xs text-gray-500">Top Gap Reasons:</p>
            {data.topGapReasons.slice(0, 3).map((reason: string, index: number) => (
              <p key={index} className="text-xs text-red-600">• {reason}</p>
            ))}
          </div>
        )}
      </div>
    );
  }
  return null;
};

export default function CategoryUseCaseBar({ 
  data, 
  title = "Top 10 most mentioned positive use cases",
  description = "Bars are sorted by positive reviews from left to right in descending order",
  productType = 'dimmer',
  onProductTypeChange,
  projectId,
  filters,
  totalUseMentions
}: CategoryUseCaseBarProps) {
  const { openPanel } = useReviewPanel()
  const { handleCategoryClick, isLoading } = useReviewPanelQuery()
  
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
  
  // 按正面提及数排序，并取前10个
  const sortedData = [...data]
    .sort((a, b) => b.positiveReviews - a.positiveReviews)
    .slice(0, 10);
  
  const chartData = sortedData.map(item => ({
    ...item,
    // 用于X轴显示的短名称
    displayName: item.useCase.length > 15 ? 
      item.useCase.substring(0, 15) + '...' : 
      item.useCase
  }));

  const handleBarClick = (data: any, index: number) => {
    // Note: This component doesn't have category IDs, so we can't use the new API
    // The click functionality is disabled until we have proper category mapping
    console.log('Click functionality not available for use case bars without category IDs')
  }

  const handleProductTypeChange = (value: ProductType) => {
    if (onProductTypeChange) {
      onProductTypeChange(value)
    }
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
       
         
        </CardTitle>
        <CardDescription>
          {description}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <UnifiedStackedBarChart
          data={chartData}
          xAxisDataKey="displayName"
          positiveDataKey="positiveReviews"
          negativeDataKey="negativeReviews"
          onBarClick={handleBarClick}
          CustomTooltip={CustomTooltip}
        />
        
        {/* 图表下方的统计信息 */}
        <div className="mt-4 pt-4 border-t">
          {/* 主要使用场景展示 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-4">
            {sortedData.slice(0, 4).map((item, index) => (
              <div key={index} className="text-center">
                <div className="text-lg font-bold text-green-600">
                  {item.positiveReviews}
                </div>
                <div className="text-sm text-gray-600 truncate" title={item.useCase}>
                  {item.useCase}
                </div>
                <div className="text-xs text-gray-600">
                  {Math.round(item.satisfactionRate)}% satisfaction
                </div>
              </div>
            ))}
          </div>
          
          {/* 汇总统计 */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
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
              <p className="text-sm text-gray-600">Total Positive</p>
              <p className="text-lg font-semibold text-green-600">
                {data.reduce((sum, item) => sum + item.positiveReviews, 0)}
              </p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-600">Total Negative</p>
              <p className="text-lg font-semibold text-red-600">
                {data.reduce((sum, item) => sum + item.negativeReviews, 0)}
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
} 