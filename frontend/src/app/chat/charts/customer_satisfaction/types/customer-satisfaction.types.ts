// Customer Satisfaction Chart Types

export interface ProductSatisfactionData {
  asin: string
  name: string
  full_title: string
  brand: string
  total_reviews: number
  average_rating?: number
  satisfaction_score: number
  price_usd?: number
  product_url?: string
  thumbnail_url?: string
}

export interface CustomerSatisfactionFilters {
  categories?: string[]
  brands?: string[]
  segments?: string[]
  extend_fields?: Record<string, any>
}

export interface CustomerSatisfactionResponse {
  status: string
  message?: string
  timestamp: string
  data: ProductSatisfactionData[]
}

export interface CustomerSatisfactionRequest {
  project_id: string
  filters?: CustomerSatisfactionFilters
  date_range?: {
    start_date: string
    end_date: string
  }
}

export interface CustomerSatisfactionChartProps {
  projectId: string
  filters?: CustomerSatisfactionFilters
  onProductClick?: (product: ProductSatisfactionData) => void
}
