export interface ExtendFieldDefinition {
  field_name: string
  display_name: string
  field_type: 'boolean' | 'select' | 'multi_select' | 'range'
  sort_order: number
  filter_options: {
    options?: Record<string, string | number>
    min?: number
    max?: number
    step?: number
    default?: string | boolean | number | string[] | number[]
  }
}

export type ExtendFieldValue = string | boolean | number | string[] | number[] | undefined

export interface ExtendFieldsFilterProps {
  value: Record<string, ExtendFieldValue>
  onChange: (extendFields: Record<string, ExtendFieldValue>) => void
  
  // 上下文信息
  projectId: string
  projectData?: {
    distributions?: {
      extend_fields?: Record<string, Array<{
        name: string
        count: number
        percentage: number
      }>>
    }
  }
  
  // 配置
  filterConfig?: {
    visible_filters?: Record<string, boolean>
    default_values?: Record<string, any>
    extend_fields?: Array<{
      field_name: string
      display_name: string
      field_type: string
      filter_options: Record<string, any>
    }>
  } | null
  
  // UI状态
  loading?: boolean
  disabled?: boolean
  className?: string
}
