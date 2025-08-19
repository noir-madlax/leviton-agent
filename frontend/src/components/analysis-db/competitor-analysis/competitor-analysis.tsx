"use client"

import { useState, useEffect, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Filter } from "lucide-react"
import { CompetitorMatrix } from "@/components/analysis-db/charts/competitor-matrix"
import { MissedOpportunitiesMatrix } from "@/components/analysis-db/charts/missed-opportunities-matrix"
// import CustomerSentimentScatter from "@/components/analysis-db/charts/customer-sentiment-scatter"
import { CompetitorAsinSelector } from "./competitor-asin-selector"

import { databaseService } from "@/components/analysis-db/data/database-service"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { ProjectFilters } from "@/components/analysis-db/types/filters"
import { supabase } from "@/lib/supabase"
import { useChartSections } from "@/components/integrated-dashboard/hooks/use-chart-sections"
import { useChartsT } from '@/i18n/hooks'
import { CustomerSatisfactionOverview } from "@/components/analysis-db/competitor-analysis/customer-satisfaction-overview"



interface CompetitorAnalysisProps {
  projectId: string | null;
  initialFilters?: ProjectFilters;
  data: {
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

// Fixed default competitor ASINs for Customer satisfaction overview
const DEFAULT_COMPETITOR_ASINS = [
  'B00NG0ELL0', // Leviton DSL06 - Mid-tier brand representative
  'B0BVKZLT3B', // Leviton D215S - Mid-tier brand representative  
  'B0BVKYKKRK', // Leviton D26HD - Mid-tier brand representative
  'B0BSHKS26L', // Lutron Caseta Diva - Mid-tier brand representative
  'B085D8M2MR', // Lutron Diva - Mid-tier brand representative
  'B01EZV35QU'  // Kasa HomeKit - Mid-tier brand representative
];

export function CompetitorAnalysis({ projectId, data, initialFilters }: CompetitorAnalysisProps) {
  // Get chart sections configuration for conditional rendering
  const { shouldShowChart } = useChartSections('competitor-analysis', projectId || '')
  const chartsT = useChartsT()

  const [selectedAsins, setSelectedAsins] = useState<string[]>([]);
  const [matrixViewData, setMatrixViewData] = useState<any>(null);
  const [useCaseMatrixViewData, setUseCaseMatrixViewData] = useState<any>(null);
  const [loading, setLoading] = useState(false);
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

  // 统一的数据加载函数
  const loadMatrixData = async (asins: string[]) => {
    if (!projectId || asins.length === 0) return;

    console.log(`🔄 Loading matrix data for ASINs: ${asins.join(', ')}`);
    setLoading(true);

    try {
      // 并行获取两种矩阵数据
      const [matrixResponse, useCaseMatrixResponse] = await Promise.all([
        databaseService.getCompetitorMatrixViewData(projectId, asins, 'phy_perf'),
        databaseService.getCompetitorMatrixViewData(projectId, asins, 'use')
      ]);

      console.log('🔍 [DEBUG-COMPETITOR] Physical/Performance matrix response:', matrixResponse);
      console.log('🔍 [DEBUG-COMPETITOR] Use case matrix response:', useCaseMatrixResponse);
      console.log('🔍 [DEBUG-COMPETITOR] Physical matrix data structure:', {
        status: matrixResponse?.status,
        aspectCategoriesCount: matrixResponse?.data?.aspect_categories?.length,
        productAspectDataCount: matrixResponse?.data?.product_aspect_data?.length,
        selectedAsins: matrixResponse?.data?.selected_asins,
        totalCategories: matrixResponse?.data?.total_categories
      });

      setMatrixViewData(matrixResponse);
      setUseCaseMatrixViewData(useCaseMatrixResponse);
      console.log('✅ Matrix data loaded successfully');
    } catch (error) {
      console.error('Error fetching matrix data:', error);
    } finally {
      setLoading(false);
    }
  };



  // 加载默认产品信息
  useEffect(() => {
    const loadDefaultProducts = async () => {
      if (!projectId) return;

      try {
        console.log('🔄 Loading default products...');

        // 直接查询固定的默认产品
        const { data: products, error: productsError } = await supabase
          .from('product_wide_table')
          .select('platform_id, title, brand, price_usd, reviews_count, category, product_url, rating')
          .in('platform_id', DEFAULT_COMPETITOR_ASINS);

        if (productsError) {
          console.error('Error fetching default products:', productsError);
          return;
        }

        // 按照 DEFAULT_COMPETITOR_ASINS 的顺序格式化产品数据
        const formattedProducts = DEFAULT_COMPETITOR_ASINS.map(asin => {
          const product = products?.find((p: any) => p.platform_id === asin);
          return product ? {
            platform_id: product.platform_id,
            title: product.title,
            brand: product.brand,
            price_usd: product.price_usd,
            reviews_count: product.reviews_count,
            category: product.category,
            product_url: product.product_url,
            rating: product.rating
          } : null;
        }).filter(Boolean) as Array<{
          platform_id: string
          title: string
          brand: string
          price_usd: number
          reviews_count: number
          category: string
          product_url?: string
          monthly_sales_volume?: number
          rating?: number | null
        }>;

        setDefaultProducts(formattedProducts);

        // 如果没有选择产品，设置默认选择并加载矩阵数据
        if (selectedAsins.length === 0) {
          setSelectedAsins(DEFAULT_COMPETITOR_ASINS);
          await loadMatrixData(DEFAULT_COMPETITOR_ASINS);
        }

        console.log('✅ Default products loaded successfully');
      } catch (error) {
        console.error('Error loading default products:', error);
      }
    };

    loadDefaultProducts();
  }, [projectId]);

  // 检测 tab 切换时的数据加载
  useEffect(() => {
    // 如果有 projectId 和 selectedAsins，但没有矩阵数据，则加载数据
    if (projectId && selectedAsins.length > 0 && (!matrixViewData || !useCaseMatrixViewData)) {
      console.log('🔄 Tab switch detected, loading matrix data...');
      loadMatrixData(selectedAsins);
    }
  }, [projectId, selectedAsins, matrixViewData, useCaseMatrixViewData]);

  // 处理产品选择变化
  const handleAsinSelectionChange = async (asins: string[]) => {
    console.log(`🔄 Product selection changed: ${asins.join(', ')}`);

    setSelectedAsins(asins);

    if (asins.length === 0) {
      setMatrixViewData(null);
      setUseCaseMatrixViewData(null);
      return;
    }

    if (!projectId) return;

    // 使用统一的加载函数
    setApplyLoading(true);
    try {
      await loadMatrixData(asins);
      console.log('✅ Product selection applied successfully');
    } catch (error) {
      console.error('Error applying product selection:', error);
    } finally {
      setApplyLoading(false);
    }
  };



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

  // Create ASIN to full product name mapping for tooltips
  const asinToFullProductNameMap = useMemo(() => {
    const map: Record<string, string> = {};
    defaultProducts.forEach(product => {
      map[product.platform_id] = product.title;
    });
    return map;
    }, [defaultProducts]);


  return (
    <div className="space-y-10 max-w-7xl mx-auto px-4">
      {/* ASIN Selection */}
      <section  >
        <div className="hidden md:block mb-4">
          <Button
            variant="outline"
            onClick={() => setShowAsinSelector(!showAsinSelector)}
            className="flex items-center gap-2"
          >
            <Filter className="w-4 h-4" />
            {showAsinSelector ? chartsT('hideProductSelection') : chartsT('showProductSelection')}
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
          <h3 className="text-lg font-medium text-gray-900 mb-2">{chartsT('applyingProductSelection')}</h3>
          <p className="text-sm text-gray-600 text-center max-w-md">{chartsT('loadingNewAnalysisData')}</p>
        </div>
      ) : (
        <>
          {/* Regular Loading State - 只在非Apply loading时显示 */}
          {loading && (
            <div className="flex justify-center items-center h-32">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
            </div>
          )}

      {/* Customer Satisfaction Overview - New Implementation */}
      {shouldShowChart('customer-satisfaction-overview') && (
      <section data-chart-id="customer-satisfaction-overview">
        <CustomerSatisfactionOverview
          projectId={projectId || ''}
          initialFilters={initialFilters}
        />
      </section>
      )}

      {/* Competitor Delights and Pain Points Matrix */}
      {shouldShowChart('product-comparison-dimensions') && (
      <section data-chart-id="product-comparison-dimensions">
        <ChartWithFilters
          chartId="product-comparison-dimensions"
          projectId={projectId || ''}
          title={chartsT('productComparisonByKeyDimensions')}
          projectFilters={initialFilters}
          chartType="matrix"
        >
          <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">{chartsT('matrixLegendExplanation')}</div>

          <CompetitorMatrix
            matrixViewData={matrixViewData}
            projectId={projectId || ''}
            asinToProductNameMap={asinToProductNameMap}
            asinToFullProductNameMap={asinToFullProductNameMap}
          />
        </ChartWithFilters>
      </section>
      )}

      {/* Use Case Matrix */}
      {shouldShowChart('product-comparison-use-cases') && (
      <section data-chart-id="product-comparison-use-cases">
        <ChartWithFilters
          chartId="product-comparison-use-cases"
          projectId={projectId || ''}
          title={chartsT('productComparisonByMainUseCases')}
          projectFilters={initialFilters}
          chartType="matrix"
        >
          <div className="bg-purple-50 border-l-4 border-purple-600 p-4 mb-6">{chartsT('matrixLegendExplanation')}</div>

          <MissedOpportunitiesMatrix
            matrixViewData={useCaseMatrixViewData}
            projectId={projectId || ''}
            asinToProductNameMap={asinToProductNameMap}
            asinToFullProductNameMap={asinToFullProductNameMap}
          />
        </ChartWithFilters>
      </section>
      )}

      {/* Customer Sentiment Analysis 
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
      */}
        </>
      )}
    </div>
  )
} 