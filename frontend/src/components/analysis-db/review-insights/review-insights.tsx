"use client"

import { useState } from "react"

import { CategoryPainPointsBar } from "@/components/analysis-db/charts/category-pain-points-bar"
import { CategoryPositiveFeedbackBar } from "@/components/analysis-db/charts/category-positive-feedback-bar"
import { ChartWithFilters, ChartHeader } from "@/components/analysis-db/shared/chart-with-filters"
import { BarChart3 } from "lucide-react"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { databaseService } from "@/components/analysis-db/data/database-service"

import { CategoryFeedback, ProductType, UseCaseFeedback } from "@/components/analysis-db/types/analysis"
import { UseCaseSentimentMatrix } from "@/components/analysis-db/charts/use-case-sentiment-matrix"

interface ReviewInsightsProps {
  data: {
    reviewInsights: {
      painPoints: Array<{
        aspect: string
        category: string
        severity: number
        frequency: number
        impactedProducts: number
        type: 'Physical' | 'Performance' | 'Usability'
        categoryDefinition?: string
        totalReviews?: number
        positiveReviews?: number
        negativeReviews?: number
        negativeRate?: number
        relatedDetailTexts?: string[] // Added for new mapping logic
      }>
      customerLikes: Array<{
        feature: string
        category: string
        frequency: number
        satisfactionLevel: 'High' | 'Medium' | 'Low'
        categoryDefinition?: string
        totalReviews?: number
        positiveReviews?: number
        negativeReviews?: number
        positiveRate?: number
        relatedDetailTexts?: string[] // Added for new mapping logic
      }>
      allUseCases: Array<{
        useCase: string
        productAttribute: string
        satisfactionRate: number
        totalReviews?: number
        positiveReviews: number
        negativeReviews: number
        categoryDefinition?: string
        productCount?: number
        relatedDetailTexts?: string[] // Added for new mapping logic
      }>

    }
    allReviewData: Record<string, Array<{
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
    }>>
  }
  projectId?: string
  initialFilters?: ProjectFilters
}

export function ReviewInsights({ data, projectId, initialFilters }: ReviewInsightsProps) {
  // Debug logging for incoming data
  console.log('🔍 [DEBUG-REVIEW-INSIGHTS] Incoming data:', {
    hasReviewInsights: !!data.reviewInsights,
    painPointsLength: data.reviewInsights?.painPoints?.length,
    customerLikesLength: data.reviewInsights?.customerLikes?.length,
    allUseCasesLength: data.reviewInsights?.allUseCases?.length,
    samplePainPoint: data.reviewInsights?.painPoints?.[0],
    sampleCustomerLike: data.reviewInsights?.customerLikes?.[0],
    sampleUseCase: data.reviewInsights?.allUseCases?.[0]
  })
  
  const [selectedProductType, setSelectedProductType] = useState<ProductType>('dimmer')
  // Local derived review mapping is no longer used; keep UI lean
  const [filteredData, setFilteredData] = useState<{
    reviewInsights: typeof data.reviewInsights
    allReviewData: typeof data.allReviewData
  }>({ reviewInsights: data.reviewInsights, allReviewData: data.allReviewData })

  // Use data from the main dashboard container instead of making duplicate API calls

  // Transform dashboard data to chart format
  type PainPointRaw = {
    category: string
    type: 'Physical' | 'Performance' | 'Usability'
    totalReviews?: number
    frequency?: number
    satisfactionRate?: number
    negativeRate?: number
    positiveReviews?: number
    negativeReviews?: number
    categoryDefinition?: string
    impactedProducts?: number
    categoryId?: number
  }
  const transformPainPointsData = (rawData: PainPointRaw[]): CategoryFeedback[] => {
    console.log('🔍 [DEBUG-PAIN-POINTS] Raw data received:', rawData)
    const transformed = rawData.map(item => ({
      category: String(item.category),
      categoryType: (item.type === 'Physical' ? 'Physical' : 'Performance') as 'Physical' | 'Performance',
      totalReviews: Number(item.totalReviews ?? item.frequency ?? 0),
      satisfactionRate: Number(item.satisfactionRate ?? (100 - (item.negativeRate ?? 0))),
      negativeRate: Number(item.negativeRate ?? 0),
      positiveReviews: Number(item.positiveReviews ?? 0),
      negativeReviews: Number(item.negativeReviews ?? 0),

      topNegativeAspects: [String(item.category)],
      topPositiveAspects: [],
      topNegativeReasons: [],
      topPositiveReasons: [],
      categoryDefinition: item.categoryDefinition,
      impactedProducts: Number(item.impactedProducts ?? 1),
      categoryId: item.categoryId
    }))
    console.log('🔍 [DEBUG-PAIN-POINTS] Transformed data:', transformed)
    console.log('🔍 [DEBUG-PAIN-POINTS] Data length:', transformed.length)
    return transformed
  }

  type DelightRaw = {
    category: string
    type?: 'Physical' | 'Performance' | 'Usability'
    totalReviews?: number
    frequency?: number
    positiveRate?: number
    positiveReviews?: number
    negativeReviews?: number
    categoryDefinition?: string
    impactedProducts?: number
    categoryId?: number
  }
  const transformDelightsData = (rawData: DelightRaw[]): CategoryFeedback[] => {
    console.log('🔍 [DEBUG-DELIGHTS] Raw data received:', rawData)
    const transformed = rawData.map(item => ({
      category: String(item.category),
      categoryType: ((item.type ?? 'Performance') === 'Physical' ? 'Physical' : 'Performance') as 'Physical' | 'Performance',
      totalReviews: Number(item.totalReviews ?? item.frequency ?? 0),
      satisfactionRate: Number(item.positiveRate ?? 70),
      negativeRate: 100 - Number(item.positiveRate ?? 70),
      positiveReviews: Number(item.positiveReviews ?? 0),
      negativeReviews: Number(item.negativeReviews ?? 0),

      topNegativeAspects: [],
      topPositiveAspects: [String(item.category)],
      topNegativeReasons: [],
      topPositiveReasons: [],
      categoryDefinition: item.categoryDefinition,
      impactedProducts: Number(item.impactedProducts ?? 1),
      categoryId: item.categoryId
    }))
    console.log('🔍 [DEBUG-DELIGHTS] Transformed data:', transformed)
    console.log('🔍 [DEBUG-DELIGHTS] Data length:', transformed.length)
    return transformed
  }

  type UseCaseRaw = {
    useCase: string
    totalReviews?: number
    positiveReviews?: number
    negativeReviews?: number
    satisfactionRate?: number
    categoryDefinition?: string
    productCount?: number
    categoryId?: number
  }
  const transformUseCaseData = (rawData: UseCaseRaw[]): UseCaseFeedback[] => {
    console.log('🔍 [DEBUG-USE-CASE] Raw data received:', rawData)
    const transformed = rawData.map(item => ({
      useCase: String(item.useCase),
      totalReviews: Number(item.totalReviews ?? 0),
      positiveReviews: Number(item.positiveReviews ?? 0),
      negativeReviews: Number(item.negativeReviews ?? 0),
      satisfactionRate: Number(item.satisfactionRate ?? 0),
      categoryType: 'Performance' as const,
      topSatisfactionReasons: [],
      topGapReasons: [],
      relatedCategories: [String(item.useCase)],
      categoryDefinition: item.categoryDefinition,
      productCount: Number(item.productCount ?? 1),
      categoryId: item.categoryId
    }))
    console.log('🔍 [DEBUG-USE-CASE] Transformed data:', transformed)
    console.log('🔍 [DEBUG-USE-CASE] Data length:', transformed.length)
    return transformed
  }





  // 处理过滤器变化
  const handleFilterChange = async (filters: ProjectFilters) => {
    if (!projectId) return

    try {
      const [reviewInsights, allReviewData] = await Promise.all([
        databaseService.getReviewInsightsDataByProject(
          projectId,
          filters.categories,
          filters.brands,
          filters.segments,
          filters.extend_fields
        ),
        databaseService.getAllReviewDataByProject(
          projectId,
          filters.categories,
          filters.brands,
          filters.segments,
          filters.extend_fields
        )
      ])

      setFilteredData({
        reviewInsights,
        allReviewData
      })

      // Data is already loaded from the main dashboard container
      // No need to fetch duplicate data
    } catch (error) {
      console.error('Error fetching filtered data:', error)
    }
  }

  // Data is already loaded from the main dashboard container
  // No need to fetch duplicate data on initialization

  // Removed unused review mapping effect
  
  // 注释掉旧的痛点数据转换方法，现在使用新的 API 数据源
  // const transformPainPointsData = (): { topNegativeCategories: CategoryFeedback[] } => {
  //   // 旧的转换逻辑已被新的 fetchPainPointsData 方法替代
  // }

  // 注释掉旧的正面反馈数据转换方法，现在使用新的 API 数据源
  // const transformPositiveFeedbackData = (): { topPositiveCategories: CategoryFeedback[] } => {
  //   // 旧的转换逻辑已被新的 fetchDelightsData 方法替代
  // }



  // const categoryPainPoints = transformPainPointsData() // 注释掉旧的数据转换
  // const categoryPositiveFeedback = transformPositiveFeedbackData() // 注释掉旧的数据转换
  // const useCases = transformUseCaseData() // Commented out as it's not used currently

  const handleProductTypeChange = (productType: ProductType) => {
    setSelectedProductType(productType)
  }

  return (
    <div className="space-y-10">

      {/* 分类痛点分析 */}
      <section data-chart-id="customer-pain-points">
        <h2 className="text-2xl font-bold text-gray-800 pl-0 mb-6">
          📊 Customer Reviews
        </h2>
       
        
        <ChartWithFilters
          chartId="customer-pain-points"
          chartType="bar"
          projectId={projectId || ''}
          title="Top 10 Customer Pain Points"
          projectFilters={initialFilters}
          onFilterChange={handleFilterChange}
        >
           <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
           Bars are sorted by descending negative reviews left to right, calculated from the latest 40 reviews per product in selected categories.
            </div>
            <CategoryPainPointsBar
              data={transformPainPointsData(filteredData.reviewInsights?.painPoints || [])}
              productType={selectedProductType}
              onProductTypeChange={handleProductTypeChange}
              projectId={projectId}
              filters={initialFilters}
            />
        </ChartWithFilters>
      </section>

            {/* 分类正面反馈分析 */}
      <section data-chart-id="customer-delights">
        
        
        <ChartWithFilters
          chartId="customer-delights"
          chartType="bar"
          projectId={projectId || ''}
          title="Top 10 Customer Delights"
          projectFilters={initialFilters}
          onFilterChange={handleFilterChange}
        >
            <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
            Bars are sorted by descending positive reviews left to right, calculated from the ~50 most recent reviews per product in selected categories.

            </div>
            <CategoryPositiveFeedbackBar
              data={transformDelightsData(filteredData.reviewInsights?.customerLikes || [])}
              productType={selectedProductType}
              onProductTypeChange={handleProductTypeChange}
              projectId={projectId}
              filters={initialFilters}
            />
        </ChartWithFilters>
      </section>

      {/* Use Case Sentiment Analysis */}
      <section data-chart-id="use-case-sentiment">
        <ChartHeader title=" Use Case Sentiment Analysis" icon={BarChart3} />
        <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
        Calculated from the latest 40 reviews per product in selected categories.


            </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
            <UseCaseSentimentMatrix
              data={transformUseCaseData(filteredData.reviewInsights?.allUseCases || [])}
              projectId={projectId}
              filters={initialFilters}
            />
        </div>
      </section>

    </div>
  )
} 