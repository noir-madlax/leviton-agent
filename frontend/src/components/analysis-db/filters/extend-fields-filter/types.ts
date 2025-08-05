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
    description?: string
    placeholder?: string
  }
}

export type ExtendFieldValue = string | boolean | number | string[] | number[] | undefined

export interface ExtendFieldsFilterProps {
  onChange: (extendFields: Record<string, ExtendFieldValue>) => void

  // 只需要 projectId 即可获取所有必要数据
  projectId: string

  // 🆕 图表名称，用于获取对应的配置
  chartName: string

  // UI状态
  loading?: boolean
  disabled?: boolean
  className?: string
}
