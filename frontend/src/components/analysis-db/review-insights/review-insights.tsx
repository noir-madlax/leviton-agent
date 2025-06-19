"use client"

import { useState, useEffect } from "react"

import { CategoryPainPointsBar } from "@/components/analysis-db/charts/category-pain-points-bar"
import { CategoryPositiveFeedbackBar } from "@/components/analysis-db/charts/category-positive-feedback-bar"
import CategoryUseCaseBar from "@/components/analysis-db/shared/category-use-case-bar"

import { getReviewData, allReviewData } from "@/components/analysis-db/data/review-data"

import { getCategoryFeedback, ProductType, getTopUseCases } from "@/components/analysis-db/data/category-feedback"

interface ReviewInsightsProps {
  // Placeholder for future props
  placeholder?: never
}

export function ReviewInsights({ }: ReviewInsightsProps) {
  const [selectedProductType, setSelectedProductType] = useState<ProductType>('dimmer')
  const [reviewData, setReviewData] = useState<Record<string, unknown> | null>(null)
  
  useEffect(() => {
    const reviewData = getReviewData()
    
    // Create the structure that charts expect
    const reviewDataForCharts = {
      ...reviewData,
      reviewsByCategory: allReviewData // This is the Record<string, Review[]> structure charts need
    }
    
    setReviewData(reviewDataForCharts)
  }, [])
  
  const categoryPainPoints = getCategoryFeedback(selectedProductType)
  const useCases = getTopUseCases(selectedProductType)

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
          reviewData={reviewData as any}
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
          data={categoryPainPoints.topPositiveCategories} 
          productType={selectedProductType}
          onProductTypeChange={handleProductTypeChange}
          reviewData={reviewData as any}
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
          reviewData={reviewData as any}
        />
      </section>


    </div>
  )
} 