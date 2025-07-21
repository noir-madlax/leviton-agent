import { useState, useCallback, useMemo, useEffect } from 'react'
import { ProjectFilters, DEFAULT_FILTERS } from '../types/filters'
import { FilterMerger } from '../lib/filter-merger'
import { FilterSynchronizer } from '../lib/filter-synchronizer'

interface FilterState {
  projectFilters: ProjectFilters
  chartFilters: Map<string, ProjectFilters>
  finalFilters: Map<string, ProjectFilters>
}

/**
 * 筛选器状态管理hook
 * 管理project级和chart级筛选器的状态和同步
 */
export function useFilterState(projectId: string, initialProjectFilters?: ProjectFilters) {
  const [state, setState] = useState<FilterState>({
    projectFilters: initialProjectFilters || { ...DEFAULT_FILTERS },
    chartFilters: new Map(),
    finalFilters: new Map()
  })

  const filterMerger = useMemo(() => new FilterMerger(), [])
  const filterSynchronizer = useMemo(() => new FilterSynchronizer(), [])

  // 同步外部传入的项目筛选器
  useEffect(() => {
    if (initialProjectFilters) {
      setState(prevState => {
        const newState = { ...prevState }
        const oldProjectFilters = newState.projectFilters
        newState.projectFilters = initialProjectFilters

              // 创建新的Map引用以确保React能检测到变化
      const newChartFilters = new Map(newState.chartFilters)
      const newFinalFilters = new Map()

      // 同步到所有chart
      prevState.chartFilters.forEach((chartFilters, chartId) => {
        const syncedChartFilters = filterSynchronizer.syncProjectToChart(
          chartFilters, 
          oldProjectFilters, 
          initialProjectFilters
        )
        newChartFilters.set(chartId, syncedChartFilters)
      })

      // 重新计算所有final filters
      newChartFilters.forEach((chartFilters, chartId) => {
        const finalFilters = filterMerger.mergeFilters(initialProjectFilters, chartFilters)
        newFinalFilters.set(chartId, finalFilters)
      })

      return {
        ...newState,
        chartFilters: newChartFilters,
        finalFilters: newFinalFilters
      }
      })
    }
  }, [initialProjectFilters, filterMerger, filterSynchronizer])

  /**
   * 更新project筛选器
   * @param newFilters 新的project筛选器
   */
  const updateProjectFilters = useCallback((newFilters: ProjectFilters) => {
    console.log(`🔄 [useFilterState] Updating project filters`, newFilters)
    
    setState(prevState => {
      const oldProjectFilters = prevState.projectFilters
      
      // 创建新的Map引用以确保React能检测到变化
      const newChartFilters = new Map(prevState.chartFilters)
      const newFinalFilters = new Map()

      // 同步到所有chart
      prevState.chartFilters.forEach((chartFilters, chartId) => {
        const syncedChartFilters = filterSynchronizer.syncProjectToChart(
          chartFilters, 
          oldProjectFilters, 
          newFilters
        )
        newChartFilters.set(chartId, syncedChartFilters)
      })

      // 重新计算所有final filters
      newChartFilters.forEach((chartFilters, chartId) => {
        const finalFilters = filterMerger.mergeFilters(newFilters, chartFilters)
        newFinalFilters.set(chartId, finalFilters)
      })

      console.log(`✅ [useFilterState] Updated project filters, affected ${newFinalFilters.size} charts`)

      return {
        ...prevState,
        projectFilters: newFilters,
        chartFilters: newChartFilters,
        finalFilters: newFinalFilters
      }
    })
  }, [filterMerger, filterSynchronizer])

  /**
   * 更新chart筛选器
   * @param chartId 图表ID
   * @param newFilters 新的chart筛选器
   */
  const updateChartFilters = useCallback((chartId: string, newFilters: ProjectFilters) => {
    console.log(`🔄 [useFilterState] Updating chart filters for ${chartId}`, newFilters)
    
    setState(prevState => {
      // 创建新的Map引用以确保React能检测到变化
      const newChartFilters = new Map(prevState.chartFilters)
      const newFinalFilters = new Map(prevState.finalFilters)
      
      newChartFilters.set(chartId, newFilters)
      
      // 重新计算该chart的final filters
      const finalFilters = filterMerger.mergeFilters(prevState.projectFilters, newFilters)
      newFinalFilters.set(chartId, finalFilters)
      
      console.log(`✅ [useFilterState] Updated final filters for ${chartId}:`, finalFilters)
      
      return {
        ...prevState,
        chartFilters: newChartFilters,
        finalFilters: newFinalFilters
      }
    })
  }, [filterMerger])

  /**
   * 初始化chart筛选器
   * @param chartId 图表ID
   */
  const initializeChartFilter = useCallback((chartId: string) => {
    setState(prevState => {
      if (prevState.chartFilters.has(chartId)) return prevState
      
      console.log(`🔄 [useFilterState] Initializing chart filter for ${chartId}`)
      
      // 创建新的Map引用以确保React能检测到变化
      const newChartFilters = new Map(prevState.chartFilters)
      const newFinalFilters = new Map(prevState.finalFilters)
      
      // 新chart默认继承project筛选器
      const initialChartFilters = { ...prevState.projectFilters }
      newChartFilters.set(chartId, initialChartFilters)
      
      // 计算final filters
      const finalFilters = filterMerger.mergeFilters(prevState.projectFilters, initialChartFilters)
      newFinalFilters.set(chartId, finalFilters)
      
      console.log(`✅ [useFilterState] Initialized chart filter for ${chartId}:`, finalFilters)
      
      return {
        ...prevState,
        chartFilters: newChartFilters,
        finalFilters: newFinalFilters
      }
    })
  }, [filterMerger])

  /**
   * 获取chart筛选器
   * @param chartId 图表ID
   * @returns chart筛选器
   */
  const getChartFilters = useCallback((chartId: string): ProjectFilters | undefined => {
    return state.chartFilters.get(chartId)
  }, [state.chartFilters])

  /**
   * 获取最终筛选器
   * @param chartId 图表ID
   * @returns 最终筛选器
   */
  const getFinalFilters = useCallback((chartId: string): ProjectFilters | undefined => {
    return state.finalFilters.get(chartId)
  }, [state.finalFilters])

  return {
    projectFilters: state.projectFilters,
    getChartFilters,
    getFinalFilters,
    updateProjectFilters,
    updateChartFilters,
    initializeChartFilter
  }
} 