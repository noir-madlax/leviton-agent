// Number Formatting Utilities

/**
 * 格式化收入数值显示
 * @param value 数值
 * @returns 格式化后的字符串
 */
export function formatRevenue(value: number): string {
  if (value >= 1000000) {
    return `$${(value / 1000000).toFixed(1)}M`
  } else if (value >= 1000) {
    return `$${(value / 1000).toFixed(0)}K`
  }
  return `$${value.toLocaleString()}`
}

/**
 * 格式化销量数值显示
 * @param value 数值
 * @returns 格式化后的字符串
 */
export function formatVolume(value: number): string {
  if (value >= 1000000) {
    return `${(value / 1000000).toFixed(1)}M`
  } else if (value >= 1000) {
    return `${(value / 1000).toFixed(0)}K`
  }
  return value.toLocaleString()
}

/**
 * 格式化百分比显示
 * @param value 数值 (0-1)
 * @param decimals 小数位数
 * @returns 格式化后的百分比字符串
 */
export function formatPercentage(value: number, decimals: number = 1): string {
  return `${(value * 100).toFixed(decimals)}%`
}

/**
 * 根据指标类型格式化数值
 * @param value 数值
 * @param metricType 指标类型
 * @returns 格式化后的字符串
 */
export function formatMetricValue(value: number, metricType: 'revenue' | 'volume'): string {
  return metricType === 'revenue' ? formatRevenue(value) : formatVolume(value)
}

/**
 * 格式化大数值为紧凑显示
 * @param value 数值
 * @returns 格式化后的字符串
 */
export function formatCompactNumber(value: number): string {
  const formatter = new Intl.NumberFormat('en-US', {
    notation: 'compact',
    maximumFractionDigits: 1
  })
  return formatter.format(value)
} 