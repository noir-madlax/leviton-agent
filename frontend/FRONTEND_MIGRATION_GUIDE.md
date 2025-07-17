# 前端 API 迁移指南

## 概述

后端 Dashboard API 已经从 GET 请求改为 POST 请求，使用统一的 JSON 格式传递过滤条件。前端需要相应地进行调整。

## 主要变化

### 1. 请求方式变化

**旧方式 (GET)**:
```typescript
const url = `${API_BASE_URL}/api/v1/dashboard/brand-analysis?project_id=${projectId}&categories=${categories.join(',')}&brands=${brands.join(',')}`
const response = await fetch(url)
```

**新方式 (POST)**:
```typescript
const requestBody = {
  project_id: projectId,
  filters: {
    categories: categories,
    brands: brands,
    segments: segments,
    extend_fields: extendFields
  }
}

const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/brand-analysis`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(requestBody)
})
```

### 2. 过滤器结构统一

所有过滤条件现在都放在 `filters` 对象中：

```typescript
interface DashboardFilters {
  categories?: string[];
  brands?: string[];
  segments?: string[];
  extend_fields?: Record<string, any>;
}

interface DashboardRequest {
  project_id: string;
  filters?: DashboardFilters;
}
```

## 需要更新的文件

### 1. database-service.ts

**主要更新**：
- 所有 Dashboard API 调用方法
- 从 GET 请求改为 POST 请求
- 使用统一的请求体格式

**更新的方法**：
- `getBrandCategoryRevenueByProject`
- `getProductAnalysisDataByProject`
- `getPricingAnalysisDataByProject`
- `getMarketInsightsDataByProject`
- `getPackagePreferenceDataByProject`
- `getReviewInsightsDataByProject`
- `getCompetitorAnalysisDataByProject`
- `getAllReviewDataByProject`
- `getProjectOverview`

### 2. 组件文件

需要更新所有使用这些 API 的组件：

- `frontend/src/components/analysis-db/index.tsx`
- `frontend/src/components/analysis-db/market-analysis/brand-analysis.tsx`
- `frontend/src/components/analysis-db/market-analysis/product-analysis.tsx`
- `frontend/src/components/analysis-db/market-analysis/pricing-analysis.tsx`
- 等等...

## 实施步骤

### 步骤 1: 更新 database-service.ts

1. 添加通用的 API 调用函数
2. 更新所有 Dashboard API 方法
3. 保持方法签名不变，只改变内部实现

### 步骤 2: 创建新的 Hook

使用新的 `useDashboardAPI` Hook 来简化 API 调用：

```typescript
import { useDashboardAPI, buildFilters } from '@/hooks/use-dashboard-api'

function MyComponent() {
  const { brandAnalysis, loading, error } = useDashboardAPI()
  
  const loadData = async () => {
    const filters = buildFilters({
      categories: ['Electronics'],
      brands: ['Leviton']
    })
    
    const data = await brandAnalysis('project-123', filters)
  }
}
```

### 步骤 3: 更新现有组件

逐步更新现有组件，使用新的 API 调用方式。

### 步骤 4: 测试

确保所有功能正常工作。

## 新的 API 调用示例

### Brand Analysis

```typescript
// 旧方式
const data = await databaseService.getBrandCategoryRevenueByProject(
  projectId, 
  categoryFilters, 
  brandFilters, 
  segmentFilters, 
  extendFields
)

// 新方式 (方法签名保持不变，但内部使用 POST)
const data = await databaseService.getBrandCategoryRevenueByProject(
  projectId, 
  categoryFilters, 
  brandFilters, 
  segmentFilters, 
  extendFields
)

// 或者使用新的 Hook
const { brandAnalysis } = useDashboardAPI()
const filters = buildFilters({
  categories: categoryFilters,
  brands: brandFilters,
  segments: segmentFilters,
  extendFields: extendFields
})
const data = await brandAnalysis(projectId, filters)
```

### Package Preference (特殊参数)

```typescript
// 新方式 - 包含 metric_type
const { packagePreference } = useDashboardAPI()
const data = await packagePreference(projectId, filters, 'revenue')
```

### Competitor Analysis (特殊参数)

```typescript
// 新方式 - 包含 selected_asins
const { competitorAnalysis } = useDashboardAPI()
const data = await competitorAnalysis(projectId, filters, ['ASIN1', 'ASIN2'])
```

## 错误处理

新的 API 调用包含更好的错误处理：

```typescript
const { brandAnalysis, loading, error } = useDashboardAPI()

try {
  const data = await brandAnalysis(projectId, filters)
  // 处理成功响应
} catch (err) {
  // 处理错误
  console.error('API call failed:', err)
}

// 或者使用 Hook 的错误状态
if (error) {
  return <div>Error: {error}</div>
}
```

## 向后兼容性

为了确保平滑迁移：

1. **保持方法签名不变**：现有的方法调用不需要修改
2. **渐进式迁移**：可以逐步迁移到新的 Hook 方式
3. **错误回退**：如果新 API 失败，可以临时回退到旧方式

## 测试清单

- [ ] Brand Analysis 数据加载正常
- [ ] Product Analysis 数据加载正常
- [ ] Pricing Analysis 数据加载正常
- [ ] Market Insights 数据加载正常
- [ ] Package Preference 数据加载正常
- [ ] Review Insights 数据加载正常
- [ ] Competitor Analysis 数据加载正常
- [ ] All Review Data 数据加载正常
- [ ] Project Overview 数据加载正常
- [ ] 过滤器功能正常工作
- [ ] 错误处理正常
- [ ] 加载状态显示正常

## 注意事项

1. **API 端点路径不变**：只是请求方式从 GET 改为 POST
2. **响应格式不变**：后端响应格式保持不变
3. **过滤器逻辑增强**：新的过滤器结构更加灵活
4. **性能优化**：POST 请求可以处理更复杂的过滤条件

## 完成后的优势

1. **统一的 API 格式**：所有 Dashboard API 使用相同的请求格式
2. **更好的扩展性**：新增过滤条件不需要修改接口
3. **类型安全**：完整的 TypeScript 类型定义
4. **更好的错误处理**：统一的错误处理机制
5. **代码复用**：通用的 API 调用函数减少重复代码
