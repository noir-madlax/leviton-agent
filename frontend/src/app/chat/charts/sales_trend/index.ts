// Sales Trend Chart Module Exports

export { SalesTrendChart } from './components/sales-trend-chart'
export { SalesTrendSummary } from './components/sales-trend-summary'
export { useSalesTrendData } from './hooks/use-sales-trend-data'
export { salesTrendApi } from './services/sales-trend-api'
export { 
  transformSalesTrendData, 
  validateSalesTrendData, 
  getSalesTrendSummary 
} from './utils/data-transformer'

export type {
  SalesTrendData,
  SalesTrendFilters,
  SalesTrendChartProps,
  ChartTrendData,
  SalesTrendRequest
} from './types/sales-trend.types' 