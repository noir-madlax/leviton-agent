#!/usr/bin/env python3
"""
脚本：批量更新前端 API 调用从 GET 改为 POST

这个脚本会自动更新 database-service.ts 中的所有 Dashboard API 调用
"""

import re

# 需要更新的 API 方法映射
API_METHODS = {
    'getPricingAnalysisDataByProject': 'pricing-analysis',
    'getMarketInsightsDataByProject': 'market-insights', 
    'getPackagePreferenceDataByProject': 'package-preference',
    'getReviewInsightsDataByProject': 'review-insights',
    'getCompetitorAnalysisDataByProject': 'competitor-analysis',
    'getAllReviewDataByProject': 'all-review-data',
    'getProjectOverview': 'project-overview'
}

def generate_method_replacement(method_name, endpoint):
    """生成方法替换的代码"""
    
    if endpoint == 'package-preference':
        # package-preference 需要 metricType 参数
        return f'''    try {{
      const result = await callDashboardAPI('{endpoint}', projectId, {{
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields,
        metricType
      }})'''
    
    elif endpoint == 'competitor-analysis':
        # competitor-analysis 需要 selectedAsins 参数
        return f'''    try {{
      const result = await callDashboardAPI('{endpoint}', projectId, {{
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields,
        selectedAsins: selectedAsins ? selectedAsins.split(',') : undefined
      }})'''
    
    else:
        # 标准方法
        return f'''    try {{
      const result = await callDashboardAPI('{endpoint}', projectId, {{
        categoryFilters,
        packagingTypeFilters,
        segmentFilters,
        extendFields
      }})'''

def print_replacements():
    """打印所有需要的替换"""
    print("=== 需要进行的 API 调用替换 ===\n")
    
    for method_name, endpoint in API_METHODS.items():
        print(f"方法: {method_name}")
        print(f"端点: {endpoint}")
        print("替换代码:")
        print(generate_method_replacement(method_name, endpoint))
        print("\n" + "="*50 + "\n")

def generate_typescript_interfaces():
    """生成 TypeScript 接口定义"""
    interfaces = '''
// 新的 TypeScript 接口定义
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
'''
    return interfaces

def main():
    print("🔄 前端 API 调用更新脚本")
    print("=" * 50)
    
    print_replacements()
    
    print("📝 TypeScript 接口定义:")
    print(generate_typescript_interfaces())
    
    print("\n✅ 脚本完成！")
    print("\n📋 手动操作步骤：")
    print("1. 使用上面的替换代码更新每个方法")
    print("2. 添加 TypeScript 接口定义")
    print("3. 测试所有 API 调用")
    print("4. 更新前端组件中的调用方式")

if __name__ == "__main__":
    main()
