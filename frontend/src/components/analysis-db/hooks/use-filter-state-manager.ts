/**
 * React Hook for Filter State Manager
 * 提供响应式的过滤器状态管理
 */

import { useState, useEffect, useCallback, useMemo } from 'react'
import { filterStateManager } from '../stores'
import type { ChartFilterState, FilterUpdateEvent } from '../stores'

interface UseFilterStateManagerReturn {
  // 获取指定图表的过滤器状态
  getChartFilters: (chartName: string) => ChartFilterState | null
  
  // 更新指定图表的过滤器状态
  updateChartFilters: (chartName: string, filters: Partial<ChartFilterState>) => void
  
  // 重置指定图表的过滤器
  resetChartFilters: (chartName: string) => void
  
  // 获取指定图表的特定过滤器
  getSpecificFilter: <T = any>(chartName: string, filterPath: string) => T | null
  
  // 更新指定图表的特定过滤器
  updateSpecificFilter: (chartName: string, filterPath: string, value: any) => void
  
  // 获取所有过滤器状态
  getAllFilters: () => Record<string, ChartFilterState>
  
  // 状态快照（用于调试）
  stateSnapshot: { state: Record<string, ChartFilterState>; subscriberCount: number }
}

/**
 * 通用的过滤器状态管理 Hook
 */
export function useFilterStateManager(): UseFilterStateManagerReturn {
  const [, forceUpdate] = useState({})

  // 强制组件重新渲染
  const triggerUpdate = useCallback(() => {
    forceUpdate({})
  }, [])

  // 订阅状态变化
  useEffect(() => {
    const unsubscribe = filterStateManager.subscribe((event: FilterUpdateEvent) => {
      console.log('🔔 [USE-FILTER-STATE-MANAGER] State changed:', event)
      triggerUpdate()
    })

    return unsubscribe
  }, [triggerUpdate])

  // 包装 filterStateManager 的方法
  const getChartFilters = useCallback((chartName: string) => {
    return filterStateManager.getChartFilters(chartName)
  }, [])

  const updateChartFilters = useCallback((chartName: string, filters: Partial<ChartFilterState>) => {
    filterStateManager.updateChartFilters(chartName, filters)
  }, [])

  const resetChartFilters = useCallback((chartName: string) => {
    filterStateManager.resetChartFilters(chartName)
  }, [])

  const getSpecificFilter = useCallback(<T = any>(chartName: string, filterPath: string): T | null => {
    return filterStateManager.getSpecificFilter<T>(chartName, filterPath)
  }, [])

  const updateSpecificFilter = useCallback((chartName: string, filterPath: string, value: any) => {
    filterStateManager.updateSpecificFilter(chartName, filterPath, value)
  }, [])

  const getAllFilters = useCallback(() => {
    return filterStateManager.getAllFilters()
  }, [])

  // 获取状态快照
  const stateSnapshot = useMemo(() => {
    return filterStateManager.getStateSnapshot()
  }, [triggerUpdate])

  return {
    getChartFilters,
    updateChartFilters,
    resetChartFilters,
    getSpecificFilter,
    updateSpecificFilter,
    getAllFilters,
    stateSnapshot
  }
}

/**
 * 针对特定图表的过滤器状态 Hook
 */
interface UseChartFiltersReturn {
  // 当前图表的过滤器状态
  filters: ChartFilterState | null
  
  // 更新过滤器状态
  updateFilters: (filters: Partial<ChartFilterState>) => void
  
  // 重置过滤器
  resetFilters: () => void
  
  // 获取特定过滤器
  getFilter: <T = any>(filterPath: string) => T | null
  
  // 更新特定过滤器
  updateFilter: (filterPath: string, value: any) => void
  
  // 便捷方法：更新 categories
  updateCategories: (categories: string[]) => void
  
  // 便捷方法：更新 brands
  updateBrands: (brands: string[]) => void
  
  // 便捷方法：更新 segments
  updateSegments: (segments: string[]) => void
  
  // 便捷方法：更新 extend_fields
  updateExtendFields: (extendFields: Record<string, any>) => void
  
  // 便捷方法：更新 timeframe
  updateTimeframe: (timeframe: { period?: string; start_date?: string; end_date?: string }) => void
}

export function useChartFilters(chartName: string): UseChartFiltersReturn {
  const { 
    getChartFilters, 
    updateChartFilters, 
    resetChartFilters, 
    getSpecificFilter, 
    updateSpecificFilter 
  } = useFilterStateManager()

  const filters = getChartFilters(chartName)

  const updateFilters = useCallback((newFilters: Partial<ChartFilterState>) => {
    updateChartFilters(chartName, newFilters)
  }, [chartName, updateChartFilters])

  const resetFilters = useCallback(() => {
    resetChartFilters(chartName)
  }, [chartName, resetChartFilters])

  const getFilter = useCallback(<T = any>(filterPath: string): T | null => {
    return getSpecificFilter<T>(chartName, filterPath)
  }, [chartName, getSpecificFilter])

  const updateFilter = useCallback((filterPath: string, value: any) => {
    updateSpecificFilter(chartName, filterPath, value)
  }, [chartName, updateSpecificFilter])

  // 便捷方法
  const updateCategories = useCallback((categories: string[]) => {
    updateFilter('filters.categories', categories)
  }, [updateFilter])

  const updateBrands = useCallback((brands: string[]) => {
    updateFilter('filters.brands', brands)
  }, [updateFilter])

  const updateSegments = useCallback((segments: string[]) => {
    updateFilter('filters.segments', segments)
  }, [updateFilter])

  const updateExtendFields = useCallback((extendFields: Record<string, any>) => {
    updateFilter('filters.extend_fields', extendFields)
  }, [updateFilter])

  const updateTimeframe = useCallback((timeframe: { period?: string; start_date?: string; end_date?: string }) => {
    updateFilter('timeframe', timeframe)
  }, [updateFilter])

  return {
    filters,
    updateFilters,
    resetFilters,
    getFilter,
    updateFilter,
    updateCategories,
    updateBrands,
    updateSegments,
    updateExtendFields,
    updateTimeframe
  }
}
