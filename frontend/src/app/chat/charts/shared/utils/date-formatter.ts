// Date Formatting Utilities

/**
 * 格式化月份显示
 * @param monthStr 月份字符串 (YYYY-MM)
 * @returns 格式化后的月份 (Jan 2025)
 */
export function formatMonth(monthStr: string): string {
  const [year, month] = monthStr.split('-')
  const monthNames = [
    'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
    'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'
  ]
  
  const monthIndex = parseInt(month) - 1
  if (monthIndex < 0 || monthIndex >= 12) {
    return monthStr // 返回原始字符串如果格式不正确
  }
  
  return `${monthNames[monthIndex]} ${year}`
}

/**
 * 格式化日期范围显示
 * @param startDate 开始日期 (YYYY-MM-DD)
 * @param endDate 结束日期 (YYYY-MM-DD)
 * @returns 格式化后的日期范围
 */
export function formatDateRange(startDate: string, endDate: string): string {
  const start = new Date(startDate)
  const end = new Date(endDate)
  
  const options: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric'
  }
  
  return `${start.toLocaleDateString('en-US', options)} - ${end.toLocaleDateString('en-US', options)}`
}

/**
 * 获取默认日期范围（最近6个月）
 * @returns 日期范围对象
 */
export function getDefaultDateRange(): { start_date: string; end_date: string } {
  const end = new Date()
  const start = new Date()
  start.setMonth(start.getMonth() - 6)
  
  return {
    start_date: start.toISOString().split('T')[0],
    end_date: end.toISOString().split('T')[0]
  }
} 