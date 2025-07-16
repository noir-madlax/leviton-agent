"use client"

import { useState, useEffect, useCallback } from 'react'
import { FilterOptions } from '../types/filters'
import { databaseService } from '../data/database-service'

interface FilterCacheState {
  data: FilterOptions | null
  loading: boolean
  error: string | null
  lastUpdated: number | null
}

interface FilterCacheHookReturn {
  filterOptions: FilterOptions | null
  isLoading: boolean
  error: string | null
  refreshCache: () => Promise<void>
}

// 全局缓存存储
const filterCacheStore = new Map<string, FilterCacheState>()

export function useFilterCache(projectId: string): FilterCacheHookReturn {
  const [cacheState, setCacheState] = useState<FilterCacheState>(() => {
    // 从缓存中获取或初始化
    const cached = filterCacheStore.get(projectId)
    if (cached) {
      return cached
    }
    
    // 如果缓存不存在，设置初始加载状态
    return {
      data: null,
      loading: true, // 设置为true，因为即将开始加载
      error: null,
      lastUpdated: null
    }
  })

  // 加载筛选器选项数据
  const loadFilterOptions = useCallback(async (projectId: string, forceRefresh = false) => {
    const cached = filterCacheStore.get(projectId)
    
    // 如果缓存存在且不强制刷新，且缓存时间不超过5分钟，则直接返回缓存
    if (cached && cached.data && !forceRefresh && cached.lastUpdated) {
      const cacheAge = Date.now() - cached.lastUpdated
      if (cacheAge < 5 * 60 * 1000) { // 5分钟缓存仍然有效
        setCacheState(cached)
        return
      }
    }

    // 更新加载状态
    const newState: FilterCacheState = {
      data: cached?.data || null,
      loading: true,
      error: null,
      lastUpdated: cached?.lastUpdated || null
    }
    
    setCacheState(newState)
    filterCacheStore.set(projectId, newState)

    try {
      // 并行加载所有筛选器选项
      const [overview, segments] = await Promise.all([
        databaseService.getProjectOverview(projectId),
        databaseService.getProjectSegments(projectId)
      ])

      const filterOptions: FilterOptions = {
        categories: overview.available_categories.flat_categories,
        hierarchical_categories: overview.available_categories.hierarchical_categories,
        brands: [], // 从后端获取的品牌列表
        segments: segments,
        extend_fields: {} // 这个可以根据需要扩展
      }

      console.log('🔍 [FILTER-CACHE] Loaded filter options:', {
        flat_categories: filterOptions.categories?.length || 0,
        hierarchical_categories: filterOptions.hierarchical_categories?.length || 0,
        hierarchical_with_children: filterOptions.hierarchical_categories?.filter(g => g.children.length > 0).length || 0,
        project_id: projectId
      })

      const successState: FilterCacheState = {
        data: filterOptions,
        loading: false,
        error: null,
        lastUpdated: Date.now()
      }

      setCacheState(successState)
      filterCacheStore.set(projectId, successState)
    } catch (error) {
      const errorState: FilterCacheState = {
        data: cached?.data || null,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load filter options',
        lastUpdated: cached?.lastUpdated || null
      }

      setCacheState(errorState)
      filterCacheStore.set(projectId, errorState)
    }
  }, [])

  // 项目ID改变时重新加载
  useEffect(() => {
    if (projectId) {
      loadFilterOptions(projectId)
    }
  }, [projectId, loadFilterOptions])

  // 强制刷新缓存
  const refreshCache = useCallback(async () => {
    if (projectId) {
      await loadFilterOptions(projectId, true)
    }
  }, [projectId, loadFilterOptions])

  return {
    filterOptions: cacheState.data,
    isLoading: cacheState.loading,
    error: cacheState.error,
    refreshCache
  }
}

// 预加载指定项目的筛选器数据
export function preloadFilterOptions(projectId: string): Promise<void> {
  return new Promise((resolve, reject) => {
    const loadOptions = async () => {
      try {
        // 检查缓存是否已经存在且有效
        const cached = filterCacheStore.get(projectId)
        if (cached && cached.data && cached.lastUpdated) {
          const cacheAge = Date.now() - cached.lastUpdated
          if (cacheAge < 5 * 60 * 1000) { // 5分钟缓存仍然有效
            console.log(`Filter options already cached for project ${projectId}`)
            resolve()
            return
          }
        }

        console.log(`Preloading filter options for project ${projectId}`)
        
        const [overview, segments] = await Promise.all([
          databaseService.getProjectOverview(projectId),
          databaseService.getProjectSegments(projectId)
        ])

        const filterOptions: FilterOptions = {
          categories: overview.available_categories.flat_categories,
          hierarchical_categories: overview.available_categories.hierarchical_categories,
          brands: [], // 从后端获取的品牌列表
          segments: segments,
          extend_fields: {}
        }

        console.log('🔍 [PRELOAD-CACHE] Preloaded filter options:', {
          flat_categories: filterOptions.categories?.length || 0,
          hierarchical_categories: filterOptions.hierarchical_categories?.length || 0,
          hierarchical_with_children: filterOptions.hierarchical_categories?.filter(g => g.children.length > 0).length || 0,
          project_id: projectId
        })

        const cacheState: FilterCacheState = {
          data: filterOptions,
          loading: false,
          error: null,
          lastUpdated: Date.now()
        }

        filterCacheStore.set(projectId, cacheState)
        console.log(`Filter options successfully preloaded for project ${projectId}`)
        resolve()
      } catch (error) {
        console.error(`Failed to preload filter options for project ${projectId}:`, error)
        
        const errorState: FilterCacheState = {
          data: null,
          loading: false,
          error: error instanceof Error ? error.message : 'Failed to preload filter options',
          lastUpdated: null
        }

        filterCacheStore.set(projectId, errorState)
        
        // 即使预加载失败，我们也resolve，让组件能够继续工作
        // 组件会通过useFilterCache重新尝试加载
        resolve()
      }
    }

    loadOptions()
  })
}

// 清除缓存
export function clearFilterCache(projectId?: string) {
  if (projectId) {
    filterCacheStore.delete(projectId)
  } else {
    filterCacheStore.clear()
  }
} 