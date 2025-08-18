"use client"

import { BarChart3, ExternalLink } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Tooltip } from "@/components/ui/tooltip"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import type { ProjectFilters } from "@/components/analysis-db/types/filters"
import { useChartsT } from "@/i18n/hooks"
import { databaseService } from "@/components/analysis-db/data/database-service"
import { useCallback, useEffect, useMemo, useState } from "react"

interface CustomerSatisfactionOverviewProps {
  projectId: string
  initialFilters?: ProjectFilters
}

type ProductItem = {
  asin: string
  product_title: string
  brand?: string
  unique_reviews_count: number
  rating?: number
  list_price?: number
  product_url?: string
}

export function CustomerSatisfactionOverview({ projectId, initialFilters }: CustomerSatisfactionOverviewProps) {
  const chartsT = useChartsT()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [products, setProducts] = useState<ProductItem[]>([])

  const loadData = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const data = await databaseService.getCustomerSatisfactionOverview(projectId)
      // data 可能是 { products: [...], total_products, ... } 或直接是数组
      const items: ProductItem[] = Array.isArray(data)
        ? data as ProductItem[]
        : (data?.products as ProductItem[]) || []
      setProducts(items || [])
    } catch (e) {
      const msg = (e as { message?: string })?.message || 'Failed to load'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [projectId])

  // 使用统一的过滤器管理，并在 filters 就绪或变化时拉数
  const { filters, handleFiltersReady, handleFiltersChange } = useChartWithFilters(
    CHART_NAMES.COMPETITOR_ANALYSIS,
    async () => { await loadData() },
    projectId,
    { initialFilters }
  )

  useEffect(() => {
    // 当 filtersReady 变为 true 时，useChartWithFilters 会调用 loadData
    // 这里无需重复调用
  }, [filters])

  const truncate = (title: string, max = 50) => (title?.length > max ? `${title.slice(0, max)}...` : title)
  const formatPrice = (price?: number) => (price ? `$${price.toFixed(2)}` : 'N/A')

  return (
    <div>
      <h2 className="text-xl font-bold text-gray-800 pl-0 mb-4">📊 {chartsT('competitorAnalysis')}</h2>
      <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2 pb-5">
        <BarChart3 className="w-5 h-5" />
        {chartsT('customerSatisfactionOverview')}
      </h3>

      <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
        {chartsT('calculatedFromLatest200Reviews')}
      </div>

      {/* 过滤器渲染器 - 接入项目统一过滤器系统 */}
      <FilterRenderer
        projectId={projectId}
        chartName={CHART_NAMES.COMPETITOR_ANALYSIS}
        currentFilters={filters}
        onChange={handleFiltersChange}
        onFiltersReady={handleFiltersReady}
        className="mb-6"
      />

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {Array.from({ length: 6 }).map((_, idx) => (
            <Card key={idx} className="p-4">
              <div className="animate-pulse">
                <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
                <div className="h-6 bg-gray-200 rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-gray-200 rounded w-2/3"></div>
              </div>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="p-6">
          <div className="text-center text-red-600">
            <h3 className="text-lg font-semibold mb-2">Error Loading Data</h3>
            <p>{error}</p>
          </div>
        </Card>
      ) : products.length === 0 ? (
        <Card className="p-6">
          <div className="text-center text-gray-500">
            <h3 className="text-lg font-semibold mb-2">No Data Available</h3>
            <p>No customer satisfaction data found for this project.</p>
          </div>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {products.map((p) => (
            <Card
              key={p.asin}
              className="p-4 hover:shadow-md transition-shadow cursor-pointer"
              onClick={() => { if (p.product_url) window.open(p.product_url, '_blank', 'noopener,noreferrer') }}
            >
              <div className="flex justify-between items-start mb-2">
                <div className="flex-1">
                  <Tooltip content={p.product_title}>
                    <h3 className="font-semibold text-gray-800 text-sm leading-tight">
                      {truncate(p.product_title)}
                    </h3>
                  </Tooltip>
                  <p className="text-xs text-gray-500 mt-1">{p.brand || 'Unknown'}</p>
                </div>
                {p.product_url && (
                  <Button
                    variant="ghost"
                    size="sm"
                    className="p-1 h-auto"
                    onClick={(e) => {
                      e.stopPropagation()
                      window.open(p.product_url, '_blank', 'noopener,noreferrer')
                    }}
                  >
                    <ExternalLink className="h-3 w-3" />
                  </Button>
                )}
              </div>

              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Reviews Analyzed</span>
                  <span className="text-sm font-medium">{(p.unique_reviews_count || 0).toLocaleString()}</span>
                </div>

                {typeof p.rating === 'number' && (
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-gray-500">Avg Rating</span>
                    <span className="text-sm font-medium">{p.rating.toFixed(1)} ⭐</span>
                  </div>
                )}

                <div className="flex justify-between items-center">
                  <span className="text-xs text-gray-500">Price</span>
                  <span className="text-sm font-medium">{formatPrice(p.list_price)}</span>
                </div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  )
}
