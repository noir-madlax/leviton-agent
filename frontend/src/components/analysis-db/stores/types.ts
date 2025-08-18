/**
 * 过滤器状态管理相关类型定义
 */

// 单个图表的过滤器状态
export interface ChartFilterState {
  filters: {
    categories?: string[]
    brands?: string[]
    segments?: string[]
    extend_fields?: Record<string, any>
  }
  // 🆕 选中的ASIN（与 filters 平级，供 asin-filter 使用）
  selected_asins?: string[]
  timeframe?: {
    period?: string
  }
  // 预留扩展字段
  metadata?: {
    lastUpdated?: number
    appliedAt?: number
    version?: string
    // 🆕 全局同步相关字段
    syncedFromProject?: boolean
    syncTimestamp?: number
  }
}

// 全局过滤器状态存储
export interface GlobalFilterState {
  [chartName: string]: ChartFilterState
}

// 过滤器更新事件
export interface FilterUpdateEvent {
  type: 'FILTER_UPDATE'
  chartName: string
  oldState: ChartFilterState | null
  newState: ChartFilterState
  timestamp: number
}

// 🆕 全局同步事件
export interface GlobalSyncEvent {
  type: 'GLOBAL_SYNC'
  sourceChart: 'project'
  projectFilters: ChartFilterState
  affectedCharts: string[]
  timestamp: number
}

// 🆕 联合事件类型
export type FilterEvent = FilterUpdateEvent | GlobalSyncEvent

// 过滤器状态管理器接口
export interface IFilterStateManager {
  // 获取指定图表的过滤器状态
  getChartFilters(chartName: string): ChartFilterState | null
  
  // 更新指定图表的过滤器状态
  updateChartFilters(chartName: string, filters: Partial<ChartFilterState>): void
  
  // 获取所有图表的过滤器状态
  getAllFilters(): GlobalFilterState
  
  // 重置指定图表的过滤器
  resetChartFilters(chartName: string): void
  
  // 批量更新多个图表的过滤器
  batchUpdateFilters(updates: Record<string, Partial<ChartFilterState>>): void
  
  // 订阅过滤器状态变化
  subscribe(callback: (event: FilterEvent) => void): () => void
  
  // 获取指定图表的特定过滤器
  getSpecificFilter<T = any>(chartName: string, filterPath: string): T | null
  
  // 更新指定图表的特定过滤器
  updateSpecificFilter(chartName: string, filterPath: string, value: any): void
}

// 默认的图表过滤器状态
export const DEFAULT_CHART_FILTER_STATE: ChartFilterState = {
  filters: {
    categories: [],
    brands: [],
    segments: [],
    extend_fields: {}
  },
  selected_asins: [],
  timeframe: {
    period: "" // 🔧 移除硬编码默认值，完全依赖后端
  },
  metadata: {
    lastUpdated: Date.now(),
    appliedAt: 0,
    version: "1.0.0"
  }
}

// 图表名称类型从常量文件导入
import type { ChartName } from '../constants'
export type { ChartName }
