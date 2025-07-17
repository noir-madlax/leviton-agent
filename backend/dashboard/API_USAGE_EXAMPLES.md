# Dashboard API 使用示例

## 概述

所有 Dashboard 数据获取接口已经从 GET 请求改为 POST 请求，使用统一的 JSON 格式传递过滤条件。

## 统一的请求格式

### 基础请求结构

```json
{
  "project_id": "string",
  "filters": {
    "categories": ["category1", "category2"],
    "brands": ["brand1", "brand2"],
    "segments": ["segment1", "segment2"],
    "extend_fields": {
      "field_name": "value",
      "is_bestseller": true,
      "price_range": "high"
    }
  },
  "options": {
    "limit": 10,
    "offset": 0,
    "sort_by": "revenue",
    "sort_order": "desc"
  }
}
```

### 字段说明

- **project_id**: 必填，项目ID
- **filters**: 可选，过滤条件对象
  - **categories**: 类别过滤，字符串数组
  - **brands**: 品牌过滤，字符串数组
  - **segments**: 段过滤，字符串数组
  - **extend_fields**: 扩展字段过滤，键值对对象
- **options**: 可选，查询选项
  - **limit**: 限制返回结果数量
  - **offset**: 分页偏移量
  - **sort_by**: 排序字段
  - **sort_order**: 排序方向 ("asc" 或 "desc")

## 接口列表

### 1. 品牌分析 - Brand Analysis

**接口**: `POST /api/dashboard/brand-analysis`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "categories": ["Electronics", "Home & Garden"],
    "brands": ["Leviton", "Lutron"],
    "segments": ["Premium", "Budget"]
  }
}
```

### 2. 产品分析 - Product Analysis

**接口**: `POST /api/dashboard/product-analysis`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "categories": ["Light Switches"],
    "extend_fields": {
      "is_bestseller": true,
      "rating": "4+"
    }
  }
}
```

### 3. 价格分析 - Pricing Analysis

**接口**: `POST /api/dashboard/pricing-analysis`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "brands": ["Leviton"],
    "segments": ["Premium"],
    "extend_fields": {
      "price_range": "high"
    }
  }
}
```

### 4. 市场洞察 - Market Insights

**接口**: `POST /api/dashboard/market-insights`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "categories": ["Dimmer Switches", "Light Switches"],
    "segments": ["Premium"]
  }
}
```

### 5. 包装偏好 - Package Preference

**接口**: `POST /api/dashboard/package-preference`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "brands": ["Leviton"],
    "categories": ["Light Switches"]
  },
  "metric_type": "revenue"
}
```

### 6. 评论洞察 - Review Insights

**接口**: `POST /api/dashboard/review-insights`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "segments": ["Premium"],
    "extend_fields": {
      "has_reviews": true
    }
  }
}
```

### 7. 竞争对手分析 - Competitor Analysis

**接口**: `POST /api/dashboard/competitor-analysis`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "categories": ["Light Switches"],
    "brands": ["Leviton", "Lutron"]
  },
  "selected_asins": ["B08XYZ123", "B09ABC456"]
}
```

### 8. 所有评论数据 - All Review Data

**接口**: `POST /api/dashboard/all-review-data`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "segments": ["Premium"],
    "extend_fields": {
      "review_count": "100+"
    }
  }
}
```

### 9. 项目概览 - Project Overview

**接口**: `POST /api/dashboard/project-overview`

**请求示例**:
```json
{
  "project_id": "project-123",
  "filters": {
    "categories": ["Electronics"],
    "brands": ["Leviton"]
  }
}
```

## 前端调用示例

### JavaScript/TypeScript

```typescript
// 定义过滤器接口
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

// 调用示例
async function getBrandAnalysis(projectId: string, filters?: DashboardFilters) {
  const request: DashboardRequest = {
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

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

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

const brandData = await getBrandAnalysis('project-123', filters);
```

## 优势

1. **统一性**: 所有接口使用相同的请求格式
2. **扩展性**: 新增过滤条件不需要修改接口签名
3. **类型安全**: 完整的 Pydantic 模型验证
4. **简洁性**: 装饰器自动处理过滤器逻辑
5. **可维护性**: 代码重复度大大降低

## 迁移指南

### 从旧的 GET 请求迁移

**旧方式**:
```
GET /api/dashboard/brand-analysis?project_id=123&categories=Electronics,Home&brands=Leviton
```

**新方式**:
```json
POST /api/dashboard/brand-analysis
{
  "project_id": "123",
  "filters": {
    "categories": ["Electronics", "Home"],
    "brands": ["Leviton"]
  }
}
```
