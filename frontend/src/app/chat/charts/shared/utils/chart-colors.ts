// Chart Colors Utility

// 图表颜色配置 - 与现有系统保持一致
const CHART_COLORS = [
  '#3B82F6', // blue-500
  '#EF4444', // red-500
  '#10B981', // emerald-500
  '#F59E0B', // amber-500
  '#8B5CF6', // violet-500
  '#EC4899', // pink-500
  '#14B8A6', // teal-500
  '#F97316', // orange-500
  '#6366F1', // indigo-500
  '#84CC16', // lime-500
  '#06B6D4', // cyan-500
  '#F43F5E', // rose-500
  '#8B5A2B', // brown-500
  '#6B7280', // gray-500
  '#DC2626', // red-600
  '#059669', // emerald-600
  '#D97706', // amber-600
  '#7C3AED', // violet-600
  '#DB2777', // pink-600
  '#0D9488', // teal-600
]

/**
 * 获取图表颜色
 * @param index 颜色索引
 * @returns 十六进制颜色值
 */
export function getChartColor(index: number): string {
  return CHART_COLORS[index % CHART_COLORS.length]
}

/**
 * 获取多个图表颜色
 * @param count 需要的颜色数量
 * @returns 颜色数组
 */
export function getChartColors(count: number): string[] {
  return Array.from({ length: count }, (_, index) => getChartColor(index))
}

/**
 * 为品牌生成颜色映射
 * @param brands 品牌列表
 * @returns 品牌到颜色的映射对象
 */
export function getBrandColorMapping(brands: string[]): Record<string, string> {
  const mapping: Record<string, string> = {}
  brands.forEach((brand, index) => {
    mapping[brand] = getChartColor(index)
  })
  return mapping
} 