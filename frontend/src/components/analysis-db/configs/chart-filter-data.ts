/**
 * Chart Filter 配置数据
 * 每个chart的专属筛选器配置
 */

import { ChartFilterConfig } from './filter-config'

// Chart Filter配置映射
export const CHART_FILTER_CONFIGS: Record<string, ChartFilterConfig> = {
  // Brand Analysis Chart配置
  'brand-analysis': {
    chart_id: 'brand-analysis',
    chart_type: 'brand-analysis',
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7', // 这个会动态设置
    inherit_from_project: false, // 不完全继承，有自己的定制
    
    visible_filters: {
      categories: true,
      brands: true,
      segments: false,
      timeframe: true,
      extend_fields: true
    },
    
    default_values: {
      categories: [],
      brands: ['Leviton'], // 这个chart默认只看Leviton品牌
      timeframe: '1_year',
      extend_fields: {
        smart_capability: 'All'
      }
    },
    
    extend_fields: [
      {
        field_name: 'smart_capability',
        display_name: 'Smart Capability',
        field_type: 'select',
        filter_options: {
          options: ['All', 'Smart', 'Non-Smart'],
          default: 'All'
        },
        is_required: false,
        sort_order: 1
      }
    ],
    
    metadata: {
      name: 'Brand Analysis Filter',
      description: '品牌分析图表的筛选器配置'
    }
  },

  // Market Share Analysis Chart配置
  'market-share-analysis': {
    chart_id: 'market-share-analysis',
    chart_type: 'market-share-analysis',
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    inherit_from_project: false,
    
    visible_filters: {
      categories: true,
      brands: false,  // 这个chart不显示brand筛选
      segments: true, // 但显示segments筛选
      timeframe: true,
      extend_fields: true
    },
    
    default_values: {
      categories: [],
      segments: [],
      timeframe: '6_months', // 默认6个月
      extend_fields: {
        smart_capability: 'Smart' // 默认只看Smart产品
      }
    },
    
    extend_fields: [
      {
        field_name: 'smart_capability',
        display_name: 'Smart Capability',
        field_type: 'select',
        filter_options: {
          options: ['Smart', 'Non-Smart'], // 这个chart不显示All选项
          default: 'Smart'
        },
        is_required: true, // 这个chart必须选择
        sort_order: 1
      },
      {
        field_name: 'market_segment',
        display_name: 'Market Segment',
        field_type: 'multi_select',
        filter_options: {
          options: ['Premium', 'Mid-range', 'Budget'],
          default: ['Premium'],
          placeholder: '选择市场细分'
        },
        is_required: false,
        sort_order: 2
      }
    ],
    
    metadata: {
      name: 'Market Share Analysis Filter',
      description: '市场份额分析图表的筛选器配置'
    }
  },

  // Sales Trend Analysis Chart配置
  'sales-trend-analysis': {
    chart_id: 'sales-trend-analysis',
    chart_type: 'sales-trend-analysis',
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    inherit_from_project: true, // 完全继承Project配置
    
    visible_filters: {
      categories: true,
      brands: true,
      segments: false,
      timeframe: true,
      extend_fields: true
    },
    
    default_values: {
      timeframe: '1_year', // 销售趋势图默认看1年
      extend_fields: {}
    },
    
    extend_fields: [], // 继承Project的扩展字段
    
    metadata: {
      name: 'Sales Trend Analysis Filter',
      description: '销售趋势分析图表的筛选器配置'
    }
  }
}

// 获取Chart Filter配置的函数
export async function getChartFilterConfig(
  projectId: string, 
  chartId: string
): Promise<ChartFilterConfig | null> {
  // 模拟API延迟
  await new Promise(resolve => setTimeout(resolve, 50))
  
  // 后续这里会改为真实的API调用
  // return fetch(`/api/projects/${projectId}/charts/${chartId}/filter-config`)
  //   .then(res => res.json())
  
  const config = CHART_FILTER_CONFIGS[chartId]
  if (!config) return null
  
  return {
    ...config,
    project_id: projectId
  }
}

// 获取所有Chart配置的函数
export async function getAllChartFilterConfigs(projectId: string): Promise<Record<string, ChartFilterConfig>> {
  const configs: Record<string, ChartFilterConfig> = {}
  
  for (const [chartId, config] of Object.entries(CHART_FILTER_CONFIGS)) {
    configs[chartId] = {
      ...config,
      project_id: projectId
    }
  }
  
  return configs
}