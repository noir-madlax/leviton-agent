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
  time_period: ""  // 🔧 不设置前端默认值，完全依赖后端
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

/**
 * 🆕 新的过滤器默认值API响应结构
 */
export interface FilterDefaultItem {
  chartName: string
  filterName: string
  filterValues: string[] | Record<string, any>  // 默认值/当前选中值
  options?: string[] | Record<string, any>     // 🆕 所有可选项
  isVisible: boolean | null
}

export type FilterDefaultsResponse = FilterDefaultItem[]

/**
 * 🆕 单个过滤器配置
 */
export interface FilterConfig {
  values: string[] | Record<string, any>    // 默认值/当前选中值
  options: string[] | Record<string, any>   // 🆕 所有可选项
  isVisible: boolean
}

/**
 * 🆕 按图表分组的过滤器配置
 */
export interface ChartFilterConfiguration {
  chartName: string
  filters: {
    categories?: FilterConfig
    asins?: FilterConfig
    brands?: FilterConfig
    product_segments?: FilterConfig
    time_period?: FilterConfig
    extend_fields?: FilterConfig
  }
}

/**
 * 🆕 统一过滤器数据（新版本）
 */
export interface UnifiedFilterData {
  // 按图表名称分组的配置
  charts: Record<string, ChartFilterConfiguration>
}

/**
 * 🆕 过滤器缓存状态
 */
export interface UnifiedFilterCacheState {
  data: UnifiedFilterData | null
  loading: boolean
  error: string | null
  lastUpdated: number | null
} 