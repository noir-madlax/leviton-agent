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
      underservedUseCases: Array<{
        useCase: string
        productAttribute: string
        gapLevel: number
        totalReviews?: number
        positiveCount?: number
        negativeCount?: number
        categoryDefinition?: string
        productCount?: number
        relatedDetailTexts?: string[] // Added for new mapping logic
      }>
      totalUseReviews?: number
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

  // 新增：存储第一个图表的数据
  const [painPointsData, setPainPointsData] = useState<CategoryFeedback[]>([])
  const [painPointsLoading, setPainPointsLoading] = useState(false)

  // 新增：存储第二个图表的数据
  const [delightsData, setDelightsData] = useState<CategoryFeedback[]>([])
  const [delightsLoading, setDelightsLoading] = useState(false)

  // 新增：存储第三个图表的数据
  const [useCaseData, setUseCaseData] = useState<UseCaseFeedback[]>([])
  const [useCaseLoading, setUseCaseLoading] = useState(false)

  // 新增：获取痛点数据的方法
  const fetchPainPointsData = async (filters?: ProjectFilters) => {
    if (!projectId) return

    setPainPointsLoading(true)
    try {
      const result = await databaseService.getTopCategoriesData(
        projectId,
        'phy_perf', // 使用 phy_perf 类型获取痛点数据
        {
          sortBy: 'negative_mentions',
          sortDirection: 'desc',
          maxCategories: 10,
          minMentions: 5,
          minPositiveMentions: 2
        },
        filters // 传递过滤器参数
      )

      // 转换数据格式为 CategoryFeedback，添加 category_id 用于点击时获取评论详情
      const transformedData: CategoryFeedback[] = result.data.categories.map(item => ({
        category: item.category_name,
        categoryType: item.aspect_type === 'phy_perf' ? 'Physical' : 'Performance',
        mentions: item.total_mentions,
        satisfactionRate: item.positive_ratio * 100,
        negativeRate: 100 - (item.positive_ratio * 100),
        positiveCount: item.positive_reviews || item.positive_mentions,  // Use unique positive reviews, fallback to mentions
        negativeCount: item.negative_reviews || item.negative_mentions,  // Use unique negative reviews, fallback to mentions
        totalReviews: item.total_reviews,        // Use total unique reviews
        averageRating: Math.max(1, 5 - ((100 - (item.positive_ratio * 100)) / 20)), // 基于正面率计算平均评分
        topNegativeAspects: [item.category_name],
        topPositiveAspects: [],
        topNegativeReasons: [
          `${Math.round(100 - (item.positive_ratio * 100))}% negative sentiment`,
          ...(item.definition ? [`Context: ${item.definition}`] : [])
        ],
        topPositiveReasons: [],
        categoryDefinition: item.definition,
        impactedProducts: item.total_reviews, // 使用 total_reviews 作为影响产品数
        categoryId: item.category_id // 新增：存储 category_id 用于点击时获取评论详情
      }))

      setPainPointsData(transformedData)
    } catch (error) {
      console.error('Error fetching pain points data:', error)
    } finally {
      setPainPointsLoading(false)
    }
  }

  // 新增：获取亮点数据的方法
  const fetchDelightsData = async (filters?: ProjectFilters) => {
    if (!projectId) return

    setDelightsLoading(true)
    try {
      const result = await databaseService.getTopCategoriesData(
        projectId,
        'phy_perf', // 使用 phy_perf 类型获取亮点数据
        {
          sortBy: 'positive_mentions', // 按照你的要求，第二个图表也使用 negative_mentions 排序
          sortDirection: 'desc',
          maxCategories: 10,
          minMentions: 5,
          minPositiveMentions: 2
        },
        filters // 传递过滤器参数
      )

      // 转换数据格式为 CategoryFeedback，但重点关注正面数据，添加 category_id
      const transformedData: CategoryFeedback[] = result.data.categories.map(item => ({
        category: item.category_name,
        categoryType: item.aspect_type === 'phy_perf' ? 'Physical' : 'Performance',
        mentions: item.total_mentions,
        satisfactionRate: item.positive_ratio * 100,
        negativeRate: 100 - (item.positive_ratio * 100),
        positiveCount: item.positive_mentions,
        negativeCount: item.negative_mentions,
        totalReviews: item.total_reviews,
        averageRating: 3 + ((item.positive_ratio * 100) / 50), // 基于正面率计算评分
        topNegativeAspects: [],
        topPositiveAspects: [item.category_name],
        topNegativeReasons: [],
        topPositiveReasons: [
          `${Math.round(item.positive_ratio * 100)}% positive sentiment`,
          ...(item.definition ? [`Context: ${item.definition}`] : [])
        ],
        categoryDefinition: item.definition,
        impactedProducts: item.total_reviews, // 使用 total_reviews 作为影响产品数
        categoryId: item.category_id // 新增：存储 category_id 用于点击时获取评论详情
      }))

      setDelightsData(transformedData)
    } catch (error) {
      console.error('Error fetching delights data:', error)
    } finally {
      setDelightsLoading(false)
    }
  }

  // 新增：获取使用场景数据的方法
  const fetchUseCaseData = async (filters?: ProjectFilters) => {
    if (!projectId) return

    setUseCaseLoading(true)
    try {
      const result = await databaseService.getTopCategoriesData(
        projectId,
        'use', // 使用 use 类型获取使用场景数据
        {
          sortBy: 'positive_mentions', // 按正面提及排序
          sortDirection: 'desc',
          maxCategories: 15, // 使用场景可以显示更多
          minMentions: 3,
          minPositiveMentions: 1
        },
        filters // 传递过滤器参数
      )

      // 转换数据格式为 UseCaseFeedback，添加 category_id
      const transformedData: UseCaseFeedback[] = result.data.categories.map(item => ({
        useCase: item.category_name,
        totalReviews: item.total_reviews,
        positiveReviews: item.positive_reviews,
        negativeReviews: item.negative_reviews,
        satisfactionRate: item.positive_ratio * 100,
        categoryType: 'Performance' as const,
        topSatisfactionReasons: (item.positive_ratio * 100) > 50 ? [
          `${Math.round(item.positive_ratio * 100)}% positive sentiment`,
          `${item.positive_reviews} positive reviews`,
          ...(item.definition ? [`Context: ${item.definition}`] : [])
        ] : [],
        topGapReasons: (item.positive_ratio * 100) <= 50 ? [
          `${item.negative_reviews} negative reviews`,
          `${(item.positive_ratio * 100).toFixed(1)}% satisfaction rate`,
          ...(item.definition ? [`Context: ${item.definition}`] : [])
        ] : [],
        relatedCategories: [item.category_name],
        categoryDefinition: item.definition,
        productCount: item.total_reviews,
        categoryId: item.category_id
      }))

      setUseCaseData(transformedData)
    } catch (error) {
      console.error('Error fetching use case data:', error)
    } finally {
      setUseCaseLoading(false)
    }
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

      // 同时更新三个图表的数据，传递过滤器参数
      await Promise.all([
        fetchPainPointsData(filters),
        fetchDelightsData(filters),
        fetchUseCaseData(filters)
      ])
    } catch (error) {
      console.error('Error fetching filtered data:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // 初始化时获取三个图表的数据
  useEffect(() => {
    if (projectId) {
      fetchPainPointsData(initialFilters)
      fetchDelightsData(initialFilters)
      fetchUseCaseData(initialFilters)
    }
  }, [projectId, initialFilters])

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
      
      // 为underservedUseCases数据建立基于relatedDetailTexts的映射关系
      filteredData.reviewInsights.underservedUseCases.forEach(useCaseItem => {
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

  // const transformUseCaseData = (): UseCaseFeedback[] => {
  //   // 使用新的allUseCases数据而不是underservedUseCases
  //   return filteredData.reviewInsights.allUseCases
  //     .sort((a, b) => b.mentionCount - a.mentionCount)
  //     .slice(0, 15) // 取前15个
  //     .map(item => {
  //       return {
  //         useCase: item.useCase,
  //         totalMentions: item.mentionCount,
  //         positiveCount: item.positiveCount,
  //         negativeCount: item.negativeCount,
  //         satisfactionRate: item.satisfactionRate,
  //         categoryType: 'Performance', // 默认为Performance
  //         topSatisfactionReasons: item.satisfactionRate > 50 ? [
  //           `Good coverage for ${item.useCase}`,
  //           `${item.positiveCount} positive mentions`,
  //           ...(item.categoryDefinition ? [`Context: ${item.categoryDefinition}`] : [])
  //         ] : [],
  //         topGapReasons: item.satisfactionRate <= 50 ? [
  //           `${item.negativeCount} negative mentions`,
  //           `${item.satisfactionRate.toFixed(1)}% satisfaction rate`,
  //           ...(item.productCount ? [`Mentioned in ${item.productCount} products`] : []),
  //           ...(item.categoryDefinition ? [`Context: ${item.categoryDefinition}`] : [])
  //         ] : [],
  //         relatedCategories: [item.productAttribute],
  //         // Enhanced information
  //         categoryDefinition: item.categoryDefinition,
  //         productCount: item.productCount
  //       }
  //     })
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
          {painPointsLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-gray-500">loading...</div>
            </div>
          ) : (
            <CategoryPainPointsBar
              data={painPointsData}
              productType={selectedProductType}
              onProductTypeChange={handleProductTypeChange}
              reviewData={reviewData || undefined}
              projectId={projectId}
              filters={initialFilters}
            />
          )}
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
          {delightsLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-gray-500">loading...</div>
            </div>
          ) : (
            <CategoryPositiveFeedbackBar
              data={delightsData}
              productType={selectedProductType}
              onProductTypeChange={handleProductTypeChange}
              reviewData={reviewData || undefined}
              projectId={projectId}
              filters={initialFilters}
            />
          )}
        </ChartWithFilters>
      </section>

      {/* Use Case Sentiment Analysis */}
      <section data-chart-id="use-case-sentiment">
        <ChartHeader title=" Use Case Sentiment Analysis" icon={BarChart3} />
        <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
        Calculated from the latest 40 reviews per product in selected categories.


            </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
          {useCaseLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-gray-500">loading...</div>
            </div>
          ) : (
            <UseCaseSentimentMatrix
              data={useCaseData}
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
          )}
        </div>
      </section>

    </div>
  )
} 