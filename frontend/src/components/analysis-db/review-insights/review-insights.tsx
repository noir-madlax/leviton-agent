"use client"

import { useState, useEffect } from "react"

import { CategoryPainPointsBar } from "@/components/analysis-db/charts/category-pain-points-bar"
import { CategoryPositiveFeedbackBar } from "@/components/analysis-db/charts/category-positive-feedback-bar"
import CategoryUseCaseBar from "@/components/analysis-db/shared/category-use-case-bar"

import { CategoryFeedback, UseCaseFeedback, ProductType } from "@/components/analysis-db/data/category-feedback"

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
      }>
      customerLikes: Array<{
        feature: string
        category: string
        frequency: number
        satisfactionLevel: 'High' | 'Medium' | 'Low'
      }>
      underservedUseCases: Array<{
        useCase: string
        productAttribute: string
        gapLevel: number
        mentionCount: number
      }>
    }
    allReviewData: Record<string, Array<{
      id: string
      productId: string
      content: string
      sentiment: 'positive' | 'negative' | 'neutral'
      category: string
      aspect: string
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
  
  // 将数据库数据转换为图表所需的格式
  const transformPainPointsData = (): { topNegativeCategories: CategoryFeedback[] } => {
    const painPoints = data.reviewInsights.painPoints
    
    // 转换为CategoryFeedback格式
    const categoryFeedbacks: CategoryFeedback[] = painPoints
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 15) // 取前15个
      .map(item => ({
        category: item.aspect,
        categoryType: item.type === 'Physical' ? 'Physical' : 'Performance',
        mentions: item.frequency,
        satisfactionRate: Math.max(0, 100 - item.severity), // severity越高，satisfaction越低
        negativeRate: item.severity,
        positiveCount: Math.floor(item.frequency * (100 - item.severity) / 100),
        negativeCount: Math.floor(item.frequency * item.severity / 100),
        totalReviews: item.frequency,
        averageRating: Math.max(1, 5 - (item.severity / 20)), // severity转换为rating
        topNegativeAspects: [item.aspect],
        topPositiveAspects: [],
        topNegativeReasons: [`High severity: ${item.severity}%`],
        topPositiveReasons: []
      }))
    
    return {
      topNegativeCategories: categoryFeedbacks
    }
  }

  const transformPositiveFeedbackData = (): { topPositiveCategories: CategoryFeedback[] } => {
    const customerLikes = data.reviewInsights.customerLikes
    
    // 转换为CategoryFeedback格式
    const categoryFeedbacks: CategoryFeedback[] = customerLikes
      .sort((a, b) => b.frequency - a.frequency)
      .slice(0, 15) // 取前15个
      .map(item => {
        const satisfactionScore = item.satisfactionLevel === 'High' ? 90 : 
                                item.satisfactionLevel === 'Medium' ? 70 : 50
        
        return {
          category: item.feature,
          categoryType: item.category === 'physical' ? 'Physical' : 'Performance',
          mentions: item.frequency,
          satisfactionRate: satisfactionScore,
          negativeRate: 100 - satisfactionScore,
          positiveCount: Math.floor(item.frequency * satisfactionScore / 100),
          negativeCount: Math.floor(item.frequency * (100 - satisfactionScore) / 100),
          totalReviews: item.frequency,
          averageRating: 3 + (satisfactionScore / 50), // 转换为1-5星级
          topNegativeAspects: [],
          topPositiveAspects: [item.feature],
          topNegativeReasons: [],
          topPositiveReasons: [`${item.satisfactionLevel} satisfaction level`]
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
          topSatisfactionReasons: satisfactionRate > 50 ? [`Good coverage for ${item.useCase}`] : [],
          topGapReasons: item.gapLevel > 50 ? [`Gap level: ${item.gapLevel}%`] : [],
          relatedCategories: [item.productAttribute]
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
      {/* 分类痛点分析 */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-red-500 pl-4 mb-6">
          📊 Customer Pain Points by Category
        </h2>
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-700">
            🖱️ <strong>Interactive Chart:</strong> Click on any bar to view actual customer reviews mentioning those specific issues and pain points.
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