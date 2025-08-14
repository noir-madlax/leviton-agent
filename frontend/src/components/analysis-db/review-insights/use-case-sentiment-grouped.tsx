"use client"

import React, { useEffect, useMemo, useState, useCallback } from "react"
import { Card } from "@/components/ui/card"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import type { ProjectFilters } from "../types/filters"
import { databaseService } from "../data/database-service"
import { UseCaseSentimentMatrix } from "../charts/use-case-sentiment-matrix"
import { useChartsT } from "@/i18n/hooks"

interface UseCaseSentimentGroupedProps {
  projectId: string
  initialFilters?: ProjectFilters
}

type UseCaseItem = {
  category_id: number
  use_case: string
  product_attribute: string
  total_reviews: number
  positive_reviews: number
  negative_reviews: number
  satisfaction_rate: number
  product_count: number
  category_definition?: string
  related_detail_texts?: string[] | null
}

export function UseCaseSentimentGrouped({ projectId, initialFilters }: UseCaseSentimentGroupedProps) {
  const chartsT = useChartsT()
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [grouped, setGrouped] = useState<{
    project_id: string
    selected_categories: string[]
    groups: Array<{
      product_category: string
      filtered_asins_count: number
      total_use_reviews: number
      total_categories: number
      all_use_cases: UseCaseItem[]
    }>
  } | null>(null)

  const { filters, filtersReady, handleFiltersReady, handleFiltersChange } = useChartWithFilters(
    CHART_NAMES.USE_CASE_SENTIMENT,
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
      const data = await databaseService.getUseCaseSentimentGrouped(projectId)
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
    if (!grouped) return [] as Array<{ title: string; rows: Array<{ useCase: string; totalReviews: number; positiveReviews: number; negativeReviews: number; categoryId?: number }> }>
    return grouped.groups.map(g => ({
      title: g.product_category,
      rows: g.all_use_cases.map(p => ({
        useCase: p.use_case,
        totalReviews: p.total_reviews,
        positiveReviews: p.positive_reviews,
        negativeReviews: p.negative_reviews,
        categoryId: p.category_id
      }))
    }))
  }, [grouped])

  return (
    <section className="mb-6">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
            {chartsT('useCaseSentimentAnalysis')}
          </h3>
        </div>
      </div>

      <div className="mt-6">
        <Card className="p-3 bg-gray-50 ">
          <FilterRenderer
            projectId={projectId}
            chartName={CHART_NAMES.USE_CASE_SENTIMENT}
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
                  <UseCaseSentimentMatrix
                    data={group.rows.map(r => ({
                      useCase: r.useCase,
                      totalReviews: r.totalReviews,
                      positiveReviews: r.positiveReviews,
                      negativeReviews: r.negativeReviews,
                      satisfactionRate: r.totalReviews > 0 ? (r.positiveReviews / r.totalReviews) * 100 : 0,
                      categoryType: 'Performance' as const,
                      topSatisfactionReasons: [],
                      topGapReasons: [],
                      relatedCategories: [r.useCase],
                      productCount: 1,
                      categoryId: r.categoryId
                    }))}
                    projectId={projectId}
                    filters={filters}
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


