'use client'

import React from 'react'
import { formatMetricValue } from '../../shared/utils/number-formatter'
import { getSalesTrendSummary } from '../utils/data-transformer'
import type { SalesTrendData } from '../types/sales-trend.types'
import type { MetricType } from '../../shared/types/chart-common.types'

interface SalesTrendSummaryProps {
  data: SalesTrendData
  metricType: MetricType
}

export function SalesTrendSummary({ data, metricType }: SalesTrendSummaryProps) {
  const summary = getSalesTrendSummary(data, metricType)

  return (
    <div className="bg-blue-50 border-l-4 border-blue-400 p-4 mb-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* 总指标值 */}
        <div className="text-center">
          <p className="text-sm text-blue-600 font-medium">Total {summary.metricLabel}</p>
          <p className="text-lg font-bold text-blue-800">
            {formatMetricValue(summary.totalValue, metricType)}
          </p>
        </div>

        {/* 品牌数量 */}
        <div className="text-center">
          <p className="text-sm text-blue-600 font-medium">Top Brands</p>
          <p className="text-lg font-bold text-blue-800">
            {summary.totalBrands}
          </p>
        </div>

        {/* 时间范围 */}
        <div className="text-center">
          <p className="text-sm text-blue-600 font-medium">Date Range</p>
          <p className="text-sm font-semibold text-blue-800">
            {summary.dateRange}
          </p>
        </div>

        {/* 前5品牌 */}
        <div className="text-center">
          <p className="text-sm text-blue-600 font-medium">Leading Brands</p>
          <p className="text-xs text-blue-700">
            {summary.topBrands.join(', ')}
          </p>
        </div>
      </div>

      <div className="mt-3 pt-3 border-t border-blue-200">
        <p className="text-xs text-blue-600">
          <strong>Sales Trend Analysis:</strong> Showing top {summary.totalBrands} brands by {summary.metricLabel.toLowerCase()} 
          for the period {summary.dateRange}. Data aggregated monthly and ranked by total {summary.metricLabel.toLowerCase()}.
        </p>
      </div>
    </div>
  )
} 