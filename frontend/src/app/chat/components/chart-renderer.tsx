'use client'

import React, { useState } from 'react'
import { SalesTrendChart, SalesTrendSummary } from '../charts/sales_trend'
import { MetricSelector } from '../charts/shared/components/metric-selector'
import type { MetricType } from '../charts/shared/types/chart-common.types'
import type { SalesTrendFilters } from '../charts/sales_trend/types/sales-trend.types'

interface ChartRendererProps {
  chartType: string
  projectId: string
  filters?: SalesTrendFilters
  dateRange?: {
    start_date: string
    end_date: string
  }
  [key: string]: any
}

export function ChartRenderer({ 
  chartType, 
  projectId, 
  filters, 
  dateRange,
  ...props 
}: ChartRendererProps) {
  const [metricType, setMetricType] = useState<MetricType>('revenue')

  const handleAreaClick = (data: unknown) => {
    console.log('Chart area clicked:', data)
    // 这里可以添加更多交互逻辑，比如显示详情面板
  }

  switch (chartType) {
    case 'sales_trend':
      return (
        <div className="space-y-6">
          {/* 指标选择器 */}
          <MetricSelector 
            value={metricType} 
            onChange={setMetricType}
          />
          
          {/* 图表组件 */}
          <SalesTrendChart
            projectId={projectId}
            filters={filters}
            metricType={metricType}
            dateRange={dateRange}
            onAreaClick={handleAreaClick}
            {...props}
          />
          
          {/* 数据摘要 - 只在有数据时显示 */}
          {/* <SalesTrendSummary data={data} metricType={metricType} /> */}
        </div>
      )
    
    // 未来可以添加更多图表类型
    // case 'market_insights':
    //   return <MarketInsightsChart projectId={projectId} filters={filters} {...props} />
    
    // case 'competitor_analysis':
    //   return <CompetitorAnalysisChart projectId={projectId} filters={filters} {...props} />
    
    default:
      return (
        <div className="flex items-center justify-center h-64 bg-gray-50 rounded-lg border">
          <div className="text-center text-gray-500">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <p className="font-medium">Unknown chart type</p>
            <p className="text-sm mt-1">Chart type "{chartType}" is not supported yet.</p>
          </div>
        </div>
      )
  }
} 