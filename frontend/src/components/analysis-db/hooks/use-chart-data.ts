"use client"

import { useState, useEffect, useCallback, useMemo } from 'react'
import { ProjectFilters } from '../types/filters'

export interface UseChartDataOptions {
  enabled?: boolean
  refetchOnFilterChange?: boolean
  cacheTime?: number
}

interface ChartDataCacheItem {
  data: any
  timestamp: number
  filters: string
}

// 参考 use-filter-cache.ts 的缓存策略
const chartDataCache = new Map<string, ChartDataCacheItem>()

function getCacheKey(chartId: string, projectId: string, filters: ProjectFilters): string {
  // 安全的序列化，避免循环引用和undefined值
  const safeFilters = {
    categories: filters?.categories || [],
    brands: filters?.brands || [],
    segments: filters?.segments || [],
    extend_fields: filters?.extend_fields || {},
    asins: filters?.asins || []
  }
  return `${chartId}-${projectId}-${JSON.stringify(safeFilters)}`
}

export function useChartData<T = any>(
  chartId: string, 
  projectId: string, 
  filters: ProjectFilters,
  options: UseChartDataOptions = { enabled: true, refetchOnFilterChange: true }
) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 参考现有的 databaseService 调用方式
  const fetchData = useCallback(async () => {
    if (!projectId || !chartId || !options.enabled) return
    
    // 确保filters是有效的
    if (!filters) {
      console.warn(`useChartData: filters is null/undefined for chart ${chartId}`)
      return
    }
  
    const cacheKey = getCacheKey(chartId, projectId, filters)
  
    // 检查缓存（参考 use-filter-cache.ts）
    const cached = chartDataCache.get(cacheKey)
    if (cached && Date.now() - cached.timestamp < (options.cacheTime || 5 * 60 * 1000)) {
      console.log(`📋 [useChartData] Using cached data for ${chartId}`)
      setData(cached.data)
      return
    }
  
    setLoading(true)
    setError(null)
    
    console.log(`🚀 [useChartData] Fetching data for ${chartId}`, {
      projectId,
      filters,
      requestBody: {
        categories: filters.categories || [],
        brands: filters.brands || [],
        segments: filters.segments || [],
        extend_fields: filters.extend_fields || {},
        asins: filters.asins || []
      }
    })
  
    try {  
      // 直接调用后端chart API
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      
      // 安全的request body
      const requestBody = {
        categories: filters.categories || [],
        brands: filters.brands || [],
        segments: filters.segments || [],
        extend_fields: filters.extend_fields || {},
        asins: filters.asins || []
      }
      
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/projects/${projectId}/charts/${chartId}/data`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`API call failed: ${response.status} - ${response.statusText}. Response: ${errorText}`)
      }

      const result = await response.json()
      
      // 验证返回的数据
      if (!result) {
        throw new Error(`API returned null/undefined data for chart ${chartId}`)
      }
    
      // 缓存结果
      chartDataCache.set(cacheKey, {
        data: result,
        timestamp: Date.now(),
        filters: JSON.stringify(filters)
      })
    
      console.log(`✅ [useChartData] Successfully fetched data for ${chartId}`, {
        dataType: typeof result,
        dataKeys: result && typeof result === 'object' ? Object.keys(result) : 'not an object'
      })
    
      setData(result as T)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      console.error(`Error fetching data for chart ${chartId}:`, err)
      // 确保在错误时数据为null，不是undefined
      setData(null)
    } finally {
      setLoading(false)
    }
  }, [chartId, projectId, filters, options.enabled, options.cacheTime])

  // 防抖处理（参考现有的防抖逻辑）
  const debouncedFetchData = useMemo(() => {
    const debounce = (func: Function, wait: number) => {
      let timeout: NodeJS.Timeout
      return (...args: any[]) => {
        clearTimeout(timeout)
        timeout = setTimeout(() => func.apply(null, args), wait)
      }
    }
    console.log(`⚡ [useChartData] Creating debounced fetch function for ${chartId}`)
    return debounce(fetchData, 300)
  }, [fetchData, chartId])

  useEffect(() => {
    console.log(`🔄 [useChartData] Filter change detected for ${chartId}`, {
      filters,
      enabled: options.enabled,
      refetchOnFilterChange: options.refetchOnFilterChange
    })
    
    if (options.refetchOnFilterChange !== false) {
      debouncedFetchData()
    }
  }, [debouncedFetchData, options.refetchOnFilterChange])

  // 额外的debug useEffect来监听filters变化
  useEffect(() => {
    console.log(`📊 [useChartData] Filters updated for ${chartId}:`, {
      categories: filters?.categories || [],
      brands: filters?.brands || [],
      segments: filters?.segments || [],
      extend_fields: filters?.extend_fields || {},
      asins: filters?.asins || [],
      timestamp: new Date().toLocaleTimeString()
    })
    
    // 如果筛选器变化且enabled，应该触发重新获取数据
    if (options.enabled) {
      console.log(`🚀 [useChartData] Filters changed, should trigger data refetch for ${chartId}`)
    }
  }, [chartId, filters, options.enabled])

  return { data, loading, error, refetch: fetchData }
} 