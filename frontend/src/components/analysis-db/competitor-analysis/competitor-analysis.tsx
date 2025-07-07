"use client"

import { useState, useEffect } from "react"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ExternalLink, Filter } from "lucide-react"
import { CompetitorMatrix } from "@/components/analysis-db/charts/competitor-matrix"
import { CompetitorPainPointsMatrix } from "@/components/analysis-db/charts/competitor-pain-points-matrix"
import { MissedOpportunitiesMatrix } from "@/components/analysis-db/charts/missed-opportunities-matrix"
import { CustomerSentimentBar } from "@/components/analysis-db/charts/customer-sentiment-bar"
import { CompetitorAsinSelector } from "./competitor-asin-selector"
import { databaseService } from "@/components/analysis-db/data/database-service"
import { useProductPanel } from "@/components/analysis-db/contexts/product-panel-context"
interface CompetitorAnalysisProps {
  projectId: string | null;
  data: {
    competitorAnalysis: {
      targetProducts: string[]
      matrixData: Array<{
        product: string
        category: string
        categoryType: 'Physical' | 'Performance'
        mentions: number
        satisfactionRate: number
        positiveCount: number
        negativeCount: number
        totalReviews: number
      }>
      productTotalReviews: Record<string, number>
      useCaseData: {
        targetProducts: string[]
        matrixData: Array<{
          product: string
          useCase: string
          mentions: number
          satisfactionRate: number
          gapLevel: number
        }>
      }
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

export function CompetitorAnalysis({ projectId, data }: CompetitorAnalysisProps) {
  const [selectedAsins, setSelectedAsins] = useState<string[]>([]);
  const [customCompetitorData, setCustomCompetitorData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showAsinSelector, setShowAsinSelector] = useState(false);

  // Default to using the original data
  const competitorData = customCompetitorData || {
    targetProducts: data.competitorAnalysis.targetProducts,
    matrixData: data.competitorAnalysis.matrixData,
    productTotalReviews: data.competitorAnalysis.productTotalReviews
  }
  const useCaseData = customCompetitorData?.useCaseData || data.competitorAnalysis.useCaseData

  // Handle ASIN selection change
  const handleAsinSelectionChange = async (asins: string[]) => {
    setSelectedAsins(asins);
    
    if (asins.length === 0) {
      setCustomCompetitorData(null);
      return;
    }

    if (!projectId) return;

    try {
      setLoading(true);
      const response = await databaseService.getCompetitorAnalysisDataByProject(
        projectId,
        undefined, // No category filters
        asins.join(',') // Selected ASINs as string
      );
      setCustomCompetitorData(response);
    } catch (error) {
      console.error('Error fetching custom competitor data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Map product names to their ASINs (consistent with DatabaseService)
  const productToAsin: Record<string, string> = {
    'Philips Hue Smart': 'B08PKMT2DV',
    'CLOUDY BAY Dimmer': 'B0771BC2YH',
    'Lutron Credenza': 'B004DZONXI',
    'Feit Electric Smart': 'B07SXDFH38',
    'Leviton Trimatron': 'B073H9Y7SH',
    'Kasa HomeKit': 'B0BTMWZH3K'
  }

  // Use the pre-calculated matrix data from DatabaseService
  const realMatrixData = competitorData.matrixData

  // Use the pre-calculated use case data from DatabaseService and add missing fields
  const realUseCaseData = useCaseData.matrixData.map((item: any) => ({
    ...item,
    positiveCount: Math.floor(item.mentions * item.satisfactionRate / 100),
    negativeCount: Math.floor(item.mentions * (100 - item.satisfactionRate) / 100),
    totalReviews: item.mentions
  }))

  // Amazon product URLs for focal products
  const productUrls: Record<string, string> = {
    "Philips Hue Smart": "https://www.amazon.com/dp/B08PKMT2DV", // Philips Hue Smart Wireless Dimmer Switch V2
    "CLOUDY BAY Dimmer": "https://www.amazon.com/dp/B0771BC2YH", // Cloudy Bay in Wall Dimmer Switch
    "Lutron Credenza": "https://www.amazon.com/dp/B004DZONXI", // Lutron Credenza LED+ Plug-In Lamp Dimmer
    "Feit Electric Smart": "https://www.amazon.com/dp/B07SXDFH38", // Feit Electric Smart Dimmer Switch
    "Leviton Trimatron": "https://www.amazon.com/dp/B073H9Y7SH", // Leviton Trimatron Rotary Dimmer Switch
    "Kasa HomeKit": "https://www.amazon.com/dp/B0BTMWZH3K" // Kasa Apple HomeKit Smart Dimmer Switch
  }

  const handleProductClick = (productName: string) => {
    const url = productUrls[productName]
    if (url) {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  // Calculate statistics for each product - including all 6 products
  const productStats = competitorData.targetProducts.map((product: string) => {
    const productData = competitorData.matrixData.filter((item: any) => item.product === product)
    const actualTotalReviews = competitorData.productTotalReviews[product] || 0  // Use actual total review count
    const totalMentions = productData.reduce((sum: number, item: any) => sum + item.mentions, 0)
    const categoriesCount = productData.length
    const avgSatisfaction = productData.length > 0 
      ? productData.reduce((sum: number, item: any) => sum + item.satisfactionRate, 0) / productData.length 
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
      {/* ASIN Selection */}
      <section>
        <div className="mb-4">
          <Button
            variant="outline"
            onClick={() => setShowAsinSelector(!showAsinSelector)}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            {showAsinSelector ? 'Hide' : 'Show'} Product Selection
          </Button>
        </div>
        
        {showAsinSelector && (
          <CompetitorAsinSelector
            projectId={projectId}
            onSelectionChange={handleAsinSelectionChange}
            defaultSelection={selectedAsins}
          />
        )}
      </section>

      {/* Loading State */}
      {loading && (
        <div className="flex justify-center items-center h-32">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        </div>
      )}

      {/* Product Data Overview */}
      <section>
        <h2 className="text-xl font-bold text-gray-800 border-l-4 border-orange-500 pl-4 mb-4">
          📊 Product Data Overview
          {selectedAsins.length > 0 && (
            <span className="ml-2 text-sm font-normal text-gray-600">
              ({selectedAsins.length} custom products selected)
            </span>
          )}
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
          {productStats.map((stat: any) => (
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
          allReviewData={data.allReviewData}
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
          allReviewData={data.allReviewData}
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
          allReviewData={data.allReviewData}
        />
      </section>
    </div>
  )
} 