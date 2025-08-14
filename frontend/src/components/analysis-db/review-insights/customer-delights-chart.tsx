"use client"

import React, { useEffect, useMemo, useState, useCallback } from "react"
import { Card } from "@/components/ui/card"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import type { ProjectFilters } from "../types/filters"
import { databaseService } from "../data/database-service"
import { UnifiedStackedBarChart } from "../shared/unified-stacked-bar-chart"
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

  const perGroupData = useMemo(() => {
    if (!grouped) return [] as Array<{ title: string; rows: Array<{ name: string; positive: number; negative: number }> }>
    return grouped.groups.map(g => ({
      title: g.product_category,
      rows: g.customer_likes.map(p => ({
        name: p.category_name,
        positive: p.positive_reviews,
        negative: p.negative_reviews
      }))
    }))
  }, [grouped])

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
                  <UnifiedStackedBarChart
                    data={group.rows}
                    xAxisDataKey="name"
                    positiveDataKey="positive"
                    negativeDataKey="negative"
                    bottomBarType="positive" 
                  />
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


