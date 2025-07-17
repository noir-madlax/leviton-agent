#!/usr/bin/env python3
"""
测试新的 Dashboard API 结构

这个脚本用于测试新的 POST 请求格式和 JSON 过滤器结构
"""

import asyncio
import json
from typing import Dict, Any

# 模拟测试数据
TEST_PROJECT_ID = "test-project-123"

# 测试用的过滤器数据
TEST_FILTERS = {
    "categories": ["Electronics", "Home & Garden"],
    "brands": ["Leviton", "Lutron"],
    "segments": ["Premium", "Budget"],
    "extend_fields": {
        "is_bestseller": True,
        "price_range": "high",
        "rating": "4+"
    }
}

def create_dashboard_request(project_id: str, filters: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
    """创建标准的 Dashboard 请求"""
    request = {
        "project_id": project_id,
        "filters": filters or {}
    }
    
    # 添加额外的参数（如 metric_type, selected_asins 等）
    request.update(kwargs)
    
    return request

def test_request_models():
    """测试请求模型的创建"""
    print("=== 测试请求模型 ===")
    
    # 1. 基础请求
    basic_request = create_dashboard_request(TEST_PROJECT_ID, TEST_FILTERS)
    print("基础请求:")
    print(json.dumps(basic_request, indent=2, ensure_ascii=False))
    print()
    
    # 2. 包装偏好请求（带 metric_type）
    package_request = create_dashboard_request(
        TEST_PROJECT_ID, 
        TEST_FILTERS, 
        metric_type="revenue"
    )
    print("包装偏好请求:")
    print(json.dumps(package_request, indent=2, ensure_ascii=False))
    print()
    
    # 3. 竞争对手分析请求（带 selected_asins）
    competitor_request = create_dashboard_request(
        TEST_PROJECT_ID,
        TEST_FILTERS,
        selected_asins=["B08XYZ123", "B09ABC456", "B07DEF789"]
    )
    print("竞争对手分析请求:")
    print(json.dumps(competitor_request, indent=2, ensure_ascii=False))
    print()

def test_filter_variations():
    """测试不同的过滤器组合"""
    print("=== 测试过滤器变化 ===")
    
    # 1. 只有类别过滤
    category_only = create_dashboard_request(
        TEST_PROJECT_ID,
        {"categories": ["Light Switches", "Dimmer Switches"]}
    )
    print("只有类别过滤:")
    print(json.dumps(category_only, indent=2, ensure_ascii=False))
    print()
    
    # 2. 只有扩展字段过滤
    extend_only = create_dashboard_request(
        TEST_PROJECT_ID,
        {
            "extend_fields": {
                "is_bestseller": True,
                "has_reviews": True,
                "review_count": "100+"
            }
        }
    )
    print("只有扩展字段过滤:")
    print(json.dumps(extend_only, indent=2, ensure_ascii=False))
    print()
    
    # 3. 空过滤器
    empty_filters = create_dashboard_request(TEST_PROJECT_ID, {})
    print("空过滤器:")
    print(json.dumps(empty_filters, indent=2, ensure_ascii=False))
    print()
    
    # 4. 无过滤器
    no_filters = create_dashboard_request(TEST_PROJECT_ID)
    print("无过滤器:")
    print(json.dumps(no_filters, indent=2, ensure_ascii=False))
    print()

def test_api_endpoints():
    """测试所有 API 端点的请求格式"""
    print("=== 测试 API 端点 ===")
    
    endpoints = [
        "brand-analysis",
        "product-analysis", 
        "pricing-analysis",
        "market-insights",
        "package-preference",
        "review-insights",
        "competitor-analysis",
        "all-review-data",
        "project-overview"
    ]
    
    for endpoint in endpoints:
        print(f"\n{endpoint.upper()} 请求示例:")
        
        if endpoint == "package-preference":
            request = create_dashboard_request(
                TEST_PROJECT_ID,
                TEST_FILTERS,
                metric_type="revenue"
            )
        elif endpoint == "competitor-analysis":
            request = create_dashboard_request(
                TEST_PROJECT_ID,
                TEST_FILTERS,
                selected_asins=["B08XYZ123", "B09ABC456"]
            )
        else:
            request = create_dashboard_request(TEST_PROJECT_ID, TEST_FILTERS)
        
        print(f"POST /api/dashboard/{endpoint}")
        print(json.dumps(request, indent=2, ensure_ascii=False))

def simulate_frontend_usage():
    """模拟前端使用方式"""
    print("\n=== 模拟前端使用 ===")
    
    # TypeScript 接口定义
    typescript_interface = '''
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
'''
    
    print(typescript_interface)
    
    # JavaScript 调用示例
    js_example = '''
// JavaScript 调用示例
async function getBrandAnalysis(projectId, filters) {
  const request = {
    project_id: projectId,
    filters: filters
  };

  const response = await fetch('/api/dashboard/brand-analysis', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(request)
  });

  return await response.json();
}

// 使用示例
const filters = {
  categories: ['Electronics'],
  brands: ['Leviton'],
  extend_fields: {
    is_bestseller: true
  }
};

const data = await getBrandAnalysis('project-123', filters);
'''
    
    print(js_example)

def main():
    """主测试函数"""
    print("🚀 Dashboard API 新结构测试")
    print("=" * 50)
    
    test_request_models()
    test_filter_variations()
    test_api_endpoints()
    simulate_frontend_usage()
    
    print("\n✅ 测试完成！")
    print("\n📝 总结:")
    print("1. 所有接口都改为 POST 请求")
    print("2. 使用统一的 JSON 请求格式")
    print("3. 过滤器结构清晰，易于扩展")
    print("4. 特殊接口（package-preference, competitor-analysis）有额外参数")
    print("5. 前端调用方式简化，类型安全")

if __name__ == "__main__":
    main()
