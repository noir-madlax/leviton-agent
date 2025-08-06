"use client"

import { useState, useCallback } from 'react'
import { ProjectFilters } from '../types/filters'

export interface ChartDataRefreshConfig<T> {
  chartId: string
  projectId: string
  initialData?: T
  refreshFunction: (projectId: string, filters: ProjectFilters) => Promise<T>
}

export function useChartDataRefresh<T>({
  chartId,
  projectId,
  initialData,
  refreshFunction
}: ChartDataRefreshConfig<T>) {
  const [data, setData] = useState<T | undefined>(initialData)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const refreshData = useCallback(async (filters: ProjectFilters) => {
    if (!projectId) {
      console.warn(`⚠️ Cannot refresh ${chartId} data: no project ID`)
      return
    }

    try {
      setLoading(true)
      setError(null)
      console.log(`🔄 Refreshing ${chartId} data with filters:`, filters)
      
      const newData = await refreshFunction(projectId, filters)
      setData(newData)
      
      console.log(`✅ ${chartId} data refreshed successfully`)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      console.error(`❌ Error refreshing ${chartId} data:`, err)
    } finally {
      setLoading(false)
    }
  }, [chartId, projectId, refreshFunction])

  return {
    data,
    loading,
    error,
    refreshData,
    setData
  }
}

