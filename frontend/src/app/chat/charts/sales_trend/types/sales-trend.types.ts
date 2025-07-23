// Sales Trend Chart Types

export interface SalesTrendData {
  trend_data: Array<{
    month: string
    [brandName: string]: { revenue: number; volume: number } | string
  }>
  brands: string[]
  summary: {
    total_brands: number
    date_range: { start: string; end: string }
    total_revenue: number
    total_volume: number
  }
}

export interface SalesTrendFilters {
  categories?: string[]
  brands?: string[]
  segments?: string[]
  extend_fields?: Record<string, any>
}

export interface SalesTrendChartProps {
  projectId: string
  filters?: SalesTrendFilters
  metricType?: 'revenue' | 'volume'
  dateRange?: {
    start_date: string
    end_date: string
  }
  onAreaClick?: (data: unknown) => void
}

export interface ChartTrendData {
  month: string
  [brandName: string]: number | string
}

export interface SalesTrendRequest {
  project_id: string
  filters?: SalesTrendFilters
  date_range?: {
    start_date: string
    end_date: string
  }
  aggregation?: 'monthly'
} 