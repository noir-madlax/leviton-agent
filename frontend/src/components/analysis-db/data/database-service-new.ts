/**
 * 新版本的 Database Service - 适配 POST API
 * 
 * 这个文件包含了所有更新后的 API 调用方法，使用新的 POST 请求格式
 */

import { createClient } from '@supabase/supabase-js'

// Supabase 配置
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
const supabase = createClient(supabaseUrl, supabaseKey)

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
async function callDashboardAPI(endpoint: string, projectId: string, options: {
  categoryFilters?: string[]
  packagingTypeFilters?: string[]
  segmentFilters?: string[]
  extendFields?: Record<string, any>
  selectedAsins?: string[]
  metricType?: string
} = {}) {
  const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  
  const requestBody: any = {
    project_id: projectId,
    filters: {
      ...(options.categoryFilters && options.categoryFilters.length > 0 && { categories: options.categoryFilters }),
      ...(options.packagingTypeFilters && options.packagingTypeFilters.length > 0 && { brands: options.packagingTypeFilters }),
      ...(options.segmentFilters && options.segmentFilters.length > 0 && { segments: options.segmentFilters }),
      ...(options.extendFields && Object.keys(options.extendFields).length > 0 && { extend_fields: options.extendFields })
    }
  }

  // 添加特殊参数
  if (options.selectedAsins) {
    requestBody.selected_asins = options.selectedAsins
  }
  if (options.metricType) {
    requestBody.metric_type = options.metricType
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(requestBody)
  })

  if (!response.ok) {
    throw new Error(`API call failed: ${response.status}`)
  }

  return await response.json()
}

export class DatabaseService {
  
  // 🔑 Brand Analysis
  async getBrandCategoryRevenueByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
    try {
      const result = await callDashboardAPI('brand-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      return {
        brandCategoryRevenue: result.data || [],
        segmentNames: result.segmentNames || [],
        segmentColors: result.segmentColors || []
      }
    } catch (error) {
      console.error('Error fetching brand analysis:', error)
      throw error
    }
  }

  // 🔑 Product Analysis
  async getProductAnalysisDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
    try {
      const result = await callDashboardAPI('product-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      return {
        priceVsRevenue: result.priceVsRevenue || [],
        topProducts: result.topProducts || { segments: {}, dimmerSwitches: [], lightSwitches: [] },
        segmentSummary: result.segmentSummary || {},
        segmentNames: result.segmentNames || [],
        segmentColors: result.segmentColors || []
      }
    } catch (error) {
      console.error('Error fetching product analysis:', error)
      throw error
    }
  }

  // 🔑 Pricing Analysis
  async getPricingAnalysisDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
    try {
      const result = await callDashboardAPI('pricing-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      return result
    } catch (error) {
      console.error('Error fetching pricing analysis:', error)
      throw error
    }
  }

  // 🔑 Market Insights
  async getMarketInsightsDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
    try {
      const result = await callDashboardAPI('market-insights', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      return result
    } catch (error) {
      console.error('Error fetching market insights:', error)
      throw error
    }
  }

  // 🔑 Package Preference
  async getPackagePreferenceDataByProject(projectId: string, categoryFilters?: string[], brandFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>, metricType: string = 'revenue') {
    try {
      const result = await callDashboardAPI('package-preference', projectId, {
        categoryFilters,
        packagingTypeFilters: brandFilters,
        segmentFilters,
        extendFields,
        metricType
      })
      
      return result
    } catch (error) {
      console.error('Error fetching package preference:', error)
      throw error
    }
  }

  // 🔑 Review Insights
  async getReviewInsightsDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
    try {
      const result = await callDashboardAPI('review-insights', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      return result
    } catch (error) {
      console.error('Error fetching review insights:', error)
      throw error
    }
  }

  // 🔑 Competitor Analysis
  async getCompetitorAnalysisDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>, selectedAsins?: string) {
    try {
      const result = await callDashboardAPI('competitor-analysis', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields,
        selectedAsins: selectedAsins ? selectedAsins.split(',') : undefined
      })
      
      return result
    } catch (error) {
      console.error('Error fetching competitor analysis:', error)
      throw error
    }
  }

  // 🔑 All Review Data
  async getAllReviewDataByProject(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
    try {
      const result = await callDashboardAPI('all-review-data', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      return result
    } catch (error) {
      console.error('Error fetching all review data:', error)
      throw error
    }
  }

  // 🔑 Project Overview
  async getProjectOverview(projectId: string, categoryFilters?: string[], packagingTypeFilters?: string[], segmentFilters?: string[], extendFields?: Record<string, any>) {
    try {
      const result = await callDashboardAPI('project-overview', projectId, {
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      })
      
      return result
    } catch (error) {
      console.error('Error fetching project overview:', error)
      throw error
    }
  }

  // 保留其他非 Dashboard 相关的方法...
  // 这些方法不需要修改，因为它们不是 Dashboard API
  
  // 项目相关方法
  async getProjects(userUid?: string) {
    // 保持原有实现
  }
  
  async getProject(id: string) {
    // 保持原有实现
  }
  
  // 数据确认相关方法
  async getDataConfirmationData(filters?: any) {
    // 保持原有实现
  }
  
  // 其他工具方法...
}

// 导出单例
export const databaseService = new DatabaseService()
