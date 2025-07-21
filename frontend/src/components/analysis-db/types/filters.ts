/**
 * 统一的项目筛选器接口定义
 */
export interface ProjectFilters {
  categories: string[]
  asins: string[]
  brands: string[]  // 改：packaging_types -> brands (品牌筛选)
  segments: string[]  // 新增: 产品段筛选
  extend_fields: Record<string, any>  // 新增: 扩展字段筛选
  time_period: string  // 新增: 时间周期筛选
}

/**
 * 筛选器可用选项接口定义
 */
export interface FilterOptions {
  categories: string[]
  hierarchical_categories?: Array<{
    parent_category: string
    parent_count: number
    children: Array<{
      category: string
      count: number
      percentage: number
    }>
  }>
  brands: string[]  // 改：packaging_types -> brands
  segments: string[]
  extend_fields: Record<string, string[]>
}

/**
 * 扩展字段定义接口
 */
export interface ExtendFieldDefinition {
  field_name: string
  display_name: string
  field_type: 'select' | 'multi_select' | 'range' | 'boolean'
  filter_options: ExtendFieldOptions
  sort_order: number
}

/**
 * 扩展字段选项接口
 */
export interface ExtendFieldOptions {
  // 对于 select 和 multi_select 类型
  options?: Record<string, string> | string[]
  default?: string | boolean | number
  placeholder?: string
  description?: string
  
  // 对于 boolean 类型
  true_label?: string
  false_label?: string
  
  // 对于 range 类型
  min?: number
  max?: number
  step?: number
}

/**
 * 默认的空筛选器配置
 */
export const DEFAULT_FILTERS: ProjectFilters = {
  categories: [],
  asins: [],
  brands: [],  // 改：packaging_types -> brands
  segments: [],
  extend_fields: {},
  time_period: "30 days"  // 新增: 默认30天
}

/**
 * 包装类型选项 (用于extend fields的package_type字段)
 */
export const PACKAGING_TYPE_OPTIONS = [
  { value: 'individual', label: 'Individual/Unknown' },
  { value: 'package', label: 'Package (Multi-pack)' }
] as const

/**
 * 包装类型定义 (用于extend fields的package_type字段)
 */
export type PackagingType = 'individual' | 'package'

/**
 * 扩展字段类型定义
 */
export type ExtendFieldType = 'select' | 'multi_select' | 'range' | 'boolean' 