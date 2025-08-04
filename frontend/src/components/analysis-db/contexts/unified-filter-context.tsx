"use client"

import React, { createContext, useContext, ReactNode } from 'react'
import { UnifiedFilterData, ChartFilterConfiguration } from '../types/filters'
import { useUnifiedFilterData } from '../hooks/use-unified-filter-data'

// Context 数据类型
interface UnifiedFilterContextType {
  filterData: UnifiedFilterData | null
  isLoading: boolean
  error: string | null
  refreshData: () => Promise<void>
  // 🆕 便捷方法：获取特定图表的配置
  getChartConfig: (chartName: string) => ChartFilterConfiguration | null
}

// 创建Context
const UnifiedFilterContext = createContext<UnifiedFilterContextType | null>(null)

// Provider Props
interface UnifiedFilterProviderProps {
  children: ReactNode
  projectId: string
}

// Provider 组件
export function UnifiedFilterProvider({ children, projectId }: UnifiedFilterProviderProps) {
  // 🆕 使用新的 hook 获取数据
  const { filterData, isLoading, error, refreshData, getChartConfig } = useUnifiedFilterData(projectId)

  const contextValue: UnifiedFilterContextType = {
    filterData,
    isLoading,
    error,
    refreshData,
    getChartConfig
  }

  return (
    <UnifiedFilterContext.Provider value={contextValue}>
      {children}
    </UnifiedFilterContext.Provider>
  )
}

// 使用Context的Hook
export function useUnifiedFilter(): UnifiedFilterContextType {
  const context = useContext(UnifiedFilterContext)
  
  if (!context) {
    throw new Error('useUnifiedFilter must be used within a UnifiedFilterProvider')
  }
  
  return context
}