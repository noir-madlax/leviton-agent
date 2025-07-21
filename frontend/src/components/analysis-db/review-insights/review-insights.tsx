"use client"

import { useState, useEffect } from "react"

import { CategoryPainPointsBar } from "@/components/analysis-db/charts/category-pain-points-bar"
import { CategoryPositiveFeedbackBar } from "@/components/analysis-db/charts/category-positive-feedback-bar"
import { ChartWithFilters, ChartHeader } from "@/components/analysis-db/shared/chart-with-filters"
import { BarChart3, Target } from "lucide-react"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { databaseService } from "@/components/analysis-db/data/database-service"

import { CategoryFeedback, ProductType, StandardizedInsightData, AllInsightsResponse } from "@/components/analysis-db/types/analysis"
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
        totalMentions?: number
        negativeRate?: number
        relatedDetailTexts?: string[] // Added for new mapping logic
      }>
      customerLikes: Array<{
        feature: string
        category: string
        frequency: number
        satisfactionLevel: 'High' | 'Medium' | 'Low'
        categoryDefinition?: string
        totalMentions?: number
        positiveRate?: number
        relatedDetailTexts?: string[] // Added for new mapping logic
      }>
      allUseCases: Array<{
        useCase: string
        productAttribute: string
        satisfactionRate: number
        mentionCount: number
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
        mentionCount: number
        categoryDefinition?: string
        productCount?: number
        relatedDetailTexts?: string[] // Added for new mapping logic
      }>
      totalUseMentions: number
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
  const [reviewData, setReviewData] = useState<{
    painPointsReviews?: Record<string, unknown[]>
    customerLikesReviews?: Record<string, unknown[]>
    useCaseReviews?: Record<string, unknown[]>
  } | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [filteredData, setFilteredData] = useState<{
    reviewInsights: typeof data.reviewInsights
    allReviewData: typeof data.allReviewData
  }>({ reviewInsights: data.reviewInsights, allReviewData: data.allReviewData })
  
  // New state for standardized data
  const [standardizedInsights, setStandardizedInsights] = useState<{
    delights?: StandardizedInsightData
    pain_points?: StandardizedInsightData
    use_cases?: StandardizedInsightData
  }>({})
  const [useStandardizedData, setUseStandardizedData] = useState(false)
  const [isDataSwitching, setIsDataSwitching] = useState(false)
  
  // Environment check - only show debug panel in development
  const isDevelopment = typeof window !== 'undefined' && (
    window.location.hostname === 'localhost' || 
    window.location.hostname === '127.0.0.1' ||
    process.env.NODE_ENV === 'development'
  )

  // Fetch standardized insights data
  const fetchStandardizedData = async (): Promise<boolean> => {
    if (!projectId) return false
    
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/insights/all/${projectId}`)
      if (!response.ok) {
        throw new Error(`Failed to fetch standardized data: ${response.statusText}`)
      }
      
      const result: AllInsightsResponse = await response.json()
      if (result.success && result.data) {
        setStandardizedInsights(result.data)
        console.log('Standardized insights loaded:', result.data)
        return true
      }
      return false
    } catch (error) {
      console.error('Error fetching standardized insights:', error)
      return false
    }
  }

  // Fetch traditional insights data (force refresh)
  const fetchTraditionalData = async () => {
    if (!projectId) return
    
    try {
      const [reviewInsights, allReviewData] = await Promise.all([
        databaseService.getReviewInsightsDataByProject(
          projectId,
          initialFilters?.categories || [],
          initialFilters?.brands || [],
          initialFilters?.segments || [],
          initialFilters?.extend_fields || {}
        ),
        databaseService.getAllReviewDataByProject(
          projectId,
          initialFilters?.categories || [],
          initialFilters?.brands || [],
          initialFilters?.segments || [],
          initialFilters?.extend_fields || {}
        )
      ])
      
      setFilteredData({
        reviewInsights,
        allReviewData
      })
      console.log('Traditional insights refreshed:', { reviewInsights, allReviewData })
    } catch (error) {
      console.error('Error fetching traditional data:', error)
    }
  }

  // Handle data source toggle with forced refresh
  const handleDataSourceToggle = async () => {
    if (!projectId) return
    
    setIsDataSwitching(true)
    const newValue = !useStandardizedData
    
    try {
      if (newValue) {
        // Switching to standardized data - force refresh standardized data
        console.log('Switching to standardized data, refreshing...')
        const success = await fetchStandardizedData()
        if (success) {
          setUseStandardizedData(true)
        } else {
          console.log('Standardized data loading failed, staying with traditional data')
          // Keep using traditional data if standardized fails
        }
      } else {
        // Switching to traditional data - force refresh traditional data  
        console.log('Switching to traditional data, refreshing...')
        await fetchTraditionalData()
        setUseStandardizedData(false)
      }
    } catch (error) {
      console.error('Error during data source switch:', error)
    } finally {
      setIsDataSwitching(false)
    }
  }

  // Load standardized data on component mount and when projectId changes
  useEffect(() => {
    if (projectId) {
      fetchStandardizedData().then((success) => {
        // Only enable standardized data if it was successfully loaded
        setUseStandardizedData(success)
        if (!success) {
          console.log('Standardized data loading failed, falling back to traditional data')
        }
      })
    }
  }, [projectId])

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
    } catch (error) {
      console.error('Error fetching filtered data:', error)
    } finally {
      setIsLoading(false)
    }
  }
  
  useEffect(() => {
    // Create the structure that charts expect using database data
    // 需要将数据结构转换为图表组件期待的格式
    const reviewDataForCharts = {
      painPointsReviews: {} as Record<string, unknown[]>,     // 第一个图表：痛点数据
      customerLikesReviews: {} as Record<string, unknown[]>,  // 第二个图表：客户喜爱数据
      useCaseReviews: {} as Record<string, unknown[]>         // 第三个图表：用例数据
    }
    
    // 如果有allReviewData，需要正确映射到类别名称
    if (filteredData.allReviewData) {
      // 为痛点数据建立基于relatedDetailTexts的映射关系
      filteredData.reviewInsights.painPoints.forEach(painPoint => {
        const aspectName = painPoint.aspect
        if (!reviewDataForCharts.painPointsReviews[aspectName]) {
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
            reviewDataForCharts.painPointsReviews[aspectName] = relatedReviews
          }
        }
      })
      
      // 为亮点数据建立映射关系：feature 对应 review.category
      filteredData.reviewInsights.customerLikes.forEach(like => {
        const featureName = like.feature
        if (!reviewDataForCharts.customerLikesReviews[featureName]) {
          const relatedReviews: unknown[] = []

          // 直接通过 category 匹配
          Object.entries(filteredData.allReviewData).forEach(([, reviews]) => {
            reviews.forEach(review => {
              if (review.category === featureName) {
                relatedReviews.push(review)
              }
            })
          })

          if (relatedReviews.length > 0) {
            reviewDataForCharts.customerLikesReviews[featureName] = relatedReviews
          }
        }
      })
      
      // 为Use Case数据建立映射关系：useCase 对应 review.category
      filteredData.reviewInsights.allUseCases.forEach(useCaseItem => {
        const useCaseName = useCaseItem.useCase

        if (!reviewDataForCharts.useCaseReviews[useCaseName]) {
          const relatedReviews: unknown[] = []

          // 直接通过 category 匹配
          Object.entries(filteredData.allReviewData).forEach(([, reviews]) => {
            reviews.forEach(review => {
              if (review.category === useCaseName) {
                relatedReviews.push(review)
              }
            })
          })

          console.log("relatedReviews", relatedReviews)

          if (relatedReviews.length > 0) {
            reviewDataForCharts.useCaseReviews[useCaseName] = relatedReviews
          }
        }
      })
      
      // // 为underservedUseCases数据建立基于relatedDetailTexts的映射关系
      // filteredData.reviewInsights.underservedUseCases.forEach(useCaseItem => {
      //   const useCaseName = useCaseItem.useCase
        
      //   if (!reviewDataForCharts.reviewsByCategory[useCaseName]) {
      //     const relatedReviews: unknown[] = []
          
      //     // 使用新的relatedDetailTexts字段进行映射
      //     if (useCaseItem.relatedDetailTexts && Array.isArray(useCaseItem.relatedDetailTexts)) {
      //       useCaseItem.relatedDetailTexts.forEach(detailText => {
      //         const reviews = filteredData.allReviewData[detailText] || []
      //         relatedReviews.push(...reviews)
      //       })
      //     } else {
      //       // fallback: 如果没有relatedDetailTexts，使用原有逻辑
      //       Object.entries(filteredData.allReviewData).forEach(([, reviews]) => {
      //         reviews.forEach(review => {
      //           if (review.aspect && useCaseName.toLowerCase().includes(review.aspect.toLowerCase())) {
      //             relatedReviews.push(review)
      //           } else if (review.category && useCaseName.toLowerCase().includes(review.category.toLowerCase())) {
      //             relatedReviews.push(review)
      //           } else if (useCaseItem.productAttribute && 
      //                      (review.aspect?.toLowerCase().includes(useCaseItem.productAttribute.toLowerCase()) ||
      //                       review.category?.toLowerCase().includes(useCaseItem.productAttribute.toLowerCase()))) {
      //             relatedReviews.push(review)
      //           }
      //         })
      //       })
      //     }
          
      //     if (relatedReviews.length > 0) {
      //       reviewDataForCharts.reviewsByCategory[useCaseName] = relatedReviews
      //     }
      //   }
      // })
    }
    
    setReviewData(reviewDataForCharts)
  }, [filteredData])
  
  // 将数据库数据转换为图表所需的格式，利用新的增强字段
  const transformPainPointsData = (): { topNegativeCategories: CategoryFeedback[] } => {
    const painPoints = filteredData.reviewInsights.painPoints
    
    // 转换为CategoryFeedback格式，使用实际的情感分析数据
    const categoryFeedbacks: CategoryFeedback[] = painPoints
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 15) // 取前15个
      .map(item => {
        // 使用新字段提供更精确的数据
        const totalMentions = item.totalMentions || item.frequency
        const negativeRate = item.negativeRate || item.severity
        const positiveRate = 100 - negativeRate
        const negativeCount = Math.floor(totalMentions * negativeRate / 100)
        const positiveCount = totalMentions - negativeCount
        
        return {
          category: item.aspect,
          categoryType: item.type === 'Physical' ? 'Physical' : 'Performance',
          mentions: totalMentions,
          satisfactionRate: positiveRate,
          negativeRate: negativeRate,
          positiveCount: positiveCount,
          negativeCount: negativeCount,
          totalReviews: totalMentions,
          averageRating: Math.max(1, 5 - (negativeRate / 20)), // 基于负面率计算平均评分
          topNegativeAspects: [item.aspect],
          topPositiveAspects: [],
          topNegativeReasons: [
            `${Math.round(negativeRate)}% negative sentiment`,
            ...(item.categoryDefinition ? [`Context: ${item.categoryDefinition}`] : [])
          ],
          topPositiveReasons: [],
          // Enhanced tooltip information
          categoryDefinition: item.categoryDefinition,
          impactedProducts: item.impactedProducts
        }
      })
    
    return {
      topNegativeCategories: categoryFeedbacks
    }
  }

  const transformPositiveFeedbackData = (): { topPositiveCategories: CategoryFeedback[] } => {
    const customerLikes = filteredData.reviewInsights.customerLikes
    
    // 转换为CategoryFeedback格式，使用实际的情感分析数据
    const categoryFeedbacks: CategoryFeedback[] = customerLikes
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 15) // 取前15个
      .map(item => {
        // 使用新字段提供更精确的数据
        const totalMentions = item.totalMentions || item.frequency
        const positiveRate = item.positiveRate || (item.satisfactionLevel === 'High' ? 90 : 
                                                   item.satisfactionLevel === 'Medium' ? 70 : 50)
        const negativeRate = 100 - positiveRate
        const positiveCount = Math.floor(totalMentions * positiveRate / 100)
        const negativeCount = totalMentions - positiveCount
        
        return {
          category: item.feature,
          categoryType: item.category === 'physical' ? 'Physical' : 'Performance',
          mentions: totalMentions,
          satisfactionRate: positiveRate,
          negativeRate: negativeRate,
          positiveCount: positiveCount,
          negativeCount: negativeCount,
          totalReviews: totalMentions,
          averageRating: 3 + (positiveRate / 50), // 基于正面率计算评分
          topNegativeAspects: [],
          topPositiveAspects: [item.feature],
          topNegativeReasons: [],
          topPositiveReasons: [
            `${Math.round(positiveRate)}% positive sentiment`,
            `${item.satisfactionLevel} satisfaction level`,
            ...(item.categoryDefinition ? [`Context: ${item.categoryDefinition}`] : [])
          ],
          // Enhanced tooltip information
          categoryDefinition: item.categoryDefinition
        }
      })
    
    return {
      topPositiveCategories: categoryFeedbacks
    }
  }

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

  const categoryPainPoints = transformPainPointsData()
  const categoryPositiveFeedback = transformPositiveFeedbackData()
  // const useCases = transformUseCaseData() // Commented out as it's not used currently

  const handleProductTypeChange = (productType: ProductType) => {
    setSelectedProductType(productType)
  }

  return (
    <div className="space-y-10">
      
      {/* Debug Toggle for Standardized Data - Only show in development */}
      {isDevelopment && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-yellow-800">Data Source Selection (Debug Mode)</h4>
              <p className="text-sm text-yellow-600">
                {useStandardizedData 
                  ? 'Using standardized data from Python script logic' 
                  : 'Using traditional dashboard API data'}
              </p>
            </div>
            <div className="flex items-center gap-3">
              {isDataSwitching && (
                <div className="flex items-center gap-2 text-sm text-yellow-600">
                  <div className="animate-spin rounded-full h-4 w-4 border-2 border-yellow-600 border-t-transparent"></div>
                  Loading...
                </div>
              )}
              <button
                onClick={handleDataSourceToggle}
                disabled={isDataSwitching}
                className={`px-4 py-2 rounded text-sm font-medium transition-colors ${
                  isDataSwitching 
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : useStandardizedData 
                      ? 'bg-green-600 hover:bg-green-700 text-white' 
                      : 'bg-gray-600 hover:bg-gray-700 text-white'
                }`}
              >
                {isDataSwitching 
                  ? 'Switching...' 
                  : useStandardizedData 
                    ? 'Standardized ON' 
                    : 'Traditional ON'}
              </button>
            </div>
          </div>
          
          {/* Data Statistics */}
          <div className="mt-3 pt-3 border-t border-yellow-200">
            <div className="grid grid-cols-2 gap-4 text-xs">
              <div>
                <span className="font-medium text-yellow-800">Standardized Data:</span>
                <div className="text-yellow-600">
                  {Object.keys(standardizedInsights).length > 0 ? (
                    <>
                      Types: {Object.keys(standardizedInsights).join(', ')}<br/>
                      Total categories: {Object.values(standardizedInsights).reduce((sum, data) => sum + Object.keys(data || {}).length, 0)}
                    </>
                  ) : (
                    'Not loaded'
                  )}
                </div>
              </div>
              <div>
                <span className="font-medium text-yellow-800">Traditional Data:</span>
                <div className="text-yellow-600">
                  Pain Points: {filteredData.reviewInsights.painPoints?.length || 0}<br/>
                  Customer Likes: {filteredData.reviewInsights.customerLikes?.length || 0}<br/>
                  Use Cases: {filteredData.reviewInsights.allUseCases?.length || 0}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* 分类痛点分析 */}
      <section data-chart-id="customer-pain-points">
        <h2 className="text-2xl font-bold text-gray-800 pl-0 mb-6">
          📊 Customer Pain Points by Category
        </h2>
       
        
        <ChartWithFilters
          chartId="customer-pain-points"
          chartType="bar"
          projectId={projectId || ''}
          title="Top 10 Customer Pain Points by Category"
          projectFilters={initialFilters}
          onFilterChange={handleFilterChange}
        >
           <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
          Analysis uses up to 200 most recent reviews per product (all-time data)
            </div>
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-gray-500">正在更新数据...</div>
            </div>
          ) : (
            <CategoryPainPointsBar
              data={categoryPainPoints.topNegativeCategories}
              productType={selectedProductType}
              onProductTypeChange={handleProductTypeChange}
              reviewData={{ reviewsByCategory: reviewData?.painPointsReviews || {} }}
              standardizedData={standardizedInsights.pain_points}
              useStandardizedData={useStandardizedData}
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
          title="Top 10 Customer Delights by Category"
          projectFilters={initialFilters}
          onFilterChange={handleFilterChange}
        >
            <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
          Analysis uses up to 200 most recent reviews per product (all-time data)
            </div>
          {isLoading ? (
            <div className="flex items-center justify-center p-8">
              <div className="text-gray-500">Loading...</div>
            </div>
          ) : (
            <CategoryPositiveFeedbackBar
              data={categoryPositiveFeedback.topPositiveCategories}
              productType={selectedProductType}
              onProductTypeChange={handleProductTypeChange}
              reviewData={{ reviewsByCategory: reviewData?.customerLikesReviews || {} }}
              standardizedData={standardizedInsights.delights}
              useStandardizedData={useStandardizedData}
            />
          )}
        </ChartWithFilters>
      </section>

      {/* Use Case Sentiment Analysis */}
      <section data-chart-id="use-case-sentiment">
        <ChartHeader title=" Use Case Sentiment Analysis" icon={BarChart3} />
        <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
          Analysis uses up to 200 most recent reviews per product (all-time data)
            </div>
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mt-6">
          <UseCaseSentimentMatrix 
            data={filteredData.reviewInsights.allUseCases.map(item => ({
              useCase: item.useCase,
              totalMentions: item.mentionCount,
              positiveCount: item.positiveCount,
              negativeCount: item.negativeCount,
              satisfactionRate: item.satisfactionRate,
              categoryType: 'Performance' as const,
              topSatisfactionReasons: [],
              topGapReasons: [],
              relatedCategories: [item.productAttribute],
              categoryDefinition: item.categoryDefinition,
              productCount: item.productCount
            }))} 
            reviewData={{ reviewsByCategory: reviewData?.useCaseReviews as Record<string, Array<{
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
            }>> || {} }}
            standardizedData={standardizedInsights.use_cases}
            useStandardizedData={useStandardizedData}
          />
        </div>
      </section>

    </div>
  )
} 