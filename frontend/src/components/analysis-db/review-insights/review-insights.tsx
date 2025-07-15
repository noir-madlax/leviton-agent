"use client"

import { useState, useEffect } from "react"

import { CategoryPainPointsBar } from "@/components/analysis-db/charts/category-pain-points-bar"
import { CategoryPositiveFeedbackBar } from "@/components/analysis-db/charts/category-positive-feedback-bar"
import CategoryUseCaseBar from "@/components/analysis-db/shared/category-use-case-bar"

import { CategoryFeedback, UseCaseFeedback, ProductType } from "@/components/analysis-db/types/analysis"

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
}

export function ReviewInsights({ data }: ReviewInsightsProps) {
  const [selectedProductType, setSelectedProductType] = useState<ProductType>('dimmer')
  const [reviewData, setReviewData] = useState<{ reviewsByCategory?: Record<string, unknown[]> } | null>(null)
  
  useEffect(() => {
    // Create the structure that charts expect using database data
    // 需要将数据结构转换为图表组件期待的格式
    const reviewDataForCharts = {
      reviewsByCategory: {} as Record<string, unknown[]>
    }
    
    // 如果有allReviewData，需要正确映射到类别名称
    if (data.allReviewData) {
      // 首先直接使用allReviewData的现有映射
      reviewDataForCharts.reviewsByCategory = { ...data.allReviewData }
      
      // 为痛点数据建立基于relatedDetailTexts的映射关系
      data.reviewInsights.painPoints.forEach(painPoint => {
        const aspectName = painPoint.aspect
        if (!reviewDataForCharts.reviewsByCategory[aspectName]) {
          const relatedReviews: unknown[] = []
          
          // 使用新的relatedDetailTexts字段进行映射
          if (painPoint.relatedDetailTexts && Array.isArray(painPoint.relatedDetailTexts)) {
            painPoint.relatedDetailTexts.forEach(detailText => {
              const reviews = data.allReviewData[detailText] || []
              relatedReviews.push(...reviews)
            })
          } else {
            // fallback: 如果没有relatedDetailTexts，使用原有逻辑
            Object.entries(data.allReviewData).forEach(([, reviews]) => {
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
      data.reviewInsights.customerLikes.forEach(like => {
        const featureName = like.feature
        if (!reviewDataForCharts.reviewsByCategory[featureName]) {
          const relatedReviews: unknown[] = []
          
          // 使用新的relatedDetailTexts字段进行映射
          if (like.relatedDetailTexts && Array.isArray(like.relatedDetailTexts)) {
            like.relatedDetailTexts.forEach(detailText => {
              const reviews = data.allReviewData[detailText] || []
              relatedReviews.push(...reviews)
            })
          } else {
            // fallback: 如果没有relatedDetailTexts，使用原有逻辑
            Object.entries(data.allReviewData).forEach(([, reviews]) => {
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
      data.reviewInsights.allUseCases.forEach(useCaseItem => {
        const useCaseName = useCaseItem.useCase
        
        if (!reviewDataForCharts.reviewsByCategory[useCaseName]) {
          const relatedReviews: unknown[] = []
          
          // 使用新的relatedDetailTexts字段进行映射
          if (useCaseItem.relatedDetailTexts && Array.isArray(useCaseItem.relatedDetailTexts)) {
            useCaseItem.relatedDetailTexts.forEach(detailText => {
              const reviews = data.allReviewData[detailText] || []
              relatedReviews.push(...reviews)
            })
          } else {
            // fallback: 如果没有relatedDetailTexts，使用原有逻辑
            Object.entries(data.allReviewData).forEach(([, reviews]) => {
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
      data.reviewInsights.underservedUseCases.forEach(useCaseItem => {
        const useCaseName = useCaseItem.useCase
        
        if (!reviewDataForCharts.reviewsByCategory[useCaseName]) {
          const relatedReviews: unknown[] = []
          
          // 使用新的relatedDetailTexts字段进行映射
          if (useCaseItem.relatedDetailTexts && Array.isArray(useCaseItem.relatedDetailTexts)) {
            useCaseItem.relatedDetailTexts.forEach(detailText => {
              const reviews = data.allReviewData[detailText] || []
              relatedReviews.push(...reviews)
            })
          } else {
            // fallback: 如果没有relatedDetailTexts，使用原有逻辑
            Object.entries(data.allReviewData).forEach(([, reviews]) => {
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
  }, [data])
  
  // 将数据库数据转换为图表所需的格式，利用新的增强字段
  const transformPainPointsData = (): { topNegativeCategories: CategoryFeedback[] } => {
    const painPoints = data.reviewInsights.painPoints
    
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
    const customerLikes = data.reviewInsights.customerLikes
    
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

  const transformUseCaseData = (): UseCaseFeedback[] => {
    // 使用新的allUseCases数据而不是underservedUseCases
    return data.reviewInsights.allUseCases
      .sort((a, b) => b.mentionCount - a.mentionCount)
      .slice(0, 15) // 取前15个
      .map(item => {
        return {
          useCase: item.useCase,
          totalMentions: item.mentionCount,
          positiveCount: item.positiveCount,
          negativeCount: item.negativeCount,
          satisfactionRate: item.satisfactionRate,
          categoryType: 'Performance', // 默认为Performance
          topSatisfactionReasons: item.satisfactionRate > 50 ? [
            `Good coverage for ${item.useCase}`,
            `${item.positiveCount} positive mentions`,
            ...(item.categoryDefinition ? [`Context: ${item.categoryDefinition}`] : [])
          ] : [],
          topGapReasons: item.satisfactionRate <= 50 ? [
            `${item.negativeCount} negative mentions`,
            `${item.satisfactionRate.toFixed(1)}% satisfaction rate`,
            ...(item.productCount ? [`Mentioned in ${item.productCount} products`] : []),
            ...(item.categoryDefinition ? [`Context: ${item.categoryDefinition}`] : [])
          ] : [],
          relatedCategories: [item.productAttribute],
          // Enhanced information
          categoryDefinition: item.categoryDefinition,
          productCount: item.productCount
        }
      })
  }

  const categoryPainPoints = transformPainPointsData()
  const categoryPositiveFeedback = transformPositiveFeedbackData()
  const useCases = transformUseCaseData()

  const handleProductTypeChange = (productType: ProductType) => {
    setSelectedProductType(productType)
  }

  return (
    <div className="space-y-10">
      {/* Enhanced header with migration info */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
        <h3 className="text-lg font-semibold text-blue-800 mb-2">📊 Enhanced Review Insights</h3>
        <p className="text-sm text-blue-700">
          Now powered by advanced sentiment analysis with precise positive/negative breakdowns and category definitions for better understanding.
        </p>
      </div>

      {/* 分类痛点分析 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-red-500 pl-4 mb-6">
          📊 Customer Pain Points by Category
        </h2>
       

        <CategoryPainPointsBar 
          data={categoryPainPoints.topNegativeCategories} 
          productType={selectedProductType}
          onProductTypeChange={handleProductTypeChange}
          reviewData={reviewData || undefined}
        />
      </section>

      {/* 分类正面反馈分析 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-green-500 pl-4 mb-6">
          ⭐ Customer Delights by Category
        </h2>
      

        <CategoryPositiveFeedbackBar 
          data={categoryPositiveFeedback.topPositiveCategories} 
          productType={selectedProductType}
          onProductTypeChange={handleProductTypeChange}
          reviewData={reviewData || undefined}
        />
      </section>

      {/* 使用场景满意度分析 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-purple-500 pl-4 mb-6">
          🎯 Use Case Satisfaction Analysis
        </h2>
       

        <CategoryUseCaseBar 
          data={useCases} 
          title="Top Mentioned Use Cases by Satisfaction Level"
          description="Bar height = mention count, color = satisfaction level (green=high, yellow=medium, red=low) - Click bars to explore reviews"
          productType={selectedProductType}
          onProductTypeChange={handleProductTypeChange}
          reviewData={reviewData || undefined}
          totalUseMentions={data.reviewInsights.totalUseMentions}
        />
      </section>


    </div>
  )
} 