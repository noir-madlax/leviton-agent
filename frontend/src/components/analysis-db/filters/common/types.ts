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
  availableOptions: {
    hierarchical_categories?: Array<{
      parent_category: string
      parent_count: number
      children: Array<{
        category: string
        count: number
        percentage: number
      }>
    }>
    categories: string[]
  }
  projectData?: {
    distributions?: {
      categories?: FilterOptionWithCount[]
    }
  }
}