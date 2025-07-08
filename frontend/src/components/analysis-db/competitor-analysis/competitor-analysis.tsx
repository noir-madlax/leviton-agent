"use client"

import { useState, useEffect, useMemo } from "react"
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
  const [defaultProducts, setDefaultProducts] = useState<Array<{
    platform_id: string
    title: string
    brand: string
    price_usd: number
    reviews_count: number
    category: string
    product_url?: string
    monthly_sales_volume?: number
  }>>([]);

  // Load default top 6 products by analysis review count on component mount
  useEffect(() => {
    const loadDefaultProducts = async () => {
      if (!projectId) return;
      
      try {
        // Get products ranked by analysis review count from current project
        const projectProducts = await databaseService.getProjectProductsByReviewCount(projectId);
        
        // Take top 6 products by analysis review count
        const topProducts = projectProducts.slice(0, 6);
        
        // Convert to the expected format
        const formattedProducts = topProducts.map(product => ({
          platform_id: product.platform_id,
          title: product.title,
          brand: product.brand,
          price_usd: product.price_usd,
          reviews_count: product.actual_review_count,
          category: product.category,
          product_url: product.product_url
        }));
        
        setDefaultProducts(formattedProducts);
        
        // If no custom selection, use these default products for analysis
        if (selectedAsins.length === 0) {
          const defaultAsins = topProducts.map(p => p.platform_id);
          setSelectedAsins(defaultAsins);
          
          // Load competitor data for default products
          if (defaultAsins.length > 0) {
            setLoading(true);
            try {
              const response = await databaseService.getCompetitorAnalysisDataByProject(
                projectId,
                undefined, // No category filters
                defaultAsins.join(',') // Selected ASINs as string
              );
              setCustomCompetitorData(response);
            } catch (error) {
              console.error('Error fetching default competitor data:', error);
            } finally {
              setLoading(false);
            }
          }
        }
      } catch (error) {
        console.error('Error loading default products:', error);
        
        // Fallback to original logic if new method fails
        try {
          const availableProducts = await databaseService.getAvailableAsins();
          const topProducts = availableProducts
            .sort((a, b) => b.reviews_count - a.reviews_count)
            .slice(0, 6);
          setDefaultProducts(topProducts);
        } catch (fallbackError) {
          console.error('Fallback also failed:', fallbackError);
        }
      }
    };

    loadDefaultProducts();
  }, [projectId]);

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

  // Use the pre-calculated matrix data from DatabaseService
  const realMatrixData = competitorData.matrixData

  // Use the pre-calculated use case data from DatabaseService and add missing fields
  const realUseCaseData = useCaseData.matrixData.map((item: any) => ({
    ...item,
    positiveCount: Math.floor(item.mentions * item.satisfactionRate / 100),
    negativeCount: Math.floor(item.mentions * (100 - item.satisfactionRate) / 100),
    totalReviews: item.mentions
  }))

  const handleProductClick = (productAsin: string) => {
    // Find the product info by ASIN
    const defaultProduct = defaultProducts.find(p => p.platform_id === productAsin);
    
    if (defaultProduct?.product_url) {
      window.open(defaultProduct.product_url, '_blank', 'noopener,noreferrer');
    } else {
      // Fallback: construct Amazon URL from ASIN
      const amazonUrl = `https://www.amazon.com/dp/${productAsin}`;
      window.open(amazonUrl, '_blank', 'noopener,noreferrer');
    }
  }

  // Calculate statistics for each product - including all selected products
  const productStats = competitorData.targetProducts.map((productAsin: string) => {
    const productData = competitorData.matrixData.filter((item: any) => item.product === productAsin)
    const actualTotalReviews = competitorData.productTotalReviews[productAsin] || 0  // Use actual total review count
    const totalMentions = productData.reduce((sum: number, item: any) => sum + item.mentions, 0)
    const categoriesCount = productData.length
    const avgSatisfaction = productData.length > 0 
      ? productData.reduce((sum: number, item: any) => sum + item.satisfactionRate, 0) / productData.length 
      : 0
    
    // Find the product info to get the title
    const productInfo = defaultProducts.find(p => p.platform_id === productAsin);
    const productTitle = productInfo?.title || productAsin;
    const shortTitle = productTitle.length > 50 ? `${productTitle.substring(0, 50)}...` : productTitle;
    
    return {
      asin: productAsin,
      name: shortTitle,
      fullTitle: productTitle,
      totalReviews: actualTotalReviews,  // Use actual total review count
      totalMentions,
      categoriesCount,
      avgSatisfaction: Math.round(avgSatisfaction * 10) / 10
    }
  }) // Show all selected products, including those without data

  // Create ASIN to product name mapping for child components
  const asinToProductNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    defaultProducts.forEach(product => {
      const shortTitle = product.title.length > 30 ? 
        `${product.title.substring(0, 30)}...` : 
        product.title;
      map[product.platform_id] = shortTitle;
    });
    return map;
  }, [defaultProducts]);

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
              key={stat.asin} 
              className="interactive-card p-4"
              onClick={() => handleProductClick(stat.asin)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                  e.preventDefault()
                  handleProductClick(stat.asin)
                }
              }}
              tabIndex={0}
              role="button"
              aria-label={`View ${stat.name} on Amazon`}
              title={`Click to view ${stat.name} on Amazon`}
            >
              <h4 className="font-medium text-gray-900 mb-3 text-sm flex items-center justify-between" title={stat.fullTitle}>
                {stat.name}
                <ExternalLink className="w-3 h-3 text-blue-500" />
              </h4>
              <div className="text-xs text-gray-600 space-y-2">
                <div className="flex justify-between">
                  <span>📝 Analyzed review count:</span>
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
          <strong>How to read this table:</strong> Each cell shows the number of unique analyzed customer reviews (large number) for that product-category combination, 
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
          asinToProductNameMap={asinToProductNameMap}
        />
      </section>

      {/* Use Case Matrix */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-purple-500 pl-4 mb-6">
          🎯 Use Case Matrix
        </h2>
        <div className="bg-purple-50 border-l-4 border-purple-600 p-4 mb-6">
          <strong>How to read this table:</strong> Each cell shows the number of unique analyzed customer reviews (large number) for that product-use case combination, 
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
          asinToProductNameMap={asinToProductNameMap}
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
          asinToProductNameMap={asinToProductNameMap}
        />
      </section>
    </div>
  )
} 