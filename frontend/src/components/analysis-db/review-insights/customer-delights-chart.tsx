"use client"

import React, { useEffect, useMemo, useState, useCallback } from "react"
import { Card } from "@/components/ui/card"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import type { ProjectFilters } from "../types/filters"
import { databaseService } from "../data/database-service"
import { UnifiedStackedBarChart } from "../shared/unified-stacked-bar-chart"
import { useReviewPanelQuery } from "../hooks/use-review-panel-query"
import { useChartsT } from "@/i18n/hooks"

interface CustomerDelightsChartProps {
  projectId: string
  initialFilters?: ProjectFilters
}

type DelightItem = {
  category_id: number
  category_name: string
  category_definition?: string
  type: "Physical" | "Performance"
  total_reviews: number
  positive_reviews: number
  negative_reviews: number
  positive_rate: number
  satisfaction_level: "High" | "Medium" | "Low"
  impacted_products: number
  related_detail_texts?: string[] | null
}

export function CustomerDelightsChart({ projectId, initialFilters }: CustomerDelightsChartProps) {
  const chartsT = useChartsT()
  const { handleCategoryClick, isLoading } = useReviewPanelQuery()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [grouped, setGrouped] = useState<{
    project_id: string
    selected_categories: string[]
    groups: Array<{
      product_category: string
      filtered_asins_count: number
      total_categories: number
      customer_likes: DelightItem[]
    }>
  } | null>(null)

  const { filters, filtersReady, handleFiltersReady, handleFiltersChange } = useChartWithFilters(
    CHART_NAMES.CUSTOMER_DELIGHTS,
    async () => {
      await loadData()
    },
    projectId,
    { initialFilters }
  )

  const loadData = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      const data = await databaseService.getCustomerDelightsGrouped(projectId)
      setGrouped(data)
    } catch (e) {
      const err = e as { message?: string }
      setError(err?.message || 'Failed to load')
    } finally {
      setLoading(false)
    }
  }, [projectId])

  useEffect(() => {
    if (projectId && filtersReady) {
      loadData()
    }
  }, [projectId, filtersReady, loadData])

  type RowDatum = {
    name: string
    positive: number
    negative: number
    _categoryId: number
    _type: "Physical" | "Performance"
    _total: number
    _positiveRate: number
    _details?: string
    _definition?: string
    _satisfactionLevel?: string
  }

  const perGroupData = useMemo(() => {
    if (!grouped) return [] as Array<{ title: string; rows: Array<RowDatum> }>
    return grouped.groups.map(g => ({
      title: g.product_category,
      rows: g.customer_likes.map(p => ({
        name: p.category_name,
        positive: p.positive_reviews,
        negative: p.negative_reviews,
        _categoryId: p.category_id as unknown as number,
        _type: p.type,
        _total: p.total_reviews,
        _positiveRate: p.positive_rate,
        _details: undefined,
        _definition: p.category_definition,
        _satisfactionLevel: p.satisfaction_level
      }))
    }))
  }, [grouped])

  // 自定义 Tooltip（紧凑样式，参考示例）
  const StrengthTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ dataKey: string; payload: Record<string, string | number> }> }) => {
    if (!active || !payload || payload.length === 0) return null
    const row = payload[0].payload as unknown as RowDatum
    const satisfaction = Math.round(row._positiveRate || (row._total > 0 ? (row.positive / row._total) * 100 : 0))
    return (
      <div className="bg-white rounded-lg shadow-lg p-2.5 max-w-[300px] border border-gray-200">
        <div className="text-gray-900 font-bold text-sm mb-1">{row.name}</div>
        <div className="text-xs text-gray-700 space-y-1 mb-2 leading-snug">
          <div><span className="font-semibold">Type:</span> {row._type}</div>
          <div className="text-green-600 font-semibold">Positive Mentions: {row.positive.toLocaleString()}</div>
          <div className="text-red-600 font-semibold">Negative Mentions: {row.negative.toLocaleString()}</div>
          <div className="text-blue-600 font-semibold">Total Mentions: {row._total.toLocaleString()}</div>
          <div className="text-gray-800">Satisfaction Rate: {satisfaction}%</div>
        </div>
        <div className="text-xs text-gray-900 font-semibold mb-1">Top Strength Details:</div>
        <ul className="list-disc pl-4 text-xs text-gray-800 mb-2 leading-snug">
          <li>{row.name}</li>
        </ul>
        <div className="text-xs text-gray-900 font-semibold mb-1">Top Strength Reasons:</div>
        <div className="text-xs text-green-700 space-y-1 leading-snug">
          <div>• {satisfaction}% positive sentiment</div>
          {row._satisfactionLevel && (
            <div>• {row._satisfactionLevel.toLowerCase()} satisfaction level</div>
          )}
          {(row._definition || row._details) && (
            <div>• Context: {row._definition || row._details}</div>
          )}
        </div>
      </div>
    )
  }

  return (
    <section className="mb-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            {chartsT('top10CustomerDelights')}
          </h3>
        </div>
      </div>

      <div className="mt-6">

          {/* Info banner about sorting and calculation rule */}
          <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6 text-sm text-blue-900">
            Bars are sorted by descending positive reviews left to right, calculated from the ~50 most recent reviews per product in selected categories.
          </div>
        <Card className="p-6 bg-gray-50 rounded-xl border shadow-sm">
          <FilterRenderer
            projectId={projectId}
            chartName={CHART_NAMES.CUSTOMER_DELIGHTS}
            currentFilters={filters}
            onChange={handleFiltersChange}
            onFiltersReady={handleFiltersReady}
            disabled={loading}
            className="mb-6"
          />


          {loading ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-3"></div>
                <p className="text-sm text-gray-600">{chartsT('updatingChartData')}</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex items-center justify-center py-20">
              <div className="text-center">
                <p className="text-sm text-red-600 mb-3">{chartsT('dataLoadFailed')}: {error}</p>
                <button onClick={loadData} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm">
                  {chartsT('retry')}
                </button>
              </div>
            </div>
          ) : grouped && perGroupData.length > 0 ? (
            <div className="space-y-10">
              {perGroupData.map((group, idx) => (
                <div key={`${group.title}-${idx}`}>
                  <h4 className="text-md font-semibold mb-4">{group.title}</h4>
                  <div className="relative">
                    {isLoading && (
                      <div className="absolute inset-0 bg-white/50 flex items-center justify-center z-10 rounded-lg">
                        <div className="flex items-center gap-3 bg-white px-4 py-3 rounded-lg shadow-lg border">
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                          <span className="text-gray-700 font-medium">Loading review details...</span>
                        </div>
                      </div>
                    )}
                    <UnifiedStackedBarChart
                      data={group.rows}
                      xAxisDataKey="name"
                      positiveDataKey="positive"
                      negativeDataKey="negative"
                      bottomBarType="positive"
                      CustomTooltip={StrengthTooltip}
                      onBarClick={(data) => {
                        const payload = data as unknown as { name?: string; _categoryId?: number }
                        if (payload?._categoryId && projectId) {
                          handleCategoryClick(projectId, payload._categoryId, payload.name || '', ['phy','perf'], filters)
                        }
                      }}
                    />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-gray-100 p-4 rounded">
              <p className="text-sm text-gray-600 text-center">{chartsT('noDataAvailable')}</p>
            </div>
          )}
        </Card>
      </div>
    </section>
  )
}


