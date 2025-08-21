/**
 * 过滤器状态管理器
 * 统一管理所有图表的过滤器状态
 */

import {
  ChartFilterState,
  GlobalFilterState,
  FilterEvent,
  IFilterStateManager,
  DEFAULT_CHART_FILTER_STATE
} from './types'
import { CHART_NAMES } from '../constants'

class FilterStateManager implements IFilterStateManager {
  private state: GlobalFilterState = {}
  private subscribers: Array<(event: FilterEvent) => void> = []

  constructor() {
    console.log('🔧 [FILTER-STATE-MANAGER] Initialized')
  }

  /**
   * 获取指定图表的过滤器状态
   */
  getChartFilters(chartName: string): ChartFilterState | null {
    const filters = this.state[chartName] || null
    console.log(`🔍 [FILTER-STATE-MANAGER] Get filters for ${chartName}:`, filters)
    return filters
  }

  /**
   * 更新指定图表的过滤器状态
   */
  updateChartFilters(chartName: string, filters: Partial<ChartFilterState>): void {
    const oldState = this.state[chartName] || null
    const currentState = this.state[chartName] || { ...DEFAULT_CHART_FILTER_STATE }
    
    // 深度合并过滤器状态
    const newState: ChartFilterState = {
      filters: {
        ...currentState.filters,
        ...filters.filters
      },
      // 🆕 顶层字段：selected_asins 需要合并
      selected_asins: (filters.selected_asins !== undefined ? filters.selected_asins : currentState.selected_asins) as string[] | undefined,
      timeframe: {
        ...currentState.timeframe,
        ...filters.timeframe
      },
      metadata: {
        ...currentState.metadata,
        ...filters.metadata,
        lastUpdated: Date.now()
      }
    }

    this.state[chartName] = newState

    console.log(`🔧 [FILTER-STATE-MANAGER] Updated filters for ${chartName}:`, {
      oldState,
      newState,
      changes: filters
    })

    // 不进行本地持久化，保持会话级内存状态即可

    // 触发订阅者
    this.notifySubscribers({
      type: 'FILTER_UPDATE',
      chartName,
      oldState,
      newState,
      timestamp: Date.now()
    })
  }

  /**
   * 获取所有图表的过滤器状态
   */
  getAllFilters(): GlobalFilterState {
    console.log('🔍 [FILTER-STATE-MANAGER] Get all filters:', this.state)
    return { ...this.state }
  }

  /**
   * 重置指定图表的过滤器
   */
  resetChartFilters(chartName: string): void {
    const oldState = this.state[chartName] || null
    const newState = { ...DEFAULT_CHART_FILTER_STATE }
    
    this.state[chartName] = newState

    console.log(`🔄 [FILTER-STATE-MANAGER] Reset filters for ${chartName}`)

    // 触发订阅者
    this.notifySubscribers({
      type: 'FILTER_UPDATE',
      chartName,
      oldState,
      newState,
      timestamp: Date.now()
    })
  }

  /**
   * 批量更新多个图表的过滤器
   */
  batchUpdateFilters(updates: Record<string, Partial<ChartFilterState>>): void {
    console.log('🔧 [FILTER-STATE-MANAGER] Batch update filters:', updates)
    
    Object.entries(updates).forEach(([chartName, filters]) => {
      this.updateChartFilters(chartName, filters)
    })
  }

  /**
   * 订阅过滤器状态变化
   */
  subscribe(callback: (event: FilterEvent) => void): () => void {
    this.subscribers.push(callback)
    console.log(`🔔 [FILTER-STATE-MANAGER] New subscriber added, total: ${this.subscribers.length}`)
    
    // 返回取消订阅函数
    return () => {
      const index = this.subscribers.indexOf(callback)
      if (index > -1) {
        this.subscribers.splice(index, 1)
        console.log(`🔕 [FILTER-STATE-MANAGER] Subscriber removed, total: ${this.subscribers.length}`)
      }
    }
  }

  /**
   * 获取指定图表的特定过滤器
   */
  getSpecificFilter<T = any>(chartName: string, filterPath: string): T | null {
    const chartState = this.getChartFilters(chartName)
    if (!chartState) return null

    // 支持点号路径，如 "filters.categories" 或 "timeframe.period"
    const pathParts = filterPath.split('.')
    let current: any = chartState

    for (const part of pathParts) {
      if (current && typeof current === 'object' && part in current) {
        current = current[part]
      } else {
        return null
      }
    }

    console.log(`🔍 [FILTER-STATE-MANAGER] Get specific filter ${chartName}.${filterPath}:`, current)
    return current as T
  }

  /**
   * 更新指定图表的特定过滤器
   */
  updateSpecificFilter(chartName: string, filterPath: string, value: any): void {
    const pathParts = filterPath.split('.')
    
    if (pathParts.length === 1 && pathParts[0] === 'selected_asins') {
      // 🆕 更新与 filters 平级的 selected_asins
      this.updateChartFilters(chartName, {
        selected_asins: value
      })
    } else if (pathParts.length === 2 && pathParts[0] === 'filters') {
      // 更新 filters 下的字段
      const filterName = pathParts[1]
      this.updateChartFilters(chartName, {
        filters: {
          [filterName]: value
        }
      })
    } else if (pathParts.length === 2 && pathParts[0] === 'timeframe') {
      // 更新 timeframe 下的字段
      const timeframeName = pathParts[1]
      this.updateChartFilters(chartName, {
        timeframe: {
          [timeframeName]: value
        }
      })
    } else {
      console.warn(`🚨 [FILTER-STATE-MANAGER] Unsupported filter path: ${filterPath}`)
    }

    console.log(`🔧 [FILTER-STATE-MANAGER] Updated specific filter ${chartName}.${filterPath}:`, value)
  }

  /**
   * 通知所有订阅者
   */
  private notifySubscribers(event: FilterEvent): void {
    this.subscribers.forEach(callback => {
      try {
        callback(event)
      } catch (error) {
        console.error('🚨 [FILTER-STATE-MANAGER] Error in subscriber callback:', error)
      }
    })
  }

  /**
   * 获取状态快照（用于调试）
   */
  getStateSnapshot(): { state: GlobalFilterState; subscriberCount: number } {
    return {
      state: { ...this.state },
      subscriberCount: this.subscribers.length
    }
  }

  /**
   * 清空所有状态（用于测试或重置）
   */
  clearAllState(): void {
    this.state = {}
    console.log('🧹 [FILTER-STATE-MANAGER] All state cleared')
  }

  /**
   * 🆕 项目级过滤器同步到所有图表
   */
  syncProjectFiltersToAllCharts(projectFilters: ChartFilterState): void {
    // 🔄 获取所有已注册的图表（除了 project 本身）
    const allRegisteredCharts = Object.keys(this.state).filter(chartName => chartName !== CHART_NAMES.PROJECT)

    console.log('🌍 [FILTER-STATE-MANAGER] Syncing project filters to all charts:', {
      projectFilters,
      allRegisteredCharts,
      totalCharts: allRegisteredCharts.length
    })

    // 直接覆盖所有目标图表的过滤器数据
    allRegisteredCharts.forEach(chartName => {
      this.state[chartName] = {
        ...projectFilters,  // 🎯 直接覆盖，不合并
        metadata: {
          ...projectFilters.metadata,
          syncedFromProject: true,
          syncTimestamp: Date.now()
        }
      }

      console.log(`🔄 [FILTER-STATE-MANAGER] Synced project filters to ${chartName}`)
    })

    // 触发全局同步事件
    this.notifyGlobalSync(projectFilters, allRegisteredCharts)

    // 不进行本地持久化
  }

  /**
   * 🆕 全局同步事件通知
   */
  private notifyGlobalSync(projectFilters: ChartFilterState, affectedCharts: string[]): void {
    const globalSyncEvent = {
      type: 'GLOBAL_SYNC' as const,
      sourceChart: 'project' as const,
      projectFilters,
      affectedCharts,
      timestamp: Date.now()
    }

    console.log('🌍 [FILTER-STATE-MANAGER] Triggering global sync event:', globalSyncEvent)

    // 通知所有订阅者发生了全局同步
    this.subscribers.forEach(callback => {
      try {
        callback(globalSyncEvent)
      } catch (error) {
        console.error('🚨 [FILTER-STATE-MANAGER] Error in global sync callback:', error)
      }
    })
  }
}

// 创建全局单例实例
export const filterStateManager = new FilterStateManager()

// 导出类型和实例
export { FilterStateManager }
export type { ChartFilterState, GlobalFilterState, FilterEvent }
