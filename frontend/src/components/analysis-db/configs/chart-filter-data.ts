/**
 * Chart Filter 配置数据
 * 每个chart的专属筛选器配置
 */

import { ChartFilterConfig } from './filter-config'
import { CHART_NAMES } from '../constants'

// 重新导出类型，方便其他文件使用
export type { ChartFilterConfig } from './filter-config'

// Chart Filter配置映射
export const CHART_FILTER_CONFIGS: Record<string, ChartFilterConfig> = {
  // Brand Analysis Chart配置
  [CHART_NAMES.BRAND_ANALYSIS]: {
    chart_id: CHART_NAMES.BRAND_ANALYSIS,
    chart_type: CHART_NAMES.BRAND_ANALYSIS,
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7', // 这个会动态设置
    inherit_from_project: false, // 不完全继承，有自己的定制
    
    visible_filters: {
      categories: true,
      brands: true,
      segments: false,
      timeframe: true,
      extend_fields: true // 明确指定可见的扩展字段
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
  [CHART_NAMES.MARKET_SHARE_ANALYSIS]: {
    chart_id: CHART_NAMES.MARKET_SHARE_ANALYSIS,
    chart_type: CHART_NAMES.MARKET_SHARE_ANALYSIS,
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    inherit_from_project: false,
    
    visible_filters: {
      categories: true,
      brands: false,  // 这个chart不显示brand筛选
      segments: true, // 但显示segments筛选
      timeframe: true,
      extend_fields: true // 明确指定可见的扩展字段
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
        field_name: 'dfasdfasdf',
        display_name: 'Smart asdfasdfa',
        field_type: 'select',
        filter_options: {
          options: ['111', '2222'], // 这个chart不显示All选项
          default: '111'
        },
        is_required: true, // 这个chart必须选择
        sort_order: 2
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
        sort_order: 3
      }
    ],
    
    metadata: {
      name: 'Market Share Analysis Filter',
      description: '市场份额分析图表的筛选器配置'
    }
  },

  // Sales Trend Analysis Chart配置
  [CHART_NAMES.SALES_TREND_ANALYSIS]: {
    chart_id: CHART_NAMES.SALES_TREND_ANALYSIS,
    chart_type: CHART_NAMES.SALES_TREND_ANALYSIS,
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    inherit_from_project: true, // 完全继承Project配置
    
    visible_filters: {
      categories: true,
      brands: true,
      segments: false,
      timeframe: true,
      extend_fields: true // true表示显示所有继承的扩展字段
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
  },

  // Price Analysis Chart配置
  [CHART_NAMES.PRICE_ANALYSIS]: {
    chart_id: CHART_NAMES.PRICE_ANALYSIS,
    chart_type: CHART_NAMES.PRICE_ANALYSIS,
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7', // 动态设置，与TAM一致
    inherit_from_project: false, // 不完全继承，有自己的定制
    
    visible_filters: {
      categories: true,
      brands: true,
      segments: false,
      timeframe: true,
      extend_fields: true // 修复：明确指定可见的扩展字段
    },
    
    default_values: {
      categories: [],
      brands: [], // 默认看所有品牌
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
      name: 'Price Analysis Filter',
      description: '价格分布分析专用筛选器',
      version: '1.0.0',
      created_at: '2024-01-15',
      updated_at: '2024-01-15'
    }
  },

  // Price vs Revenue散点图配置
  [CHART_NAMES.PRICE_VS_REVENUE]: {
    chart_id: CHART_NAMES.PRICE_VS_REVENUE,
    chart_type: CHART_NAMES.PRICE_VS_REVENUE,
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    inherit_from_project: false,
    
    visible_filters: {
      categories: true,
      brands: true,
      segments: true,
      timeframe: true,
      extend_fields: true
    },
    
    default_values: {
      categories: [],
      brands: [],
      segments: [],
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
      name: 'Price vs Revenue Scatter Filter',
      description: '价格收入散点图专用筛选器',
      version: '1.0.0',
      created_at: '2024-01-15',
      updated_at: '2024-01-15'
    }
  },

  // Brand Price Distribution配置
  [CHART_NAMES.BRAND_PRICE_DISTRIBUTION]: {
    chart_id: CHART_NAMES.BRAND_PRICE_DISTRIBUTION,
    chart_type: CHART_NAMES.BRAND_PRICE_DISTRIBUTION,
    project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    inherit_from_project: false,
    
    visible_filters: {
      categories: true,
      brands: true,
      segments: false, // 品牌分布不需要segments筛选
      timeframe: true,
      extend_fields: true
    },
    
    default_values: {
      categories: [],
      brands: [],
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
      name: 'Brand Price Distribution Filter',
      description: '品牌价格分布专用筛选器',
      version: '1.0.0',
      created_at: '2024-01-15',
      updated_at: '2024-01-15'
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