"use client"

import React, { useEffect, useMemo, useState, useCallback, useRef } from "react"
import { Card } from "@/components/ui/card"
import { FilterRenderer } from "@/components/analysis-db/filters/filter-renderer"
import { useChartWithFilters } from "@/components/analysis-db/hooks/use-chart-with-filters"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import type { ProjectFilters } from "../types/filters"
import { databaseService } from "../data/database-service"
import { UnifiedStackedBarChart } from "../shared/unified-stacked-bar-chart"
import { useReviewPanelQuery } from "../hooks/use-review-panel-query"
import { useChartsT } from "@/i18n/hooks"

interface CustomerPainPointsChartProps {
  projectId: string
  initialFilters?: ProjectFilters
}

type PainPointItem = {
  category_id: number
  category_name: string
  category_definition?: string
  type: "Physical" | "Performance"
  total_reviews: number
  positive_reviews: number
  negative_reviews: number
  negative_rate: number
  satisfaction_rate: number
  impacted_products: number
  related_detail_texts?: string[] | null
}

export function CustomerPainPointsChart({ projectId, initialFilters }: CustomerPainPointsChartProps) {
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
      pain_points: PainPointItem[]
    }>
  } | null>(null)

  // 过滤器状态管理
  const { filters, filtersReady, handleFiltersReady, handleFiltersChange } = useChartWithFilters(
    CHART_NAMES.CUSTOMER_PAIN_POINTS,
    async () => {
      await loadData()
    },
    projectId,
    { initialFilters }
  )

  // 记录本次查询使用的filters（后端请求体结构），供点击时传递
  type RequestFilters = {
    categories?: string[]
    brands?: string[]
    segments?: string[]
    extend_fields?: Record<string, unknown>
    asins?: string[]
  }
  const lastFiltersRef = useRef<RequestFilters | undefined>(undefined)

  const loadData = useCallback(async () => {
    if (!projectId) return
    setLoading(true)
    setError(null)
    try {
      // 使用 DatabaseService 的最终合并过滤器，确保与实际请求一致
      lastFiltersRef.current = databaseService.getFiltersFromState(CHART_NAMES.CUSTOMER_PAIN_POINTS).filters
      const data = await databaseService.getCustomerPainPointsGrouped(projectId)
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

  // 扁平化分组为图表数据（按各产品类别TopN拼接）
  type RowDatum = {
    name: string
    positive: number
    negative: number
    _categoryId: number
    _type: "Physical" | "Performance"
    _total: number
    _satisfaction: number
    _negativeRate: number
    _details?: string // serialize to string to satisfy index signature
    _definition?: string
  }

  const perGroupData = useMemo(() => {
    if (!grouped) return [] as Array<{ title: string; rows: Array<RowDatum> }>
    return grouped.groups.map(g => ({
      title: g.product_category,
      rows: g.pain_points.map(p => ({
        name: p.category_name,
        positive: p.positive_reviews,
        negative: p.negative_reviews,
        _categoryId: p.category_id as unknown as number,
        _type: p.type,
        _total: p.total_reviews,
        _satisfaction: p.satisfaction_rate,
        _negativeRate: p.negative_rate,
        _details: Array.isArray(p.related_detail_texts) ? p.related_detail_texts[0] : undefined,
        _definition: p.category_definition
      }))
    }))
  }, [grouped])

  // 自定义 Tooltip 组件
  const PainPointsTooltip = ({ active, payload }: { active?: boolean; payload?: Array<{ dataKey: string; payload: Record<string, string | number> }> }) => {
    if (!active || !payload || payload.length === 0) return null
    const row = payload[0].payload as unknown as RowDatum
    const satisfaction = Math.round(row._satisfaction)
    const negativeRate = Math.round(row._negativeRate)
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
        <div className="text-xs text-gray-900 font-semibold mb-1">Top Pain Details:</div>
        <ul className="list-disc pl-4 text-xs text-gray-800 mb-2 leading-snug">
          <li>{row.name}</li>
        </ul>
        <div className="text-xs text-gray-900 font-semibold mb-1">Top Pain Reasons:</div>
        <div className="text-xs text-red-600 space-y-1 leading-snug">
          <div>• {negativeRate}% negative sentiment</div>
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
            {chartsT('top10CustomerPainPoints')}
          </h3>
        </div>
      </div>

                  {/* 信息提示：与原页面一致的说明文案 */}
                  <div className="bg-blue-50 border-l-4 border-blue-600 p-4 mb-6">
            {chartsT('barsSortedByNegative')}
          </div>
      <div className="mt-6">
        <Card className="p-6 bg-gray-50 rounded-xl border shadow-sm">
          <FilterRenderer
            projectId={projectId}
            chartName={CHART_NAMES.CUSTOMER_PAIN_POINTS}
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
                      bottomBarType="negative"
                      CustomTooltip={PainPointsTooltip}
                      onBarClick={(data) => {
                        const payload = data as unknown as { name?: string; _categoryId?: number }
                        if (payload?._categoryId && projectId) {
                          handleCategoryClick(
                            projectId,
                            payload._categoryId,
                            payload.name || '',
                            ['phy','perf'],
                            lastFiltersRef.current,
                            group.title // 当前图表分组的 product_category
                          )
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


