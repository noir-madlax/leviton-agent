export interface Product {
  id: string
  name: string
  brand: string
  price: number
  unitPrice: number
  revenue: number
  volume: number
  url: string
  category?: string
  productSegment?: string
  packCount?: number
  reviewCategory?: string
  feedbackType?: string
}

// Types for analysis components - migrated from deleted static data files

export type ProductType = 'dimmer' | 'light'

export interface CategoryFeedback {
  category: string
  categoryType: 'Physical' | 'Performance'
  totalReviews: number
  satisfactionRate: number
  negativeRate: number
  positiveReviews: number
  negativeReviews: number

  topNegativeAspects: string[]
  topPositiveAspects: string[]
  topNegativeReasons: string[]
  topPositiveReasons: string[]
  // Enhanced fields for tooltips and better UX
  categoryDefinition?: string
  impactedProducts?: number
  // New field for review detail fetching
  categoryId?: number
}

export interface UseCaseFeedback {
  useCase: string
  totalReviews: number
  positiveReviews: number
  negativeReviews: number
  satisfactionRate: number
  categoryType: 'Physical' | 'Performance'
  topSatisfactionReasons: string[]
  topGapReasons: string[]
  relatedCategories: string[]
  // Enhanced fields for better analysis
  categoryDefinition?: string
  productCount?: number
  // New field for review detail fetching
  categoryId?: number
}

export interface ProductPainPoint {
  product: string
  category: string
  categoryType: 'Physical' | 'Performance'
  totalReviews: number
  satisfactionRate: number
  positiveCount: number
  negativeCount: number
}

export interface Review {
  id: string
  productId: string
  text: string
  sentiment: 'positive' | 'negative' | 'neutral'
  category: string
  aspect: string
  rating: number
  verified: boolean
  date: string
  brand: string
  // 🆕 新增字段，向后兼容 - 用于显示每个aspect的详细信息和sentiment
  aspects?: Array<{
    description: string
    sentiment: 'positive' | 'negative' | 'neutral'
    aspect_type?: string
  }>
}

// 🆕 Cause Category interface for new filter functionality
export interface CauseCategory {
  category_id: number
  category_name: string
  total_reviews: number
  positive_reviews: number
  negative_reviews: number
  satisfaction_rate: number
  negative_rate: number
  type: 'Physical' | 'Performance' | 'Usability'
  category_definition?: string
}

// 🆕 Review Panel Filter interface
export interface ReviewPanelFilters {
  search: string
  causeAnalysisFilter: string // 'all' | 'positive' | 'negative' | specific_category_id
  aspectTypeFilter: string // 'all' | 'phy_perf' | 'use'
  ratingFilter: string // 'all' | 'high' | 'mid' | 'low'
  verifiedFilter: string // 'all' | 'verified' | 'unverified'
  brandFilter: string // 'all' | brand_name (hidden UI but preserved logic)
}

// Helper functions moved from deleted static data files
export const getSatisfactionColor = (rate: number): string => {
  if (rate >= 85) return 'rgb(34, 197, 94)' // Green
  if (rate >= 70) return 'rgb(234, 179, 8)' // Yellow
  if (rate >= 60) return 'rgb(249, 115, 22)' // Orange
  return 'rgb(239, 68, 68)' // Red
}

export const getBubbleSize = (mentions: number, maxMentions: number): number => {
  return Math.max(15, (mentions / maxMentions) * 60)
}

export interface CustomerLike {
  feature: string
  category: string
  frequency: number
  satisfactionLevel: 'High' | 'Medium' | 'Low'
}

export interface PainPoint {
  aspect: string
  category: string
  severity: number
  frequency: number
  impactedProducts: number
  type: 'Physical' | 'Performance' | 'Usability'
}

export interface UnderservedUseCase {
  useCase: string
  productAttribute: string
  gapLevel: number
  mentionCount: number
}

export const getUseCaseAnalysisData = () => {
  // This function was used in the old static data approach
  // Now components should use data passed from database-service
  return {
    targetProducts: [],
    matrixData: []
  }
} 