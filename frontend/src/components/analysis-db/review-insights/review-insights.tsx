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
      }>
      customerLikes: Array<{
        feature: string
        category: string
        frequency: number
        satisfactionLevel: 'High' | 'Medium' | 'Low'
        categoryDefinition?: string
        totalMentions?: number
        positiveRate?: number
      }>
      underservedUseCases: Array<{
        useCase: string
        productAttribute: string
        gapLevel: number
        mentionCount: number
        categoryDefinition?: string
        productCount?: number
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
}

export function ReviewInsights({ data }: ReviewInsightsProps) {
  const [selectedProductType, setSelectedProductType] = useState<ProductType>('dimmer')
  const [reviewData, setReviewData] = useState<Record<string, unknown> | null>(null)
  
  useEffect(() => {
    // Create the structure that charts expect using database data
    const reviewDataForCharts = {
      reviewsByCategory: data.allReviewData // This is the Record<string, Review[]> structure charts need
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
    return data.reviewInsights.underservedUseCases
      .sort((a, b) => b.mentionCount - a.mentionCount)
      .slice(0, 15) // 取前15个
      .map(item => {
        const satisfactionRate = Math.max(0, 100 - item.gapLevel)
        const positiveCount = Math.floor(item.mentionCount * satisfactionRate / 100)
        const negativeCount = item.mentionCount - positiveCount
        
        return {
          useCase: item.useCase,
          totalMentions: item.mentionCount,
          positiveCount,
          negativeCount,
          satisfactionRate,
          categoryType: 'Performance', // 默认为Performance
          topSatisfactionReasons: satisfactionRate > 50 ? [
            `Good coverage for ${item.useCase}`,
            ...(item.categoryDefinition ? [`Context: ${item.categoryDefinition}`] : [])
          ] : [],
          topGapReasons: item.gapLevel > 50 ? [
            `Gap level: ${item.gapLevel}%`,
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
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-700">
            🖱️ <strong>Interactive Chart:</strong> Click on any bar to view actual customer reviews mentioning those specific issues and pain points.
            <br />
            🎯 <strong>Enhanced Data:</strong> Now shows precise sentiment analysis with negative rates and category context.
          </p>
        </div>

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
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg">
          <p className="text-sm text-green-700">
            🖱️ <strong>Interactive Chart:</strong> Click on any bar to view actual customer reviews highlighting those positive aspects and strengths.
            <br />
            🎯 <strong>Enhanced Data:</strong> Now shows precise sentiment analysis with positive rates and detailed satisfaction levels.
          </p>
        </div>

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
        <div className="mb-4 p-3 bg-purple-50 border border-purple-200 rounded-lg">
          <p className="text-sm text-purple-700">
            🖱️ <strong>Interactive Chart:</strong> Click on any bar to explore customer reviews related to specific use cases and applications.
            <br />
            🎯 <strong>Enhanced Data:</strong> Now includes product coverage information and detailed context for better gap analysis.
          </p>
        </div>

        <CategoryUseCaseBar 
          data={useCases} 
          title="Use Case Analysis"
          description="Bar height = mention count, color = satisfaction level (green=high, yellow=medium, red=low) - Click bars to explore reviews"
          productType={selectedProductType}
          onProductTypeChange={handleProductTypeChange}
          reviewData={reviewData || undefined}
        />
      </section>


    </div>
  )
} 