"use client"

import { useMemo } from "react"
import { Card } from "@/components/ui/card"
import { ExternalLink } from "lucide-react"
import { CompetitorMatrix } from "@/components/analysis/charts/competitor-matrix"
import { MissedOpportunitiesMatrix } from "@/components/analysis/charts/missed-opportunities-matrix"
import { CustomerSentimentBar } from "@/components/analysis/charts/customer-sentiment-bar"
import { ReviewPanel } from "@/components/analysis/panels/review-panel"
import { useReviewPanel } from "@/components/analysis/contexts/review-panel-context"
import { getCompetitorAnalysisData, getUseCaseAnalysisData } from "@/components/analysis/data/competitor-analysis"
import { allReviewData } from "@/components/analysis/data/review-data"

export function CompetitorAnalysis() {
  const competitorData = getCompetitorAnalysisData()
  const useCaseData = getUseCaseAnalysisData()
  const reviewPanel = useReviewPanel()

  // Map product names to their ASINs
  const productToAsin: Record<string, string> = {
    'Leviton D26HD': 'B0BVKYKKRK',
    'Leviton D215S': 'B0BVKZLT3B', 
    'Lutron Caseta Diva': 'B0BSHKS26L',
    'TP Link Switch': 'B01EZV35QU',
    'Leviton DSL06': 'B00NG0ELL0',
    'Lutron Diva': 'B085D8M2MR'
  }

  // Generate matrix data based on actual review counts
  const realMatrixData = useMemo(() => {
    const products = competitorData.targetProducts
    const categories = [...new Set(competitorData.matrixData.map(item => item.category))]
    
    const realData: any[] = []
    
    products.forEach(product => {
      const productAsin = productToAsin[product]
      if (!productAsin) return
      
      categories.forEach(category => {
        const categoryReviews = allReviewData[category] || []
        const productReviews = categoryReviews.filter(review => review.productId === productAsin)
        
        // Calculate satisfaction rate from actual reviews
        const positiveReviews = productReviews.filter(review => review.sentiment === 'positive')
        const negativeReviews = productReviews.filter(review => review.sentiment === 'negative')
        const totalReviews = positiveReviews.length + negativeReviews.length
        const satisfactionRate = totalReviews > 0 ? (positiveReviews.length / totalReviews) * 100 : 0
        
        // Get category type from original data
        const originalData = competitorData.matrixData.find(item => 
          item.product === product && item.category === category
        )
        
        realData.push({
          product,
          category,
          categoryType: originalData?.categoryType || 'Physical',
          mentions: productReviews.length, // Use actual review count
          satisfactionRate: Math.round(satisfactionRate * 10) / 10,
          positiveCount: positiveReviews.length,
          negativeCount: negativeReviews.length,
          totalReviews: totalReviews
        })
      })
    })
    
    return realData
  }, [competitorData, allReviewData])

  // Generate use case matrix data based on actual review counts
  const realUseCaseData = useMemo(() => {
    const products = useCaseData.targetProducts
    const useCases = [...new Set(useCaseData.matrixData.map(item => item.useCase))]
    
    const realData: any[] = []
    
    products.forEach(product => {
      const productAsin = productToAsin[product]
      if (!productAsin) return
      
      useCases.forEach(useCase => {
        const categoryReviews = allReviewData[useCase] || []
        const productReviews = categoryReviews.filter(review => review.productId === productAsin)
        
        // Calculate satisfaction rate from actual reviews
        const positiveReviews = productReviews.filter(review => review.sentiment === 'positive')
        const negativeReviews = productReviews.filter(review => review.sentiment === 'negative')
        const totalReviews = positiveReviews.length + negativeReviews.length
        const satisfactionRate = totalReviews > 0 ? (positiveReviews.length / totalReviews) * 100 : 0
        
        realData.push({
          product,
          useCase,
          mentions: productReviews.length, // Use actual review count
          satisfactionRate: Math.round(satisfactionRate * 10) / 10,
          positiveCount: positiveReviews.length,
          negativeCount: negativeReviews.length,
          totalReviews: totalReviews,
          gapLevel: Math.round((100 - satisfactionRate) * 10) / 10
        })
      })
    })
    
    return realData
  }, [useCaseData, allReviewData])

  // Amazon product URLs for focal products
  const productUrls: Record<string, string> = {
    "Leviton D26HD": "https://www.amazon.com/dp/B0BVKYKKRK", // Leviton D26HD-1BZ Universal Dimmer
    "Leviton D215S": "https://www.amazon.com/dp/B0BVKZLT3B", // Leviton D215S-1BW 15A Decora Switch
    "Leviton DSL06": "https://www.amazon.com/dp/B00NG0ELL0", // Leviton DSL06-1LZ Slide Dimmer
    "Lutron Caseta Diva": "https://www.amazon.com/dp/B01M3XJUAD", // Lutron Caseta Smart Dimmer Kit
    "TP Link Switch": "https://www.amazon.com/dp/B01EZV35QU", // TP-Link Smart Wi-Fi Light Switch
    "Lutron Diva": "https://www.amazon.com/dp/B085D8M2MR" // Lutron Diva C·L Dimmer
  }

  const handleProductClick = (productName: string) => {
    const url = productUrls[productName]
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  // Calculate statistics for each product - including all 6 products
  const productStats = competitorData.targetProducts.map(product => {
    const productData = competitorData.matrixData.filter(item => item.product === product)
    const actualTotalReviews = competitorData.productTotalReviews[product] || 0  // Use actual total review count
    const totalMentions = productData.reduce((sum, item) => sum + item.mentions, 0)
    const categoriesCount = productData.length
    const avgSatisfaction = productData.length > 0 
      ? productData.reduce((sum, item) => sum + item.satisfactionRate, 0) / productData.length 
      : 0
    
    return {
      name: product,
      totalReviews: actualTotalReviews,  // Use actual total review count
      totalMentions,
      categoriesCount,
      avgSatisfaction: Math.round(avgSatisfaction * 10) / 10
    }
  }) // Show all 6 products, including those without data

  return (
    <div className="space-y-10 max-w-7xl mx-auto px-4">
      {/* Product Data Overview */}
      <section>
        <h2 className="text-xl font-bold text-gray-800 border-l-4 border-orange-500 pl-4 mb-4">
          📊 Product Data Overview
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {productStats.map((stat) => (
            <Card 
              key={stat.name} 
              className="interactive-card p-4"
              onClick={() => handleProductClick(stat.name)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  handleProductClick(stat.name)
                }
              }}
              tabIndex={0}
              role="button"
              aria-label={`View ${stat.name} on Amazon`}
              title={`Click to view ${stat.name} on Amazon`}
            >
              <h4 className="font-medium text-gray-900 mb-3 text-sm flex items-center justify-between">
                {stat.name}
                <ExternalLink className="w-3 h-3 text-blue-500" />
              </h4>
              <div className="text-xs text-gray-600 space-y-2">
                <div className="flex justify-between">
                  <span>📝 Reviews:</span>
                  <span className="font-medium">{stat.totalReviews}</span>
                </div>
                <div className="flex justify-between">
                  <span>😊 Satisfaction:</span>
                  <span className={`font-medium ${stat.avgSatisfaction >= 60 ? 'text-green-600' : stat.avgSatisfaction >= 40 ? 'text-yellow-600' : 'text-red-600'}`}>
                    {stat.avgSatisfaction}%
                  </span>
                </div>
                <div className="text-xs text-blue-500 mt-2 text-center">
                  Click to view on Amazon
                </div>
              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Competitor Delights and Pain Points Matrix */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">
          🏆 Competitor Delights and Pain Points Matrix
        </h2>
        <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
          <strong>How to read this table:</strong> Each cell shows the number of unique customer reviews (large number) for that product-category combination, 
          with the satisfaction rate (%) below. Categories are ranked by frequency across all products. 
          <strong>Click any cell to view the actual reviews.</strong> 
          Color coding: <span className="bg-green-100 text-green-800 px-1 rounded">Green (85%+ satisfaction)</span>, 
          <span className="bg-yellow-100 text-yellow-800 px-1 rounded">Yellow (70-84%)</span>, 
          <span className="bg-orange-100 text-orange-800 px-1 rounded">Orange (60-69%)</span>, 
          <span className="bg-red-100 text-red-800 px-1 rounded">Red (&lt;60%)</span>, 
          <span className="bg-gray-100 text-gray-400 px-1 rounded">Gray (no reviews)</span>.
        </div>

        <CompetitorMatrix 
          data={realMatrixData}
          targetProducts={competitorData.targetProducts}
        />
      </section>

      {/* Use Case Matrix */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-purple-500 pl-4 mb-6">
          🎯 Use Case Matrix
        </h2>
        <div className="bg-purple-50 border-l-4 border-purple-600 p-4 mb-6">
          <strong>How to read this table:</strong> Each cell shows the number of unique customer reviews (large number) for that product-use case combination, 
          with the satisfaction rate (%) below. Use cases are ranked by frequency across all products. 
          <strong>Click any cell to view the actual reviews.</strong> 
          Color coding: <span className="bg-green-100 text-green-800 px-1 rounded">Green (85%+ satisfaction)</span>, 
          <span className="bg-yellow-100 text-yellow-800 px-1 rounded">Yellow (70-84%)</span>, 
          <span className="bg-orange-100 text-orange-800 px-1 rounded">Orange (60-69%)</span>, 
          <span className="bg-red-100 text-red-800 px-1 rounded">Red (&lt;60%)</span>, 
          <span className="bg-gray-100 text-gray-400 px-1 rounded">Gray (no reviews)</span>.
        </div>

        <MissedOpportunitiesMatrix 
          data={realUseCaseData}
          targetProducts={useCaseData.targetProducts}
        />
      </section>

      {/* Customer Sentiment Analysis */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-green-500 pl-4 mb-6">
          📈 Customer Sentiment Analysis
        </h2>
        <div className="bg-green-50 border-l-4 border-green-600 p-4 mb-6">
          <strong>Sentiment Overview:</strong> Horizontal bar chart showing total review volume per product with satisfaction rate color coding.
          Products ranked by review volume to understand market attention and customer sentiment patterns.
        </div>

        <CustomerSentimentBar 
          data={competitorData.matrixData}
          productTotalReviews={competitorData.productTotalReviews}
        />
      </section>

    </div>
  )
} 