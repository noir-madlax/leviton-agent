import { useState, useEffect, useCallback } from 'react'
import { databaseService } from '@/components/analysis-db/data/database-service'
import { FilterOptions } from '../types/filters'

// 数据缓存接口
interface UnifiedFilterCacheState {
  data: FilterOptions | null
  loading: boolean
  error: string | null
  lastUpdated: number | null
}

// 全局缓存存储
const unifiedFilterCacheStore = new Map<string, UnifiedFilterCacheState>()

interface UnifiedFilterDataReturn {
  filterData: FilterOptions | null
  isLoading: boolean
  error: string | null
  refreshData: () => Promise<void>
}

export function useUnifiedFilterData(projectId: string): UnifiedFilterDataReturn {
  const [cacheState, setCacheState] = useState<UnifiedFilterCacheState>(() => {
    // 从缓存中获取或初始化
    const cached = unifiedFilterCacheStore.get(projectId)
    if (cached) {
      return cached
    }
    
    return {
      data: null,
      loading: true,
      error: null,
      lastUpdated: null
    }
  })

  // 加载完整的筛选器选项数据
  const loadFilterData = useCallback(async (projectId: string, forceRefresh = false) => {
    const cached = unifiedFilterCacheStore.get(projectId)
    
    // 如果缓存存在且不强制刷新，且缓存时间不超过5分钟，则直接返回缓存
    if (cached && cached.data && !forceRefresh && cached.lastUpdated) {
      const cacheAge = Date.now() - cached.lastUpdated
      if (cacheAge < 5 * 60 * 1000) { // 5分钟缓存仍然有效
        setCacheState(cached)
        return
      }
    }

    // 更新加载状态
    const newState: UnifiedFilterCacheState = {
      data: cached?.data || null,
      loading: true,
      error: null,
      lastUpdated: cached?.lastUpdated || null
    }
    
    setCacheState(newState)
    unifiedFilterCacheStore.set(projectId, newState)

    try {
      // 沿用现有的project filter数据获取逻辑，但不使用筛选器以获取全量数据
      // 这样可以获得所有可能的枚举值，而不是过滤后的子集
      const [overview, segments] = await Promise.all([
        databaseService.getProjectOverview(projectId),
        databaseService.getProjectSegments(projectId)
      ])
      
      console.log('🔍 [UNIFIED-FILTER] Raw overview data received:', {
        distributions: overview.distributions,
        extend_fields_keys: overview.distributions ? Object.keys((overview.distributions as any).extend_fields || {}) : 'no distributions'
      })

      // 从overview.distributions中提取完整的filter数据，使用类型断言沿用现有逻辑
      const filterOptions: FilterOptions = {
        categories: overview.available_categories.flat_categories,
        hierarchical_categories: overview.available_categories.hierarchical_categories,
        // 从distributions中获取brands列表，使用类型断言
        brands: (overview.distributions as any)?.brands?.map((brand: any) => brand.name) || [],
        segments: segments,
        // 从distributions中获取extend_fields枚举值，使用类型断言
        extend_fields: extractExtendFieldOptions((overview.distributions as any)?.extend_fields)
      }

      console.log('🔍 [UNIFIED-FILTER] Loaded complete filter options:', {
        categories: filterOptions.categories?.length || 0,
        hierarchical_categories: filterOptions.hierarchical_categories?.length || 0,
        brands: filterOptions.brands?.length || 0,
        segments: filterOptions.segments?.length || 0,
        extend_fields: Object.keys(filterOptions.extend_fields || {}).length,
        project_id: projectId
      })

      const successState: UnifiedFilterCacheState = {
        data: filterOptions,
        loading: false,
        error: null,
        lastUpdated: Date.now()
      }

      setCacheState(successState)
      unifiedFilterCacheStore.set(projectId, successState)
    } catch (error) {
      const errorState: UnifiedFilterCacheState = {
        data: cached?.data || null,
        loading: false,
        error: error instanceof Error ? error.message : 'Failed to load filter options',
        lastUpdated: cached?.lastUpdated || null
      }

      setCacheState(errorState)
      unifiedFilterCacheStore.set(projectId, errorState)
    }
  }, [])

  // 项目ID改变时重新加载
  useEffect(() => {
    if (projectId) {
      loadFilterData(projectId)
    }
    // 只依赖projectId，不依赖loadFilterData避免死循环
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  // 强制刷新数据
  const refreshData = useCallback(async () => {
    if (projectId) {
      await loadFilterData(projectId, true)
    }
    // 只依赖projectId，不依赖loadFilterData避免死循环  
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId])

  return {
    filterData: cacheState.data,
    isLoading: cacheState.loading,
    error: cacheState.error,
    refreshData
  }
}

// 沿用现有逻辑提取extend_fields枚举值
function extractExtendFieldOptions(extendFieldsData: any): Record<string, string[]> {
  const result: Record<string, string[]> = {}
  
  if (extendFieldsData && typeof extendFieldsData === 'object') {
    Object.keys(extendFieldsData).forEach(fieldName => {
      const fieldData = extendFieldsData[fieldName]
      if (Array.isArray(fieldData)) {
        // 从分布数据中提取枚举值，去重和过滤
        const options = fieldData
          .map((item: any) => item.name || item)
          .filter((option: string) => option && option.trim() !== '')
          .filter((option: string, index: number, array: string[]) => array.indexOf(option) === index) // 去重
        
        result[fieldName] = options
        
        console.log(`🔍 [EXTRACT-EXTEND-FIELDS] Field: ${fieldName}`, {
          raw_data: fieldData,
          extracted_options: options
        })
      }
    })
  }
  
  console.log('🔍 [EXTRACT-EXTEND-FIELDS] Final result:', result)
  return result
}

// 预加载指定项目的筛选器数据
export function preloadUnifiedFilterData(projectId: string, existingOverview?: any): Promise<void> {
  return new Promise((resolve, reject) => {
    const loadOptions = async () => {
      try {
        // 检查缓存是否已经存在且有效
        const cached = unifiedFilterCacheStore.get(projectId)
        if (cached && cached.data && cached.lastUpdated) {
          const cacheAge = Date.now() - cached.lastUpdated
          if (cacheAge < 5 * 60 * 1000) { // 5分钟缓存仍然有效
            console.log(`Unified filter data already cached for project ${projectId}`)
            resolve()
            return
          }
        }

        console.log(`Preloading unified filter data for project ${projectId}`)

        // 沿用现有逻辑获取数据
        const [overview, segments] = await Promise.all([
          existingOverview || databaseService.getProjectOverview(projectId),
          databaseService.getProjectSegments(projectId)
        ])

        console.log('🔍 [PRELOAD-UNIFIED] Raw overview data received:', {
          distributions: overview.distributions,
          extend_fields_keys: overview.distributions ? Object.keys((overview.distributions as any).extend_fields || {}) : 'no distributions'
        })

        const filterOptions: FilterOptions = {
          categories: overview.available_categories.flat_categories,
          hierarchical_categories: overview.available_categories.hierarchical_categories,
          brands: (overview.distributions as any)?.brands?.map((brand: any) => brand.name) || [],
          segments: segments,
          extend_fields: extractExtendFieldOptions((overview.distributions as any)?.extend_fields)
        }

        console.log('🔍 [PRELOAD-UNIFIED] Preloaded unified filter data:', {
          categories: filterOptions.categories?.length || 0,
          hierarchical_categories: filterOptions.hierarchical_categories?.length || 0,
          brands: filterOptions.brands?.length || 0,
          segments: filterOptions.segments?.length || 0,
          extend_fields: Object.keys(filterOptions.extend_fields || {}).length,
          project_id: projectId
        })

        const cacheState: UnifiedFilterCacheState = {
          data: filterOptions,
          loading: false,
          error: null,
          lastUpdated: Date.now()
        }

        unifiedFilterCacheStore.set(projectId, cacheState)
        resolve()
      } catch (error) {
        console.error('Failed to preload unified filter data:', error)
        reject(error)
      }
    }

    loadOptions()
  })
} 