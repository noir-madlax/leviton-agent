"use client"

import { useState, useEffect } from "react"

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
  const [reviewData, setReviewData] = useState<{ reviewsByCategory?: Record<string, unknown[]> } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [filteredData, setFilteredData] = useState<{
    reviewInsights: typeof data.reviewInsights
    allReviewData: typeof data.allReviewData
  }>({ reviewInsights: data.reviewInsights, allReviewData: data.allReviewData })

  // Use data from the main dashboard container instead of making duplicate API calls

  // Transform dashboard data to chart format
  const transformPainPointsData = (rawData: any[]): CategoryFeedback[] => {
    console.log('🔍 [DEBUG-PAIN-POINTS] Raw data received:', rawData)
    const transformed = rawData.map(item => ({
      category: item.category, // Use frontend field name
      categoryType: (item.type === 'Physical' ? 'Physical' : 'Performance') as 'Physical' | 'Performance',
      totalReviews: item.totalReviews || item.frequency, // Use frontend field name with fallback
      satisfactionRate: item.satisfactionRate || (100 - (item.negativeRate || 0)), // Calculate from negative rate
      negativeRate: item.negativeRate || 0, // Use frontend field name
      positiveReviews: item.positiveReviews || 0, // Use frontend field name
      negativeReviews: item.negativeReviews || 0, // Use frontend field name

      topNegativeAspects: [item.category], // Use frontend field name
      topPositiveAspects: [],
      topNegativeReasons: [`${item.negativeRate || 0}% negative sentiment`], // Use frontend field name
      topPositiveReasons: [],
      categoryDefinition: item.categoryDefinition, // Use frontend field name
      impactedProducts: item.impactedProducts || 1, // Use frontend field name
      categoryId: item.categoryId // Use frontend field name
    }))
    console.log('🔍 [DEBUG-PAIN-POINTS] Transformed data:', transformed)
    console.log('🔍 [DEBUG-PAIN-POINTS] Data length:', transformed.length)
    return transformed
  }

  const transformDelightsData = (rawData: any[]): CategoryFeedback[] => {
    console.log('🔍 [DEBUG-DELIGHTS] Raw data received:', rawData)
    const transformed = rawData.map(item => ({
      category: item.category, // Use frontend field name
      categoryType: (item.type === 'Physical' ? 'Physical' : 'Performance') as 'Physical' | 'Performance',
      totalReviews: item.totalReviews || item.frequency, // Use frontend field name with fallback
      satisfactionRate: item.positiveRate || 70, // Use frontend field name with fallback
      negativeRate: 100 - (item.positiveRate || 70), // Calculate from positive rate
      positiveReviews: item.positiveReviews || 0, // Use frontend field name
      negativeReviews: item.negativeReviews || 0, // Use frontend field name

      topNegativeAspects: [],
      topPositiveAspects: [item.category], // Use frontend field name
      topNegativeReasons: [],
      topPositiveReasons: [`${item.positiveRate || 70}% positive sentiment`], // Use frontend field name
      categoryDefinition: item.categoryDefinition, // Use frontend field name
      impactedProducts: item.impactedProducts || 1, // Use frontend field name
      categoryId: item.categoryId // Use frontend field name
    }))
    console.log('🔍 [DEBUG-DELIGHTS] Transformed data:', transformed)
    console.log('🔍 [DEBUG-DELIGHTS] Data length:', transformed.length)
    return transformed
  }

  const transformUseCaseData = (rawData: any[]): UseCaseFeedback[] => {
    console.log('🔍 [DEBUG-USE-CASE] Raw data received:', rawData)
    const transformed = rawData.map(item => ({
      useCase: item.useCase, // Use frontend field name
      totalReviews: item.totalReviews || 0, // Use frontend field name
      positiveReviews: item.positiveReviews || 0, // Use frontend field name
      negativeReviews: item.negativeReviews || 0, // Use frontend field name
      satisfactionRate: item.satisfactionRate || 0, // Use frontend field name
      categoryType: 'Performance' as const,
      topSatisfactionReasons: (item.satisfactionRate || 0) > 50 ? [`${item.satisfactionRate || 0}% satisfaction`] : [],
      topGapReasons: (item.satisfactionRate || 0) <= 50 ? [`${item.satisfactionRate || 0}% satisfaction`] : [],
      relatedCategories: [item.useCase], // Use frontend field name
      categoryDefinition: item.categoryDefinition, // Use frontend field name
      productCount: item.productCount || 1, // Use frontend field name
      categoryId: item.categoryId // Use frontend field name
    }))
    console.log('🔍 [DEBUG-USE-CASE] Transformed data:', transformed)
    console.log('🔍 [DEBUG-USE-CASE] Data length:', transformed.length)
    return transformed
  }





  // 处理过滤器变化
  const handleFilterChange = async (filters: ProjectFilters) => {
    if (!projectId) return

    setIsLoading(true)
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
    } finally {
      setIsLoading(false)
    }
  }

  // Data is already loaded from the main dashboard container
  // No need to fetch duplicate data on initialization

  useEffect(() => {
    // Create the structure that charts expect using database data
    // 需要将数据结构转换为图表组件期待的格式
    const reviewDataForCharts = {
      reviewsByCategory: {} as Record<string, unknown[]>
    }
    
    // 如果有allReviewData，需要正确映射到类别名称
    if (filteredData.allReviewData) {
      // 首先直接使用allReviewData的现有映射
      reviewDataForCharts.reviewsByCategory = { ...filteredData.allReviewData }
      
      // 为痛点数据建立基于relatedDetailTexts的映射关系
      filteredData.reviewInsights.painPoints.forEach(painPoint => {
        const aspectName = painPoint.aspect
        if (!reviewDataForCharts.reviewsByCategory[aspectName]) {
          const relatedReviews: unknown[] = []
          
          // 使用新的relatedDetailTexts字段进行映射
          if (painPoint.relatedDetailTexts && Array.isArray(painPoint.relatedDetailTexts)) {
            painPoint.relatedDetailTexts.forEach(detailText => {
              const reviews = filteredData.allReviewData[detailText] || []
              relatedReviews.push(...reviews)
            })
          } else {
            // fallback: 如果没有relatedDetailTexts，使用原有逻辑
            Object.entries(filteredData.allReviewData).forEach(([, reviews]) => {
              reviews.forEach(review => {
                if (review.aspect && review.aspect.toLowerCase() === aspectName.toLowerCase()) {
                  relatedReviews.push(review)
                } else if (review.category && review.category.toLowerCase() === aspectName.toLowerCase()) {
                  relatedReviews.push(review)
                }
              })
            })
          }
          
          if (relatedReviews.length > 0) {
            reviewDataForCharts.reviewsByCategory[aspectName] = relatedReviews
          }
        }
      })
      
      // 为亮点数据建立基于relatedDetailTexts的映射关系
      filteredData.reviewInsights.customerLikes.forEach(like => {
        const featureName = like.feature
        if (!reviewDataForCharts.reviewsByCategory[featureName]) {
          const relatedReviews: unknown[] = []
          
          // 使用新的relatedDetailTexts字段进行映射
          if (like.relatedDetailTexts && Array.isArray(like.relatedDetailTexts)) {
            like.relatedDetailTexts.forEach(detailText => {
              const reviews = filteredData.allReviewData[detailText] || []
              relatedReviews.push(...reviews)
            })
          } else {
            // fallback: 如果没有relatedDetailTexts，使用原有逻辑
            Object.entries(filteredData.allReviewData).forEach(([, reviews]) => {
              reviews.forEach(review => {
                if (review.aspect && review.aspect.toLowerCase() === featureName.toLowerCase()) {
                  relatedReviews.push(review)
                } else if (review.category && review.category.toLowerCase() === featureName.toLowerCase()) {
                  relatedReviews.push(review)
                }
              })
            })
          }
          
          if (relatedReviews.length > 0) {
            reviewDataForCharts.reviewsByCategory[featureName] = relatedReviews
          }
        }
      })
      
      // 为Use Case数据建立基于relatedDetailTexts的映射关系
      filteredData.reviewInsights.allUseCases.forEach(useCaseItem => {
        const useCaseName = useCaseItem.useCase
        
        if (!reviewDataForCharts.reviewsByCategory[useCaseName]) {
          const relatedReviews: unknown[] = []
          
          // 使用新的relatedDetailTexts字段进行映射
          if (useCaseItem.relatedDetailTexts && Array.isArray(useCaseItem.relatedDetailTexts)) {
            useCaseItem.relatedDetailTexts.forEach(detailText => {
              const reviews = filteredData.allReviewData[detailText] || []
              relatedReviews.push(...reviews)
            })
          } else {
            // fallback: 如果没有relatedDetailTexts，使用原有逻辑
            Object.entries(filteredData.allReviewData).forEach(([, reviews]) => {
              reviews.forEach(review => {
                if (review.aspect && useCaseName.toLowerCase().includes(review.aspect.toLowerCase())) {
                  relatedReviews.push(review)
                } else if (review.category && useCaseName.toLowerCase().includes(review.category.toLowerCase())) {
                  relatedReviews.push(review)
                } else if (useCaseItem.productAttribute && 
                           (review.aspect?.toLowerCase().includes(useCaseItem.productAttribute.toLowerCase()) ||
                            review.category?.toLowerCase().includes(useCaseItem.productAttribute.toLowerCase()))) {
                  relatedReviews.push(review)
                }
              })
            })
          }
          
          if (relatedReviews.length > 0) {
            reviewDataForCharts.reviewsByCategory[useCaseName] = relatedReviews
          }
        }
      })
      

    }
    
    setReviewData(reviewDataForCharts)
  }, [filteredData])
  
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
              reviewData={reviewData || undefined}
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
              reviewData={reviewData || undefined}
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
              reviewData={reviewData as { reviewsByCategory?: Record<string, Array<{
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
              }>> }}
              projectId={projectId}
              filters={initialFilters}
            />
        </div>
      </section>

    </div>
  )
} 