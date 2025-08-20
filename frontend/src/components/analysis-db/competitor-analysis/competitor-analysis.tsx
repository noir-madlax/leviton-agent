"use client"

import { useState, useEffect, useMemo } from "react"
import { CompetitorMatrix } from "@/components/analysis-db/charts/competitor-matrix"
import { MissedOpportunitiesMatrix } from "@/components/analysis-db/charts/missed-opportunities-matrix"
// import CustomerSentimentScatter from "@/components/analysis-db/charts/customer-sentiment-scatter"
import { databaseService } from "@/components/analysis-db/data/database-service"
import type { ProjectFilters } from "@/components/analysis-db/types/filters"
import { useChartSections } from "@/components/integrated-dashboard/hooks/use-chart-sections"
import { ChartWithFilters } from "@/components/analysis-db/shared/chart-with-filters"
import { useChartsT } from '@/i18n/hooks'
import { CustomerSatisfactionOverview } from "@/components/analysis-db/competitor-analysis/customer-satisfaction-overview"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { supabase } from "@/lib/supabase"

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

// 若没有初始 ASIN 列表时的兜底默认值
const DEFAULT_COMPETITOR_ASINS = [
  'B00NG0ELL0',
  'B0BVKZLT3B',
  'B0BVKYKKRK',
  'B0BSHKS26L',
  'B085D8M2MR',
  'B01EZV35QU'
]

export function CompetitorAnalysis({ projectId, data, initialFilters }: CompetitorAnalysisProps) {
  // Get chart sections configuration for conditional rendering
  const { shouldShowChart } = useChartSections('competitor-analysis', projectId || '')
  const chartsT = useChartsT()

  const [matrixViewData, setMatrixViewData] = useState<any>(null)
  const [useCaseMatrixViewData, setUseCaseMatrixViewData] = useState<any>(null)
  const [loading, setLoading] = useState(false)
  const [applyLoading, setApplyLoading] = useState(false)

  // 父级统一维护的过滤器（提供给 FilterRenderer 的 currentFilters）
  const [parentFilters, setParentFilters] = useState<ProjectFilters>(initialFilters || {
    categories: [],
    asins: [],
    brands: [],
    segments: [],
    extend_fields: {},
    time_period: ""
  })
  // 用于通知子组件刷新
  const [refreshKey, setRefreshKey] = useState(0)
  // ASIN -> 产品名称映射（短名/全名）
  const [asinToProductNameMap, setAsinToProductNameMap] = useState<Record<string, string>>({})
  const [asinToFullProductNameMap, setAsinToFullProductNameMap] = useState<Record<string, string>>({})


  // 统一的数据加载函数（selected_asins 与其它过滤器从全局过滤器状态读取）
  const loadMatrixData = async () => {
    if (!projectId) return;

    console.log(`🔄 Loading matrix data (filters from state)`);
    setLoading(true);

    try {
      // 并行获取两种矩阵数据
      const [matrixResponse, useCaseMatrixResponse] = await Promise.all([
        databaseService.getCompetitorMatrixViewData(projectId, 'phy_perf'),
        databaseService.getCompetitorMatrixViewData(projectId, 'use')
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

      // 同步 ASIN -> 名称映射
      const selectedAsins = matrixResponse?.data?.selected_asins || []
      if (Array.isArray(selectedAsins) && selectedAsins.length > 0) {
        const { data: products } = await supabase
          .from('product_wide_table')
          .select('platform_id, title')
          .in('platform_id', selectedAsins)

        const nameMap: Record<string, string> = {}
        const fullNameMap: Record<string, string> = {}
        ;(products || []).forEach((p: any) => {
          const shortTitle = p.title && p.title.length > 30 ? `${p.title.substring(0, 30)}...` : p.title
          nameMap[p.platform_id] = shortTitle || p.platform_id
          fullNameMap[p.platform_id] = p.title || p.platform_id
        })
        setAsinToProductNameMap(nameMap)
        setAsinToFullProductNameMap(fullNameMap)
      }

      console.log('✅ Matrix data loaded successfully');
    } catch (error) {
      console.error('Error fetching matrix data:', error);
    } finally {
      setLoading(false);
    }
  };

  // 父级：FilterRenderer 触发的 onChange
  const handleParentFiltersChange = async (filters: ProjectFilters) => {
    setApplyLoading(true)
    setParentFilters(filters)
    try {
      await loadMatrixData()
      setRefreshKey(prev => prev + 1)
    } finally {
      setApplyLoading(false)
    }
  }

  // 父级：FilterRenderer 触发的 onFiltersReady（初次就绪时加载）
  const handleFiltersReady = async (isReady: boolean) => {
    if (!isReady) return
    setApplyLoading(true)
    try {
      await loadMatrixData()
      setRefreshKey(prev => prev + 1)
    } finally {
      setApplyLoading(false)
    }
  }

  // 首次挂载时，如需要可尝试初次加载（若后端需要过滤器就绪，则由 onFiltersReady 触发即可）
  useEffect(() => {
    if (projectId) {
      // 这里可以选择性预加载；当前依赖 onFiltersReady 即可
    }
  }, [projectId])

  // 父组件集中处理筛选应用，无需单独的 ASIN 选择与映射


  return (
    <div className="space-y-10 max-w-7xl mx-auto px-4">
      {/* Global Filters */}
      <section>
        <FilterRenderer
          projectId={projectId || ''}
          chartName={CHART_NAMES.COMPETITOR_ANALYSIS}
          currentFilters={parentFilters}
          onChange={handleParentFiltersChange}
          onFiltersReady={handleFiltersReady}
          className="mb-6"
        />
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
          refreshKey={refreshKey}
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