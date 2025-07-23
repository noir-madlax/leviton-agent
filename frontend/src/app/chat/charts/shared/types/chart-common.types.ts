// Common Chart Types

export type MetricType = 'revenue' | 'volume'

export interface ChartFilters {
  categories?: string[]
  brands?: string[]
  segments?: string[]
  extend_fields?: Record<string, any>
}

export interface DateRange {
  start_date: string
  end_date: string
}

export interface ChartContainerProps {
  title: string
  loading?: boolean
  error?: string | null
  children?: React.ReactNode
}

export interface ApiResponse<T> {
  data?: T
  error?: string
  status: number
}

export interface ChartApiError {
  status_code: number
  detail: string
} 