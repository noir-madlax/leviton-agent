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

// TAM Market Share 专用的数据刷新hook
export function useTAMDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'tam-market-share',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      
      return await databaseService.getTAMMarketShareData(projectId)
    }
  })
}

// Price Distribution 专用的数据刷新hook
export function usePriceDistributionDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'price-distribution',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      
      return await databaseService.getPriceDistributionData(projectId, filters)
    }
  })
}

// Price vs Revenue散点图专用的数据刷新hook
export function usePriceVsRevenueDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'price-vs-revenue',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      
      return await databaseService.getPriceVsRevenueData(projectId, filters)
    }
  })
}

// Brand Price Distribution专用的数据刷新hook
export function useBrandPriceDistributionDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'price-distribution-by-brands',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      
      return await databaseService.getBrandPriceDistributionData(projectId, filters)
    }
  })
}

// Brand Analysis 专用的数据刷新hook  
export function useBrandAnalysisDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'brand-analysis',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      
      return await databaseService.getBrandCategoryRevenueByProject(
        projectId,
        filters.categories.length > 0 ? filters.categories : undefined,
        filters.brands?.length ? filters.brands : undefined,
        filters.segments?.length ? filters.segments : undefined,
        filters.extend_fields
      )
    }
  })
}