/**
 * 新的 Dashboard API Hook
 * 
 * 这个 Hook 提供了统一的 Dashboard API 调用接口
 */

import { useState, useCallback } from 'react'

// TypeScript 接口定义
interface DashboardFilters {
  categories?: string[];
  brands?: string[];
  segments?: string[];
  extend_fields?: Record<string, any>;
}

interface DashboardRequest {
  project_id: string;
  filters?: DashboardFilters;
  options?: {
    limit?: number;
    offset?: number;
    sort_by?: string;
    sort_order?: 'asc' | 'desc';
  };
}

interface PackagePreferenceRequest extends DashboardRequest {
  metric_type?: string;
}

interface CompetitorAnalysisRequest extends DashboardRequest {
  selected_asins?: string[];
}

// 通用的 Dashboard API 调用函数
async function callDashboardAPI(endpoint: string, request: DashboardRequest | PackagePreferenceRequest | CompetitorAnalysisRequest) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  
  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  })

  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`)
  }

  return await response.json()
}

// Dashboard API Hook
export function useDashboardAPI() {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const callAPI = useCallback(async (endpoint: string, request: DashboardRequest | PackagePreferenceRequest | CompetitorAnalysisRequest) => {
    setLoading(true)
    setError(null)
    
    try {
      const result = await callDashboardAPI(endpoint, request)
      return result
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error'
      setError(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }, [])

  // 具体的 API 方法
  const brandAnalysis = useCallback(async (projectId: string, filters?: DashboardFilters) => {
    return callAPI('brand-analysis', { project_id: projectId, filters })
  }, [callAPI])

  const productAnalysis = useCallback(async (projectId: string, filters?: DashboardFilters) => {
    return callAPI('product-analysis', { project_id: projectId, filters })
  }, [callAPI])

  const pricingAnalysis = useCallback(async (projectId: string, filters?: DashboardFilters) => {
    return callAPI('pricing-analysis', { project_id: projectId, filters })
  }, [callAPI])

  const marketInsights = useCallback(async (projectId: string, filters?: DashboardFilters) => {
    return callAPI('market-insights', { project_id: projectId, filters })
  }, [callAPI])

  const packagePreference = useCallback(async (projectId: string, filters?: DashboardFilters, metricType?: string) => {
    const request: PackagePreferenceRequest = { 
      project_id: projectId, 
      filters,
      ...(metricType && { metric_type: metricType })
    }
    return callAPI('package-preference', request)
  }, [callAPI])

  const reviewInsights = useCallback(async (projectId: string, filters?: DashboardFilters) => {
    return callAPI('review-insights', { project_id: projectId, filters })
  }, [callAPI])

  const competitorAnalysis = useCallback(async (projectId: string, filters?: DashboardFilters, selectedAsins?: string[]) => {
    const request: CompetitorAnalysisRequest = { 
      project_id: projectId, 
      filters,
      ...(selectedAsins && { selected_asins: selectedAsins })
    }
    return callAPI('competitor-analysis', request)
  }, [callAPI])

  const allReviewData = useCallback(async (projectId: string, filters?: DashboardFilters) => {
    return callAPI('all-review-data', { project_id: projectId, filters })
  }, [callAPI])

  const projectOverview = useCallback(async (projectId: string, filters?: DashboardFilters) => {
    return callAPI('project-overview', { project_id: projectId, filters })
  }, [callAPI])

  return {
    loading,
    error,
    // API 方法
    brandAnalysis,
    productAnalysis,
    pricingAnalysis,
    marketInsights,
    packagePreference,
    reviewInsights,
    competitorAnalysis,
    allReviewData,
    projectOverview,
    // 通用方法
    callAPI
  }
}

// 便捷的过滤器构建函数
export function buildFilters(options: {
  categories?: string[]
  brands?: string[]
  segments?: string[]
  extendFields?: Record<string, any>
}): DashboardFilters {
  const filters: DashboardFilters = {}
  
  if (options.categories && options.categories.length > 0) {
    filters.categories = options.categories
  }
  
  if (options.brands && options.brands.length > 0) {
    filters.brands = options.brands
  }
  
  if (options.segments && options.segments.length > 0) {
    filters.segments = options.segments
  }
  
  if (options.extendFields && Object.keys(options.extendFields).length > 0) {
    filters.extend_fields = options.extendFields
  }
  
  return filters
}

// 使用示例（代码示例，不包含JSX）
/*
使用示例：

import { useDashboardAPI, buildFilters } from './use-dashboard-api'

function MyComponent() {
  const { brandAnalysis, loading, error } = useDashboardAPI()

  const handleLoadData = async () => {
    try {
      const filters = buildFilters({
        categories: ['Electronics'],
        brands: ['Leviton'],
        extendFields: {
          is_bestseller: true
        }
      })

      const data = await brandAnalysis('project-123', filters)
      console.log('Brand analysis data:', data)
    } catch (err) {
      console.error('Failed to load data:', err)
    }
  }

  return (
    <div>
      <button onClick={handleLoadData} disabled={loading}>
        {loading ? 'Loading...' : 'Load Brand Analysis'}
      </button>
      {error && <div>Error: {error}</div>}
    </div>
  )
}
*/
