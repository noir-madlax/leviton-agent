/**
 * 图表名称常量定义
 * 统一管理所有图表的名称，避免硬编码字符串
 */

// 图表名称常量
export const CHART_NAMES = {
  // 项目级别
  PROJECT: 'project',
  
  // 市场分析相关
  BRAND_ANALYSIS: 'brand-analysis',// 没用
  MARKET_SHARE_ANALYSIS: 'market-share-analysis',
  BEST_SELLING_BRANDS: 'best-selling-brands',
  SALES_TREND_ANALYSIS: 'sales-trend-analysis',
  SEGMENT_ANALYSIS: 'segment-analysis',
  PACKAGE_PREFERENCE: 'package-preference',

  // 洞察分析相关
  MARKET_INSIGHTS: 'market-insights',

  // 其他分析
  PRICE_ANALYSIS: 'price-distribution-by-type', // 修正：与图表data-chart-id匹配
  PRICE_VS_REVENUE: 'price-vs-revenue', // 散点图
  BRAND_PRICE_DISTRIBUTION: 'price-distribution-by-brands', // 品牌价格分布
  SEGMENT_ANALYSIS: 'segment-analysis',
  CATEGORY_ANALYSIS: 'category-analysis',
  COMPETITOR_ANALYSIS: 'competitor-analysis',

  // 预留扩展
  CUSTOM_ANALYSIS_1: 'custom-analysis-1',
  CUSTOM_ANALYSIS_2: 'custom-analysis-2',
  CUSTOM_ANALYSIS_3: 'custom-analysis-3'
} as const

// 图表名称类型
export type ChartName = typeof CHART_NAMES[keyof typeof CHART_NAMES]

// 图表分组
export const CHART_GROUPS = {
  // 项目级别
  PROJECT: [CHART_NAMES.PROJECT],
  
  // 市场分析组
  MARKET_ANALYSIS: [
    CHART_NAMES.BRAND_ANALYSIS,
    CHART_NAMES.MARKET_SHARE_ANALYSIS,
    CHART_NAMES.BEST_SELLING_BRANDS,
    CHART_NAMES.SALES_TREND_ANALYSIS,
    CHART_NAMES.COMPETITOR_ANALYSIS
  ],
  
  // 洞察分析组
  INSIGHTS: [
    CHART_NAMES.MARKET_INSIGHTS,
    CHART_NAMES.PACKAGE_PREFERENCE
  ],
  
  // 其他分析组
  OTHER_ANALYSIS: [
    CHART_NAMES.PRICE_ANALYSIS,
    CHART_NAMES.PRICE_VS_REVENUE,
    CHART_NAMES.BRAND_PRICE_DISTRIBUTION,
    CHART_NAMES.SEGMENT_ANALYSIS,
    CHART_NAMES.CATEGORY_ANALYSIS
  ]
} as const

// 图表显示名称映射
export const CHART_DISPLAY_NAMES: Record<ChartName, string> = {
  [CHART_NAMES.PROJECT]: '项目过滤器',
  [CHART_NAMES.BRAND_ANALYSIS]: '品牌分析',
  [CHART_NAMES.MARKET_SHARE_ANALYSIS]: '市场份额分析',
  [CHART_NAMES.BEST_SELLING_BRANDS]: '畅销品牌分析',
  [CHART_NAMES.SALES_TREND_ANALYSIS]: '销售趋势分析',
  [CHART_NAMES.COMPETITOR_ANALYSIS]: '竞争对手分析',
  [CHART_NAMES.MARKET_INSIGHTS]: '市场洞察',
  [CHART_NAMES.PACKAGE_PREFERENCE]: '包装偏好分析',
  [CHART_NAMES.PRICE_ANALYSIS]: '价格分析',
  [CHART_NAMES.PRICE_VS_REVENUE]: '价格收入分布',
  [CHART_NAMES.BRAND_PRICE_DISTRIBUTION]: '品牌价格分布',
  [CHART_NAMES.SEGMENT_ANALYSIS]: '细分分析',
  [CHART_NAMES.CATEGORY_ANALYSIS]: '分类分析',
  [CHART_NAMES.CUSTOM_ANALYSIS_1]: '自定义分析1',
  [CHART_NAMES.CUSTOM_ANALYSIS_2]: '自定义分析2',
  [CHART_NAMES.CUSTOM_ANALYSIS_3]: '自定义分析3'
}

// 图表描述映射
export const CHART_DESCRIPTIONS: Record<ChartName, string> = {
  [CHART_NAMES.PROJECT]: '项目级别的全局过滤器设置',
  [CHART_NAMES.BRAND_ANALYSIS]: '分析不同品牌的市场表现和竞争情况',
  [CHART_NAMES.MARKET_SHARE_ANALYSIS]: '分析各品牌在不同类别中的市场份额',
  [CHART_NAMES.BEST_SELLING_BRANDS]: '分析各类别中的畅销品牌排名和收入表现',
  [CHART_NAMES.SALES_TREND_ANALYSIS]: '分析销售趋势和时间序列数据',
  [CHART_NAMES.COMPETITOR_ANALYSIS]: '分析竞争对手的市场策略和表现',
  [CHART_NAMES.MARKET_INSIGHTS]: '深度市场洞察和趋势分析',
  [CHART_NAMES.PACKAGE_PREFERENCE]: '分析消费者对不同包装类型的偏好',
  [CHART_NAMES.PRICE_ANALYSIS]: '价格分布和定价策略分析',
  [CHART_NAMES.PRICE_VS_REVENUE]: '分析畅销产品的价格与收入关系',
  [CHART_NAMES.BRAND_PRICE_DISTRIBUTION]: '分析各品牌在不同类别中的价格分布',
  [CHART_NAMES.SEGMENT_ANALYSIS]: '市场细分和目标客户分析',
  [CHART_NAMES.CATEGORY_ANALYSIS]: '产品类别表现和趋势分析',
  [CHART_NAMES.CUSTOM_ANALYSIS_1]: '自定义分析图表1',
  [CHART_NAMES.CUSTOM_ANALYSIS_2]: '自定义分析图表2',
  [CHART_NAMES.CUSTOM_ANALYSIS_3]: '自定义分析图表3'
}

// 工具函数：检查是否为有效的图表名称
export function isValidChartName(name: string): name is ChartName {
  return Object.values(CHART_NAMES).includes(name as ChartName)
}

// 工具函数：获取图表显示名称
export function getChartDisplayName(chartName: ChartName): string {
  return CHART_DISPLAY_NAMES[chartName] || chartName
}

// 工具函数：获取图表描述
export function getChartDescription(chartName: ChartName): string {
  return CHART_DESCRIPTIONS[chartName] || ''
}

// 工具函数：获取图表所属分组
export function getChartGroup(chartName: ChartName): string | null {
  for (const [groupName, charts] of Object.entries(CHART_GROUPS)) {
    if ((charts as readonly ChartName[]).includes(chartName)) {
      return groupName
    }
  }
  return null
}

// 工具函数：获取分组内的所有图表
export function getChartsInGroup(groupName: keyof typeof CHART_GROUPS): ChartName[] {
  return [...(CHART_GROUPS[groupName] || [])]
}

// 导出所有图表名称的数组（用于遍历）
export const ALL_CHART_NAMES = Object.values(CHART_NAMES) as ChartName[]
