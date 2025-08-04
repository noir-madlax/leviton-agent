import { ProjectFilters } from '../../types/filters'

export interface BaseFilterProps {
  disabled?: boolean
  loading?: boolean
  className?: string
}

export interface FilterOptionWithCount {
  name: string
  count: number
  percentage: number
}

export interface CategoryFilterProps extends BaseFilterProps {
  value: string[]
  onChange: (categories: string[]) => void
  chartName: string  // 🆕 只需要图表名称，组件内部从context获取数据
  // 🗑️ 移除了 availableOptions 和 projectData，简化参数传递
}