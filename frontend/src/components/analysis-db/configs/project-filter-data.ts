/**
 * Project Filter 配置数据
 * 这里暂时写在前端，后续会从后端API获取
 */

import { ProjectFilterConfig, TIMEFRAME_OPTIONS } from './filter-config'

// 项目ID - 这个应该动态传入，这里只是示例
const DEMO_PROJECT_ID = 'd2c02b80-4c82-44cc-8093-56708a7883f7'

// Project Filter配置数据
export const PROJECT_FILTER_DATA: ProjectFilterConfig = {
  project_id: DEMO_PROJECT_ID,
  
  // 控制Project级别显示哪些筛选器
  visible_filters: {
    categories: true,
    brands: true,
    segments: false,      // Project级别暂时不显示segments
    timeframe: true,
    extend_fields: true
  },
  
  // Project级别的默认值
  default_values: {
    categories: [],       // 默认不选择任何category
    brands: [],          // 默认不选择任何brand
    segments: [],
    timeframe: '1_year', // 默认选择1年
    extend_fields: {
      smart_capability: 'All'  // Smart Capability默认选择All
    }
  },
  
  // 扩展字段配置
  extend_fields: [
    {
      field_name: 'smart_capability',
      display_name: 'Smart Capability',
      field_type: 'select',
      filter_options: {
        options: ['All', 'Smart', 'Non-Smart'],
        default: 'All',
        placeholder: '选择智能功能',
        description: '筛选产品的智能功能类型'
      },
      is_required: false,
      sort_order: 1
    },
    {
      field_name: 'package_type',
      display_name: 'Package Type',
      field_type: 'select',
      filter_options: {
        options: ['All', 'Individual', 'Package'],
        default: 'All',
        placeholder: '选择包装类型'
      },
      is_required: false,
      sort_order: 2
    },
    {
      field_name: 'price_range',
      display_name: 'Price Range',
      field_type: 'range',
      filter_options: {
        min: 0,
        max: 1000,
        step: 10,
        default: [0, 1000],
        description: '价格区间筛选'
      },
      is_required: false,
      sort_order: 3
    }
  ],
  
  // 配置适用于哪些chart
  applies_to_charts: [
    'brand-analysis',
    'market-share-analysis', 
    'sales-trend-analysis',
    'competitor-analysis'
  ],
  
  // 元信息
  metadata: {
    name: 'Default Project Filter',
    description: 'Leviton项目的默认筛选器配置',
    version: '1.0.0',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString()
  }
}

// 获取Project Filter配置的函数（模拟API调用）
export async function getProjectFilterConfig(projectId: string): Promise<ProjectFilterConfig> {
  // 模拟API延迟
  await new Promise(resolve => setTimeout(resolve, 100))
  
  // 后续这里会改为真实的API调用
  // return fetch(`/api/projects/${projectId}/filter-config`).then(res => res.json())
  
  return {
    ...PROJECT_FILTER_DATA,
    project_id: projectId
  }
}

// 时间周期选项配置
export const TIMEFRAME_CONFIG = {
  options: TIMEFRAME_OPTIONS,
  default: '1_year' as const,
  required: true
}