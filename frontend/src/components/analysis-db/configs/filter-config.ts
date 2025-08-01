/**
 * 通用Filter配置类型定义
 * 适用于Project Filter和Chart Filter
 */

// 时间周期选项
export const TIMEFRAME_OPTIONS = [
  { value: '1_month', label: '1个月', days: 30 },
  { value: '6_months', label: '6个月', days: 180 },
  { value: '1_year', label: '1年', days: 365 }
] as const

export type TimeframeValue = typeof TIMEFRAME_OPTIONS[number]['value']

// 扩展字段类型
export type ExtendFieldType = 'select' | 'multi_select' | 'boolean' | 'range'

// 扩展字段配置接口
export interface ExtendFieldConfig {
  field_name: string
  display_name: string
  field_type: ExtendFieldType
  filter_options: {
    options?: string[] | Record<string, string>
    default?: string | boolean | number | string[] | number[]
    placeholder?: string
    description?: string
    // 对于boolean类型
    true_label?: string
    false_label?: string
    // 对于range类型
    min?: number
    max?: number
    step?: number
  }
  is_required?: boolean
  sort_order: number
}

// 通用Filter配置接口
export interface FilterConfig {
  // 控制哪些筛选器显示
  visible_filters: {
    categories?: boolean
    brands?: boolean
    segments?: boolean
    timeframe?: boolean
    extend_fields?: boolean
  }
  
  // 默认值配置
  default_values: {
    categories?: string[]
    brands?: string[]
    segments?: string[]
    timeframe?: TimeframeValue
    extend_fields?: Record<string, any>
  }
  
  // 扩展字段配置
  extend_fields: ExtendFieldConfig[]
  
  // 配置元信息
  metadata?: {
    name?: string
    description?: string
    version?: string
    created_at?: string
    updated_at?: string
  }
}

// Chart专用配置接口（继承通用配置）
export interface ChartFilterConfig extends FilterConfig {
  chart_id: string
  chart_type: string
  project_id: string
  // Chart可以覆盖某些配置
  inherit_from_project?: boolean
}

// Project专用配置接口（继承通用配置）
export interface ProjectFilterConfig extends FilterConfig {
  project_id: string
  // Project作为全局默认配置
  applies_to_charts?: string[] // 哪些chart继承这个配置
}