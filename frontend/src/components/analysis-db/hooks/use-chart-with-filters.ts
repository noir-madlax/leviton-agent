/**
 * 统一的图表过滤器 Hook
 * 封装了全局同步监听、过滤器就绪处理、状态管理等所有逻辑
 */

import { useState, useEffect, useCallback } from 'react'
import { filterStateManager } from '../stores'
import { CHART_NAMES } from '../constants'
import type { ProjectFilters } from '../types/filters'

interface UseChartWithFiltersOptions {
  // 是否在过滤器就绪时自动加载数据
  autoLoadOnReady?: boolean
  // 是否启用全局同步监听
  enableGlobalSync?: boolean
  // 初始过滤器数据
  initialFilters?: ProjectFilters
}

interface UseChartWithFiltersReturn {
  // 当前过滤器状态
  filters: ProjectFilters
  // 过滤器就绪状态
  filtersReady: boolean
  // 过滤器就绪处理函数（传给 FilterRenderer）
  handleFiltersReady: (isReady: boolean) => void
  // 过滤器变化处理函数（传给 FilterRenderer）
  handleFiltersChange: (newFilters: ProjectFilters) => void
  // 手动刷新数据
  refreshData: () => Promise<void>
  // 手动设置过滤器
  setFilters: (filters: ProjectFilters) => void
}

/**
 * 统一的图表过滤器 Hook
 * @param chartName 图表名称
 * @param refreshDataFn 数据刷新函数
 * @param projectId 项目ID
 * @param options 配置选项
 */
export function useChartWithFilters(
  chartName: string,
  refreshDataFn: (filters: ProjectFilters) => Promise<any>,
  projectId?: string,
  options: UseChartWithFiltersOptions = {}
): UseChartWithFiltersReturn {
  
  const {
    autoLoadOnReady = true,
    enableGlobalSync = true,
    initialFilters = {
      categories: [],
      asins: [],
      brands: [],
      segments: [],
      extend_fields: {},
      time_period: "" // 🔧 不设置前端默认值
    }
  } = options

  // 状态管理
  const [filters, setFilters] = useState<ProjectFilters>(initialFilters)
  const [filtersReady, setFiltersReady] = useState(false)

  // 数据刷新函数
  const refreshData = useCallback(async (filtersToUse?: ProjectFilters) => {
    const targetFilters = filtersToUse || filters
    try {
      console.log(`🚀 [USE-CHART-WITH-FILTERS] Refreshing data for ${chartName}:`, targetFilters)
      await refreshDataFn(targetFilters)
      console.log(`✅ [USE-CHART-WITH-FILTERS] Data refreshed successfully for ${chartName}`)
    } catch (error) {
      console.error(`❌ [USE-CHART-WITH-FILTERS] Failed to refresh data for ${chartName}:`, error)
      throw error
    }
  }, [filters, refreshDataFn, chartName])

  // 🆕 监听全局同步事件
  useEffect(() => {
    if (!enableGlobalSync) return

    const unsubscribe = filterStateManager.subscribe((event) => {
      if (event.type === 'GLOBAL_SYNC' && 
          event.affectedCharts.includes(chartName)) {
        
        console.log(`🌍 [USE-CHART-WITH-FILTERS] Received global sync for ${chartName}:`, event)
        
        // 转换过滤器格式
        const syncedFilters: ProjectFilters = {
          categories: event.projectFilters.filters.categories || [],
          asins: [],
          brands: event.projectFilters.filters.brands || [],
          segments: event.projectFilters.filters.segments || [],
          extend_fields: event.projectFilters.filters.extend_fields || {},
          time_period: event.projectFilters.timeframe?.period || "" // 🔧 不设置默认值
        }
        
        console.log(`🔄 [USE-CHART-WITH-FILTERS] Updating filters from global sync for ${chartName}:`, syncedFilters)
        
        // 更新本地过滤器状态
        setFilters(syncedFilters)
        
        // 自动刷新数据
        refreshData(syncedFilters).then(() => {
          console.log(`✅ [USE-CHART-WITH-FILTERS] Data refreshed after global sync for ${chartName}`)
        }).catch((error) => {
          console.error(`❌ [USE-CHART-WITH-FILTERS] Failed to refresh data after global sync for ${chartName}:`, error)
        })
      }
    })
    
    return unsubscribe
  }, [chartName, enableGlobalSync, refreshData])

  // 🆕 过滤器就绪状态变化处理
  const handleFiltersReady = useCallback(async (isReady: boolean) => {
    console.log(`🎯 [USE-CHART-WITH-FILTERS] Filters ready state changed for ${chartName}: ${isReady}`)
    setFiltersReady(isReady)
    
    if (isReady && autoLoadOnReady && projectId) {
      console.log(`🚀 [USE-CHART-WITH-FILTERS] Filters are ready, fetching initial data for ${chartName}`)
      try {
        await refreshData(filters)
        console.log(`✅ [USE-CHART-WITH-FILTERS] Initial data loaded successfully for ${chartName}`)
      } catch (error) {
        console.error(`❌ [USE-CHART-WITH-FILTERS] Failed to load initial data for ${chartName}:`, error)
      }
    }
  }, [chartName, autoLoadOnReady, projectId, filters, refreshData])

  // 🆕 过滤器变化处理
  const handleFiltersChange = useCallback(async (newFilters: ProjectFilters) => {
    console.log(`🔄 [USE-CHART-WITH-FILTERS] Filters changed for ${chartName}:`, newFilters)
    setFilters(newFilters)
    
    try {
      await refreshData(newFilters)
      console.log(`✅ [USE-CHART-WITH-FILTERS] Data refreshed after filter change for ${chartName}`)
    } catch (error) {
      console.error(`❌ [USE-CHART-WITH-FILTERS] Failed to refresh data after filter change for ${chartName}:`, error)
    }
  }, [chartName, refreshData])

  return {
    filters,
    filtersReady,
    handleFiltersReady,
    handleFiltersChange,
    refreshData,
    setFilters
  }
}

/**
 * 预设的图表 Hook - 市场份额分析
 */
export function useMarketShareFilters(
  refreshDataFn: (filters: ProjectFilters) => Promise<any>,
  projectId?: string,
  options?: UseChartWithFiltersOptions
) {
  return useChartWithFilters(
    CHART_NAMES.MARKET_SHARE_ANALYSIS,
    refreshDataFn,
    projectId,
    options
  )
}

/**
 * 预设的图表 Hook - 品牌分析
 */
export function useBrandAnalysisFilters(
  refreshDataFn: (filters: ProjectFilters) => Promise<any>,
  projectId?: string,
  options?: UseChartWithFiltersOptions
) {
  return useChartWithFilters(
    CHART_NAMES.BRAND_ANALYSIS,
    refreshDataFn,
    projectId,
    options
  )
}

/**
 * 预设的图表 Hook - 定价分析
 */
export function usePricingAnalysisFilters(
  refreshDataFn: (filters: ProjectFilters) => Promise<any>,
  projectId?: string,
  options?: UseChartWithFiltersOptions
) {
  return useChartWithFilters(
    CHART_NAMES.PRICE_ANALYSIS,
    refreshDataFn,
    projectId,
    options
  )
}


/**
 * 预设的图表 Hook - 销售趋势分析
 */
export function useSalesTrendFilters(
  refreshDataFn: (filters: ProjectFilters) => Promise<any>,
  projectId?: string,
  options?: UseChartWithFiltersOptions
) {
  return useChartWithFilters(
    CHART_NAMES.SALES_TREND_ANALYSIS,
    refreshDataFn,
    projectId,
    options
  )
}
