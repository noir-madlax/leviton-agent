import { useState, useEffect, useCallback } from 'react'
import { databaseService } from '@/components/analysis-db/data/database-service'
import {
  UnifiedFilterData,
  UnifiedFilterCacheState,
  FilterDefaultsResponse,
  FilterDefaultItem,
  ChartFilterConfiguration,
  FilterConfig
} from '../types/filters'
import { filterStateManager } from '../stores'
import type { ChartFilterState } from '../stores'
import { CHART_NAMES } from '../constants'

// 全局缓存存储
const unifiedFilterCacheStore = new Map<string, UnifiedFilterCacheState>()

// 全局加载状态跟踪，防止同一项目的并发请求
const loadingPromises = new Map<string, Promise<void>>()

interface UnifiedFilterDataReturn {
  filterData: UnifiedFilterData | null
  isLoading: boolean
  error: string | null
  refreshData: () => Promise<void>
  getChartConfig: (chartName: string) => ChartFilterConfiguration | null
}

/**
 * 🔧 将API响应转换为按图表分组的数据结构
 */
function transformFilterDefaults(apiResponse: FilterDefaultsResponse): UnifiedFilterData {
  const charts: Record<string, ChartFilterConfiguration> = {}

  // 按chartName分组
  const groupedByChart = apiResponse.reduce((acc, item) => {
    if (!acc[item.chartName]) {
      acc[item.chartName] = []
    }
    acc[item.chartName].push(item)
    return acc
  }, {} as Record<string, FilterDefaultItem[]>)

  // 转换为ChartFilterConfiguration结构
  Object.entries(groupedByChart).forEach(([chartName, items]) => {
    const config: ChartFilterConfiguration = {
      chartName,
      filters: {}
    }

    items.forEach(item => {
      const filterConfig: FilterConfig = {
        values: item.filterValues,
        options: item.options || item.filterValues, // 🆕 优先使用options，回退到filterValues
        isVisible: item.isVisible === true
      }

      console.log(`🔧 [TRANSFORM] Processing filter: ${item.chartName}.${item.filterName}`, {
        values: item.filterValues,
        options: item.options,
        isVisible: item.isVisible
      })

      switch (item.filterName) {
        case 'categories':
          config.filters.categories = filterConfig
          break
        case 'asins':
          config.filters.asins = filterConfig
          break
        case 'brands':
          config.filters.brands = filterConfig
          break
        case 'product_segments':
          config.filters.product_segments = filterConfig
          break
        case 'time_period':
          config.filters.time_period = filterConfig
          break
        case 'extend_fields':
          config.filters.extend_fields = filterConfig
          break
      }
    })

    charts[chartName] = config
  })

  console.log('🔧 [TRANSFORM] Transformed filter data by charts:', charts)

  return { charts }
}

export function useUnifiedFilterData(projectId: string): UnifiedFilterDataReturn {
  const [cacheState, setCacheState] = useState<UnifiedFilterCacheState>(() => {
    // 从缓存中获取或初始化
    const cached = unifiedFilterCacheStore.get(projectId)
    if (cached) {
      return cached
    }

    return {
      data: null,
      loading: true,
      error: null,
      lastUpdated: null
    }
  })

  // 🆕 便捷方法：获取特定图表的配置
  const getChartConfig = useCallback((chartName: string): ChartFilterConfiguration | null => {
    return cacheState.data?.charts[chartName] || null
  }, [cacheState.data])

  // 🆕 加载过滤器默认配置数据
  const loadFilterData = useCallback(async (projectId: string, forceRefresh = false) => {
    const cached = unifiedFilterCacheStore.get(projectId)

    // 如果缓存存在且不强制刷新，且缓存时间不超过30分钟，则直接返回缓存
    if (cached && cached.data && !forceRefresh && cached.lastUpdated) {
      const cacheAge = Date.now() - cached.lastUpdated
      if (cacheAge < 30 * 60 * 1000) { // 30分钟缓存仍然有效
        console.log('🔍 [UNIFIED-FILTER] Using cached data for project:', projectId)
        setCacheState(cached)
        return
      }
    }

    // 检查是否已有正在进行的请求，如果有则等待该请求完成
    const existingPromise = loadingPromises.get(projectId)
    if (existingPromise && !forceRefresh) {
      console.log('🔍 [UNIFIED-FILTER] Waiting for existing request for project:', projectId)
      await existingPromise
      // 请求完成后，重新获取缓存状态
      const updatedCache = unifiedFilterCacheStore.get(projectId)
      if (updatedCache) {
        setCacheState(updatedCache)
      }
      return
    }

    // 更新加载状态
    const newState: UnifiedFilterCacheState = {
      data: cached?.data || null,
      loading: true,
      error: null,
      lastUpdated: cached?.lastUpdated || null
    }

    setCacheState(newState)
    unifiedFilterCacheStore.set(projectId, newState)

    // 创建加载Promise并存储，防止并发请求
    const loadingPromise = (async () => {
      try {
        console.log('🔍 [UNIFIED-FILTER] Starting API request for project:', projectId)

        // 🆕 调用新的过滤器默认值API
        const filterDefaults = await databaseService.getProjectFilterDefaultsNew(projectId)

        console.log('🔍 [UNIFIED-FILTER] Raw filter defaults received:', {
          total_items: filterDefaults.length,
          charts: [...new Set(filterDefaults.map(item => item.chartName))],
          project_id: projectId
        })

        // 🆕 转换数据结构
        const unifiedData = transformFilterDefaults(filterDefaults)

        console.log('🔍 [UNIFIED-FILTER] Transformed filter data:', {
          charts_count: Object.keys(unifiedData.charts).length,
          available_charts: Object.keys(unifiedData.charts),
          project_config: unifiedData.charts.project,
          tam_config: unifiedData.charts['market-share-analysis'],
          project_id: projectId
        })

        // 🆕 将 Project 过滤器写入全局状态（GlobalFilterState）——在首次进入 loading 状态前就先置空结构，避免头部等待
        const projectChartConfig: ChartFilterConfiguration | undefined = unifiedData.charts[CHART_NAMES.PROJECT]
        if (projectChartConfig) {
          const categoriesValues = projectChartConfig.filters.categories?.values
          const brandsValues = projectChartConfig.filters.brands?.values
          const segmentsValues = projectChartConfig.filters.product_segments?.values
          const timePeriodValues = projectChartConfig.filters.time_period?.values
          const extendFieldsValues = projectChartConfig.filters.extend_fields?.values

          const toStringArray = (v: unknown): string[] => Array.isArray(v) ? (v.filter((x): x is string => typeof x === 'string')) : []
          const toPeriodString = (v: unknown): string => {
            if (typeof v === 'string') return v
            if (Array.isArray(v) && v.length > 0 && typeof v[0] === 'string') return v[0]
            return ''
          }

          const chartState: Partial<ChartFilterState> = {
            filters: {
              categories: toStringArray(categoriesValues as unknown),
              brands: toStringArray(brandsValues as unknown),
              segments: toStringArray(segmentsValues as unknown),
              extend_fields: (extendFieldsValues && typeof extendFieldsValues === 'object') ? (extendFieldsValues as Record<string, unknown>) : {}
            },
            timeframe: { period: toPeriodString(timePeriodValues as unknown) },
            metadata: { syncedFromProject: true, syncTimestamp: Date.now() }
          }

          filterStateManager.updateChartFilters(CHART_NAMES.PROJECT, chartState)
          console.log('🌍 [UNIFIED-FILTER] Project filters seeded into GlobalFilterState:', chartState)
        } else {
          console.log('ℹ️ [UNIFIED-FILTER] No project chart config found in unified filter data')
          // 即便后端此时无配置，也推送一个空的项目级结构，确保头部能渲染“0 filters”并保持稳定
          filterStateManager.updateChartFilters(CHART_NAMES.PROJECT, {
            filters: { categories: [], brands: [], segments: [], extend_fields: {} },
            timeframe: { period: '' },
            metadata: { syncedFromProject: true, syncTimestamp: Date.now() }
          })
        }

        // 🆕 注入所有图表中“隐藏但需要生效”的默认值到全局过滤器状态（保持幂等，不覆盖已有用户选择）
        try {
          const charts = unifiedData.charts
          const toStringArray = (v: unknown): string[] => Array.isArray(v) ? (v.filter((x): x is string => typeof x === 'string')) : []
          const toPeriodString = (v: unknown): string => {
            if (typeof v === 'string') return v
            if (Array.isArray(v) && v.length > 0 && typeof v[0] === 'string') return v[0]
            return ''
          }
          const isEmptyArray = (v: unknown) => Array.isArray(v) && v.length === 0
          const isEmptyString = (v: unknown) => typeof v === 'string' && v.trim() === ''
          const hasNonEmptyArray = (v?: unknown[]) => Array.isArray(v) && v.length > 0

          Object.entries(charts).forEach(([chartName, cfg]) => {
            const current = filterStateManager.getChartFilters(chartName)
            const currentFilters = current?.filters || {}
            const pending: Partial<ChartFilterState> = { filters: {} }

            // categories（不可见且当前为空时注入默认值）
            if (cfg.filters.categories?.isVisible === false) {
              const defaults = toStringArray(cfg.filters.categories.values as unknown)
              if (defaults.length > 0 && !hasNonEmptyArray(currentFilters.categories)) {
                pending.filters!.categories = defaults
              }
            }

            // brands（不可见且当前为空时注入默认值）
            if (cfg.filters.brands?.isVisible === false) {
              const defaults = toStringArray(cfg.filters.brands.values as unknown)
              if (defaults.length > 0 && !hasNonEmptyArray(currentFilters.brands)) {
                pending.filters!.brands = defaults
              }
            }

            // product_segments → segments（不可见且当前为空时注入默认值）
            if (cfg.filters.product_segments?.isVisible === false) {
              const defaults = toStringArray(cfg.filters.product_segments.values as unknown)
              if (defaults.length > 0 && !hasNonEmptyArray(currentFilters.segments)) {
                pending.filters!.segments = defaults
              }
            }

            // asins → selected_asins（不可见且当前为空时注入默认值）
            if (cfg.filters.asins?.isVisible === false) {
              const defaults = toStringArray(cfg.filters.asins.values as unknown)
              if (defaults.length > 0 && !hasNonEmptyArray((current as any)?.selected_asins)) {
                pending.selected_asins = defaults
              }
            }

            // time_period → timeframe.period（不可见且当前为空时注入默认值）
            if (cfg.filters.time_period?.isVisible === false) {
              const period = toPeriodString(cfg.filters.time_period.values as unknown)
              const currentPeriod = current?.timeframe?.period
              if (period && (currentPeriod === undefined || currentPeriod === null || isEmptyString(currentPeriod))) {
                pending.timeframe = { ...(current?.timeframe || {}), period }
              }
            }

            // extend_fields（不可见时按字段注入：仅为缺失或空值的字段赋默认值，避免覆盖已有值）
            if (cfg.filters.extend_fields?.isVisible === false) {
              const defaults = cfg.filters.extend_fields.values
              if (defaults && typeof defaults === 'object' && !Array.isArray(defaults)) {
                const curObj = (currentFilters.extend_fields as Record<string, unknown> | undefined) || {}
                const merged: Record<string, unknown> = { ...curObj }
                let changed = false
                Object.entries(defaults as Record<string, unknown>).forEach(([k, v]) => {
                  const cv = curObj[k]
                  const emptyCur = cv === undefined || cv === null || isEmptyString(cv) || isEmptyArray(cv)
                  if (emptyCur && v !== undefined) {
                    merged[k] = v
                    changed = true
                  }
                })
                if (changed) {
                  pending.filters!.extend_fields = merged
                }
              }
            }

            const hasFiltersUpdate = pending.selected_asins !== undefined
              || (pending.timeframe && typeof pending.timeframe.period === 'string')
              || (pending.filters && Object.keys(pending.filters).length > 0)

            if (hasFiltersUpdate) {
              filterStateManager.updateChartFilters(chartName, pending)
              console.log(`🧩 [UNIFIED-FILTER] Seeded hidden defaults into state for ${chartName}:`, pending)
            }
          })
        } catch (e) {
          console.warn('⚠️ [UNIFIED-FILTER] Failed to seed hidden defaults into state:', e)
        }


        const successState: UnifiedFilterCacheState = {
          data: unifiedData,
          loading: false,
          error: null,
          lastUpdated: Date.now()
        }

        setCacheState(successState)
        unifiedFilterCacheStore.set(projectId, successState)
      } catch (error) {
        console.error('🚨 [UNIFIED-FILTER] API request failed for project:', projectId, error)

        const errorState: UnifiedFilterCacheState = {
          data: cached?.data || null,
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to load filter options',
          lastUpdated: cached?.lastUpdated || null
        }

        setCacheState(errorState)
        unifiedFilterCacheStore.set(projectId, errorState)
      } finally {
        // 清理加载Promise
        loadingPromises.delete(projectId)
      }
    })()

    // 存储Promise以防止并发请求
    loadingPromises.set(projectId, loadingPromise)

    // 等待请求完成
    await loadingPromise
  }, [])

  // 项目ID改变时重新加载
  useEffect(() => {
    if (projectId) {
      loadFilterData(projectId)
    }
    // 只依赖projectId，不依赖loadFilterData避免死循环
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  // 强制刷新数据
  const refreshData = useCallback(async () => {
    if (projectId) {
      await loadFilterData(projectId, true)
    }
    // 只依赖projectId，不依赖loadFilterData避免死循环
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  return {
    filterData: cacheState.data,
    isLoading: cacheState.loading,
    error: cacheState.error,
    refreshData,
    getChartConfig
  }
}