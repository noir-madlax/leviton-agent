# Chart重构规范文档

## 概述

本文档基于TAM饼图的成功重构经验，制定了统一的Chart重构标准，确保所有图表组件都遵循一致的架构模式和最佳实践。

## 架构对比分析

### TAM饼图架构（标准模板）

#### 后端架构
```
backend/dashboard/charts/market_analysis/
├── __init__.py
├── models.py          # Pydantic数据模型
├── service.py         # 业务逻辑服务
└── README.md          # API文档
```

#### 前端架构
```
frontend/src/components/analysis-db/
├── market-analysis/brand-analysis.tsx    # 组件实现
├── hooks/use-chart-data-refresh.ts       # 数据刷新Hook
├── data/database-service.ts              # 数据服务
└── filters/                              # 统一过滤器系统
```

### Price Distribution架构（待重构）

#### 当前问题
- 后端服务分散在`services/pricing_analysis_service.py`
- 缺乏统一的API路由结构
- 前端使用老旧的ChartWithFilters组件
- 没有专门的数据刷新机制
- 缺乏统一的状态管理

## Chart重构标准规范

### 1. 后端架构标准

#### 1.1 目录结构
```
backend/dashboard/charts/{module_name}/
├── __init__.py
├── models.py          # 数据模型定义
├── service.py         # 业务逻辑实现
└── README.md          # API文档和使用说明
```

#### 1.2 数据模型标准
```python
# models.py 模板
from typing import List, Optional, Literal
from pydantic import BaseModel, Field
from ..base_models import BaseRequestModel

class {ChartName}Request(BaseRequestModel):
    """请求模型，继承BaseRequestModel获得过滤器支持"""
    
    # 特定参数
    metric_type: Literal["revenue", "products"] = Field(
        default="revenue", 
        description="分析指标类型"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "uuid",
                "filters": {...},
                "timeframe": {...}
            }
        }

class {ChartName}Response(BaseModel):
    """响应模型"""
    data: {ChartName}Data
    metadata: {ChartName}Metadata
```

#### 1.3 服务层标准
```python
# service.py 模板
class {ChartName}Service:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def get_{chart_name}_data(self, request: {ChartName}Request):
        """主要业务逻辑方法"""
        try:
            # 1. 获取过滤后的ASINs
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            # 2. 查询数据
            data = self._get_data_from_wide_table(request, filtered_asins)
            
            # 3. 处理和聚合
            processed_data = self._process_data(data, request)
            
            # 4. 生成响应
            return self._build_response(processed_data, request)
            
        except Exception as e:
            logger.error(f"Error in {chart_name} analysis: {e}")
            raise
```

#### 1.4 API路由标准
```python
# 在 charts/api.py 中添加
@router.post("/{module-name}/{chart-name}", response_model={ChartName}Response)
async def get_{chart_name}(request: {ChartName}Request):
    """
    完整的API文档说明
    包含请求示例、响应示例、参数说明
    """
    try:
        supabase_client = get_supabase_client()
        service = {ChartName}Service(supabase_client)
        return service.get_{chart_name}_data(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### 2. 前端架构标准

#### 2.1 数据服务标准
```typescript
// database-service.ts 中添加
async get{ChartName}Data(projectId: string): Promise<{ChartName}Response> {
  try {
    // 从过滤器状态管理器获取过滤器
    const filters = this.getFiltersFromState(CHART_NAMES.{CHART_NAME})
    
    const requestBody = {
      project_id: projectId,
      ...filters
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/{module-name}/{chart-name}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })
    
    if (!response.ok) {
      throw new Error(`API call failed: ${response.status}`)
    }
    
    return await response.json()
  } catch (error) {
    console.error('Error fetching chart data:', error)
    throw error
  }
}
```

#### 2.2 数据刷新Hook标准
```typescript
// use-chart-data-refresh.ts 中添加
export function use{ChartName}DataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: '{chart-id}',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.get{ChartName}Data(projectId)
    }
  })
}
```

#### 2.3 组件集成标准
```typescript
// 组件中的标准集成模式
export function {ChartName}Component({ projectId, initialFilters }: Props) {
  // 使用统一的数据刷新Hook
  const {
    data: chartData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = use{ChartName}DataRefresh(projectId)
  
  // 过滤器处理
  const handleFiltersChange = useCallback((newFilters: ProjectFilters) => {
    refreshData(newFilters)
  }, [refreshData])
  
  return (
    <div>
      {/* 使用统一的FilterRenderer */}
      <FilterRenderer
        projectId={projectId}
        chartName="{chart-name}"
        currentFilters={filters}
        onChange={handleFiltersChange}
        disabled={dataLoading}
      />
      
      {/* 统一的状态处理 */}
      {dataLoading ? (
        <LoadingState />
      ) : dataError ? (
        <ErrorState error={dataError} onRetry={() => refreshData(filters)} />
      ) : (
        <ChartContent data={chartData} />
      )}
    </div>
  )
}
```

### 3. 配置和集成标准

#### 3.1 过滤器配置
```typescript
// 在 project-filter-data.ts 中添加图表支持
applies_to_charts: [
  'existing-charts',
  '{new-chart-name}'  // 添加新图表
]
```

#### 3.2 图表显示控制
```typescript
// 在相关配置中添加图表控制
const chartSections = {
  '{chart-module}': [
    '{chart-name}',
    // 其他图表...
  ]
}
```

## Price Distribution重构具体调整清单

### 后端调整（按优先级排序）

1. **创建模块结构**
   - 创建 `backend/dashboard/charts/pricing_analysis/` 目录
   - 创建 `__init__.py`, `models.py`, `service.py`, `README.md`

2. **定义数据模型**
   - 在 `models.py` 中定义 `PriceDistributionRequest`, `PriceDistributionResponse`
   - 支持 `metric_type` (sku/unit), `analysis_type` (distribution/comparison)
   - 包含完整的元数据模型

3. **实现服务类**
   - 创建 `PriceDistributionService` 类
   - 迁移现有的价格分析逻辑
   - 集成统一的过滤器服务
   - 支持多种分析类型

4. **注册API路由**
   - 在 `charts/api.py` 中添加路由
   - 路径：`/pricing-analysis/price-distribution`
   - 完整的错误处理和日志记录

### 前端调整（按优先级排序）

1. **添加数据服务**
   - 在 `database-service.ts` 中添加 `getPriceDistributionData` 方法
   - 集成过滤器状态管理
   - 支持不同的分析参数

2. **创建数据刷新Hook**
   - 创建 `usePriceDistributionDataRefresh` hook
   - 支持参数变化时自动刷新
   - 统一的状态管理

3. **重构组件实现**
   - 替换 `ChartWithFilters` 为 `FilterRenderer`
   - 集成新的数据获取机制
   - 添加统一的加载和错误状态
   - 保持现有的图表功能

4. **更新配置**
   - 在过滤器配置中添加 `pricing-analysis` 支持
   - 更新图表显示控制逻辑
   - 确保与现有系统兼容

### 验证和测试

1. **API功能验证**
   - 测试所有过滤器组合
   - 验证数据准确性
   - 检查错误处理

2. **前端集成测试**
   - 验证过滤器功能
   - 测试数据刷新机制
   - 检查用户体验一致性

3. **性能测试**
   - 对比重构前后的性能
   - 优化查询效率
   - 确保响应时间合理

## 重构执行流程

### 阶段1：后端重构（2-3小时）
1. 创建模块结构和模型定义
2. 实现服务类和业务逻辑
3. 注册API路由和测试

### 阶段2：前端集成（2-3小时）
1. 添加数据服务和Hook
2. 重构组件实现
3. 更新配置和集成测试

### 阶段3：验证优化（1-2小时）
1. 功能验证和测试
2. 性能优化
3. 文档更新

## 最佳实践总结

1. **统一性**：所有图表遵循相同的架构模式
2. **模块化**：清晰的职责分离和依赖关系
3. **可维护性**：完整的文档和错误处理
4. **可扩展性**：支持新功能和需求变化
5. **用户体验**：一致的交互和状态管理

## 后续LLM执行指南

使用本规范重构图表时，请：

1. **严格遵循**架构标准和代码模板
2. **完整实现**所有必需的组件和功能
3. **保持一致性**与现有TAM饼图的实现模式
4. **充分测试**确保功能正确性和性能
5. **更新文档**保持文档与代码同步

本规范确保了重构的系统性、一致性和高质量，为项目的长期维护和发展奠定了坚实基础。
