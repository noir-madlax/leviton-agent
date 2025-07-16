"use client"

import { useState, useEffect, useMemo } from "react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { ExternalLink, Filter } from "lucide-react"
import { CompetitorMatrix } from "@/components/analysis-db/charts/competitor-matrix"
import { MissedOpportunitiesMatrix } from "@/components/analysis-db/charts/missed-opportunities-matrix"
import CustomerSentimentScatter from "@/components/analysis-db/charts/customer-sentiment-scatter"
import { CompetitorAsinSelector } from "./competitor-asin-selector"
import { databaseService } from "@/components/analysis-db/data/database-service"
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
  // 添加专门的Apply loading状态
  const [applyLoading, setApplyLoading] = useState(false);
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
    rating?: number | null
  }>>([]);

  // 添加数据准备状态管理
  const [isDataReady, setIsDataReady] = useState(false);

  // Load default top 6 products by analysis review count on component mount
  useEffect(() => {
    const loadDefaultProducts = async () => {
      if (!projectId) return;
      
      // 重置数据准备状态
      setIsDataReady(false);
      
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
          product_url: product.product_url,
          rating: product.rating
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
              // 数据加载完成，设置为ready
              setIsDataReady(true);
            } catch (error) {
              console.error('Error fetching default competitor data:', error);
              // 即使出错也要设置为ready，避免无限loading
              setIsDataReady(true);
            } finally {
              setLoading(false);
            }
          } else {
            // 没有默认产品时也设置为ready
            setIsDataReady(true);
          }
        } else {
          // 已有自定义选择时设置为ready
          setIsDataReady(true);
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
          // 设置为ready
          setIsDataReady(true);
        } catch (fallbackError) {
          console.error('Fallback also failed:', fallbackError);
          // 最终设置为ready
          setIsDataReady(true);
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

  // Handle ASIN selection change - 修改为支持Apply loading状态
  const handleAsinSelectionChange = async (asins: string[]) => {
    setSelectedAsins(asins);
    
    if (asins.length === 0) {
      setCustomCompetitorData(null);
      setApplyLoading(false); // 确保重置loading状态
      return;
    }

    if (!projectId) return;

    try {
      // 使用Apply loading状态，提供更好的用户体验
      setApplyLoading(true);
      console.log('🔄 Applying product selection changes, loading new analysis data...');
      
      const response = await databaseService.getCompetitorAnalysisDataByProject(
        projectId,
        undefined, // No category filters
        asins.join(',') // Selected ASINs as string
      );
      
      // 模拟一个短暂延迟确保用户能看到loading状态
      await new Promise(resolve => setTimeout(resolve, 500));
      
      setCustomCompetitorData(response);
      console.log('✅ Analysis data updated successfully');
    } catch (error) {
      console.error('Error fetching custom competitor data:', error);
    } finally {
      setApplyLoading(false);
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
      avgSatisfaction: Math.round(avgSatisfaction * 10) / 10,
      rating: productInfo?.rating || null
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

  // Create ASIN to brand mapping for child components
  const asinToBrandMap = useMemo(() => {
    const map: Record<string, string> = {};
    defaultProducts.forEach(product => {
      map[product.platform_id] = product.brand;
    });
    return map;
  }, [defaultProducts]);

  // 如果数据还没有准备好，显示loading状态
  if (!isDataReady) {
    return (
      <div className="space-y-10 max-w-7xl mx-auto px-4">
        <div className="flex justify-center items-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
          <span className="ml-2">Loading competitor analysis data...</span>
        </div>
      </div>
    );
  }

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

      {/* Apply Loading State - 统一的loading状态，隐藏所有内容 */}
      {applyLoading ? (
        <div className="flex flex-col justify-center items-center h-96 bg-white rounded-lg border">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
          <h3 className="text-lg font-medium text-gray-900 mb-2">Applying Product Selection</h3>
          <p className="text-sm text-gray-600 text-center max-w-md">
            Loading new analysis data for selected products. All charts and data will be updated together.
          </p>
        </div>
      ) : (
        <>
          {/* Regular Loading State - 只在非Apply loading时显示 */}
          {loading && (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}

      {/* Product Data Overview */}
      <section>
        <h2 className="text-xl font-bold text-gray-800 border-l-4 border-orange-500 pl-4 mb-4">
          📊 Customer satisfaction overview
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
               
                {stat.rating && (
                  <div className="flex justify-between">
                    <span>⭐ Average star rating:</span>
                    <span className="font-medium text-yellow-600">
                      {stat.rating.toFixed(1)}
                    </span>
                  </div>
                )}

              </div>
            </Card>
          ))}
        </div>
      </section>

      {/* Competitor Delights and Pain Points Matrix */}
      <section>
        <h2 className="text-2xl font-bold text-gray-800 border-l-4 border-blue-500 pl-4 mb-6">
          🏆 Product Comparison by Key Dimensions
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
          🎯 Product Comparison by Main Use Cases
        </h2>
        <div className="bg-purple-50 border-l-4 border-purple-600 p-4 mb-6">
          <strong>How to read this table:</strong> Number refers to the count of reviews; Percentage: refers to the % of positive reviews)
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
          <strong>Sentiment Overview:</strong> Scatter plot showing review count vs average star rating with brand color coding.
          Products positioned by review volume and rating to understand market attention and customer sentiment patterns.
        </div>

        <CustomerSentimentScatter 
          data={competitorData.matrixData}
          productTotalReviews={competitorData.productTotalReviews}
          allReviewData={data.allReviewData}
          asinToProductNameMap={asinToProductNameMap}
          asinToBrandMap={asinToBrandMap}
        />
      </section>
        </>
      )}
    </div>
  )
} 