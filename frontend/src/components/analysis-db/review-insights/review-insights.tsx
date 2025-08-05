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
        positiveCount: number
        negativeCount: number
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
    return rawData.map(item => ({
      category: item.category_name,
      categoryType: item.type === 'Physical' ? 'Physical' : 'Performance',
      totalReviews: item.total_reviews,
      satisfactionRate: item.satisfaction_rate,
      negativeRate: item.negative_rate,
      positiveCount: item.positive_reviews || 0,
      negativeCount: item.negative_reviews || 0,
      averageRating: Math.max(1, 5 - (item.negative_rate / 20)),
      topNegativeAspects: [item.category_name],
      topPositiveAspects: [],
      topNegativeReasons: [`${item.negative_rate}% negative sentiment`],
      topPositiveReasons: [],
      categoryDefinition: item.category_definition,
      impactedProducts: item.impacted_products,
      categoryId: item.category_id
    }))
  }

  const transformDelightsData = (rawData: any[]): CategoryFeedback[] => {
    return rawData.map(item => ({
      category: item.category_name,
      categoryType: item.type === 'Physical' ? 'Physical' : 'Performance',
      totalReviews: item.total_reviews,
      satisfactionRate: item.positive_rate || 70,
      negativeRate: 100 - (item.positive_rate || 70),
      positiveCount: item.positive_reviews || 0,
      negativeCount: item.negative_reviews || 0,
      averageRating: 3 + ((item.positive_rate || 70) / 50),
      topNegativeAspects: [],
      topPositiveAspects: [item.category_name],
      topNegativeReasons: [],
      topPositiveReasons: [`${item.positive_rate || 70}% positive sentiment`],
      categoryDefinition: item.category_definition,
      impactedProducts: item.impacted_products,
      categoryId: item.category_id
    }))
  }

  const transformUseCaseData = (rawData: any[]): UseCaseFeedback[] => {
    return rawData.map(item => ({
      useCase: item.use_case,
      totalReviews: item.total_reviews,
      positiveReviews: item.positive_reviews,
      negativeReviews: item.negative_reviews,
      satisfactionRate: item.satisfaction_rate,
      categoryType: 'Performance' as const,
      topSatisfactionReasons: item.satisfaction_rate > 50 ? [`${item.satisfaction_rate}% satisfaction`] : [],
      topGapReasons: item.satisfaction_rate <= 50 ? [`${item.satisfaction_rate}% satisfaction`] : [],
      relatedCategories: [item.use_case],
      categoryDefinition: item.category_definition,
      productCount: item.product_count,
      categoryId: item.category_id
    }))
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