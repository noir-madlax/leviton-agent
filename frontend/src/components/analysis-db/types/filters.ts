/**
 * 统一的项目筛选器接口定义
 */
export interface ProjectFilters {
  categories: string[]
  asins: string[]
  packaging_types: string[]  // 新增: 包装类型筛选 - 'individual' | 'package'
  segments: string[]  // 新增: 产品段筛选
}

/**
 * 默认的空筛选器配置
 */
export const DEFAULT_FILTERS: ProjectFilters = {
  categories: [],
  asins: [],
  packaging_types: [],
  segments: []
}

/**
 * 包装类型选项
 */
export const PACKAGING_TYPE_OPTIONS = [
  { value: 'individual', label: 'Individual/Unknown' },
  { value: 'package', label: 'Package (Multi-pack)' }
] as const

export type PackagingType = 'individual' | 'package' 