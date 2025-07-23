// Sales Trend Data Transformer

import { formatMonth } from '../../shared/utils/date-formatter'
import type { SalesTrendData, ChartTrendData } from '../types/sales-trend.types'
import type { MetricType } from '../../shared/types/chart-common.types'

/**
 * 转换API数据为图表格式
 * @param trendData API返回的趋势数据
 * @param metricType 指标类型
 * @returns 转换后的图表数据
 */
export function transformSalesTrendData(
  trendData: SalesTrendData['trend_data'], 
  metricType: MetricType
): ChartTrendData[] {
  return trendData.map(item => {
    const chartItem: ChartTrendData = { 
      month: formatMonth(item.month) // "2025-01" -> "Jan 2025"
    }
    
    // 转换每个品牌的数据
    Object.keys(item).forEach(key => {
      if (key !== 'month') {
        const brandData = item[key] as { revenue: number; volume: number }
        if (brandData && typeof brandData === 'object') {
          chartItem[key] = brandData[metricType] || 0
        }
      }
    })
    
    return chartItem
  })
}

/**
 * 验证API数据格式是否正确
 * @param data API返回的数据
 * @returns 是否为有效数据
 */
export function validateSalesTrendData(data: any): data is SalesTrendData {
  if (!data || typeof data !== 'object') {
    return false
  }

  // 检查必需字段
  if (!Array.isArray(data.trend_data) || !Array.isArray(data.brands) || !data.summary) {
    return false
  }

  // 检查trend_data格式
  for (const item of data.trend_data) {
    if (!item.month || typeof item.month !== 'string') {
      return false
    }
    
    // 检查品牌数据格式
    for (const key of Object.keys(item)) {
      if (key !== 'month') {
        const brandData = item[key]
        if (!brandData || typeof brandData !== 'object' || 
            typeof brandData.revenue !== 'number' || 
            typeof brandData.volume !== 'number') {
          return false
        }
      }
    }
  }

  return true
}

/**
 * 获取数据摘要信息
 * @param data 销售趋势数据
 * @param metricType 指标类型
 * @returns 摘要信息
 */
export function getSalesTrendSummary(data: SalesTrendData, metricType: MetricType) {
  const { summary, brands } = data
  
  return {
    totalBrands: summary.total_brands,
    dateRange: `${formatMonth(summary.date_range.start)} - ${formatMonth(summary.date_range.end)}`,
    totalValue: metricType === 'revenue' ? summary.total_revenue : summary.total_volume,
    topBrands: brands.slice(0, 5), // 显示前5个品牌
    metricLabel: metricType === 'revenue' ? 'Revenue' : 'Volume',
    metricUnit: metricType === 'revenue' ? '$' : 'units'
  }
} 