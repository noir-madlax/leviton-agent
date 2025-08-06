# Price Distribution 价格分布分析重构设计文档

## 📋 概述

本文档详细描述了Price Distribution（价格分布分析）图表的完整重构方案。基于TAM饼图的成功架构模式，将Price Distribution从传统分散架构升级为现代化、模块化、标准化的实现。

### 重构目标

- **架构统一化**：与TAM饼图保持完全一致的架构模式
- **模块化重构**：采用标准的模块化目录结构
- **API标准化**：集成统一的API路由和错误处理
- **前端现代化**：使用FilterRenderer和专用Hook
- **状态管理统一**：完整的loading/error/data状态处理

## 🎯 架构对比分析

### 当前架构问题

- ❌ **后端分散**：代码在 `services/pricing_analysis_service.py`，非模块化
- ❌ **模型混合**：数据模型定义在通用的 `dashboard/models.py`中
- ❌ **缺失API**：没有在 `charts/api.py`中注册统一路由
- ❌ **前端老旧**：使用 `ChartWithFilters`而非 `FilterRenderer`
- ❌ **数据服务缺失**：`database-service.ts`中没有对应方法
- ❌ **状态管理不统一**：缺乏标准化的状态处理

### 目标架构（TAM饼图标准）

- ✅ **模块化结构**：`backend/dashboard/charts/pricing_analysis/`
- ✅ **标准化模型**：完整的Pydantic模型定义
- ✅ **统一服务层**：`PriceDistributionService`类
- ✅ **集成API路由**：在 `charts/api.py`中统一管理
- ✅ **现代化前端**：使用 `FilterRenderer`和专用Hook
- ✅ **标准化数据服务**：`database-service.ts`中的专门方法
- ✅ **完整状态管理**：统一的loading/error/data状态

## 🏗️ 详细设计方案

## 🏗️ 后端重构实施方案 (标准模板)

### 3.1. 目录结构

所有价格分析图表都应遵循此结构。

```
backend/dashboard/charts/pricing_analysis/
├── __init__.py         # 模块初始化
├── models.py           # Pydantic 数据模型定义
├── services.py         # 业务逻辑服务 (注意：是services.py，复数)
└── README.md           # [可选] 复杂的API文档和使用说明
```

### 3.2. 数据模型设计 (`models.py`)

**核心原则**: 为每个图表或一组关联图表定义独立的请求和响应模型。

**实际案例 (`PriceDistribution`)**:

```python
# backend/dashboard/charts/pricing_analysis/models.py

from typing import List, Dict
from pydantic import BaseModel, Field
from ..base_models import BaseRequestModel

# 1. 请求模型：直接继承BaseRequestModel，自动获得过滤器和时间范围支持
class PriceDistributionRequest(BaseRequestModel):
    """价格分布分析请求模型"""
    class Config:
        json_schema_extra = { "example": { ... } }
  
# 2. 响应模型：结构扁平化，包含前端所需的所有数据
class PriceStatistics(BaseModel):
    min: float
    q1: float
    median: float
    mean: float
    q3: float
    max: float
  
class CategoryPriceData(BaseModel):
    category: str
    skuPrices: List[float]
    unitPrices: List[float]
    productCount: int
    stats: Dict[str, PriceStatistics]
  
class BrandPriceData(BaseModel):
    name: str
    skuPrices: List[float]
    unitPrices: List[float]
  
class CategoryBrandDistribution(BaseModel):
    category: str
    brands: List[BrandPriceData]
  
class PriceDistributionMetadata(BaseModel):
    filtered_asins_count: int
    calculation_timestamp: str
    timeframe_used: str
    data_source: str = "product_wide_table"
    categories_processed: List[str]
  
# 3. 主响应模型：字段名与前端的 `props` 保持一致
class PriceDistributionResponse(BaseModel):
    priceDistribution: List[CategoryPriceData]
    brandPriceDistribution: List[CategoryBrandDistribution]
    # 为前端兼容性或UI便利性设计的字段
    segmentNames: List[str]
    segmentColors: List[str]
    metadata: PriceDistributionMetadata
```

**后续重构要点**:

- 新图表的Request模型同样继承 `BaseRequestModel`。
- Response模型的设计要**优先考虑前端的实际使用方式**，可以适当扁平化，避免前端进行复杂的转换。
- 如果需要颜色等UI相关的元数据，**建议在后端生成**，以保证一致性。

### 3.3. 服务层设计 (`services.py`)

**核心原则**: 服务类应封装所有数据查询、处理和计算逻辑。

**实际案例 (`PriceDistributionService`)**:

```python
# backend/dashboard/charts/pricing_analysis/services.py
from collections import defaultdict
import numpy as np
from dashboard.charts.filters.asin_filter_service import get_filtered_asins

class PriceDistributionService:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
  
    def get_price_distribution_data(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        # 1. 获取过滤后的ASINs (标准步骤)
            filtered_asins = get_filtered_asins(self.supabase, request)
        if not filtered_asins:
            return self._get_empty_response(request) # 健壮性处理

        # 2. 分页查询原始数据 (性能优化)
        products_data = self._get_product_pricing_data(filtered_asins)
        if not products_data:
            return self._get_empty_response(request)

        # 3. 核心业务逻辑 (拆分私有方法)
        category_price_data = self._calculate_category_price_distributions(products_data)
        brand_price_distributions = self._calculate_brand_price_distributions(products_data)

        # 4. 构建最终响应
        return self._format_response(category_price_data, brand_price_distributions, request)

    def _get_product_pricing_data(self, asins: List[str]) -> List[Dict[str, Any]]:
        # 实现包含分页逻辑的数据查询
        ...

    def _calculate_category_price_distributions(self, products_data: List[Dict[str, Any]]) -> List[CategoryPriceData]:
        # 实现价格分布和统计计算
        ...

    def _calculate_brand_price_distributions(self, products_data: List[Dict[str, Any]]) -> List[CategoryBrandDistribution]:
        # 实现按品牌的分布计算
        ...
      
    def _calculate_price_statistics(self, prices: List[float]) -> PriceStatistics:
        # 使用numpy进行统计计算
        ...

    def _format_response(...) -> PriceDistributionResponse:
        # 统一构建响应，包括生成颜色等UI元数据
        ...

    def _get_empty_response(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        # 提供一个标准的空响应结构
        ...
```

**后续重构要点**:

- **必须**使用 `get_filtered_asins` 作为获取数据的起点。
- 对于可能返回大量数据的查询，**必须**实现分页逻辑 (`_get_..._data`)。
- 复杂的业务逻辑应拆分为独立的私有方法，提高可读性。
- **必须**提供一个 `_get_empty_response` 方法来优雅地处理无数据的情况。

### 3.4. API路由集成 (`charts/api.py`)

**核心原则**: 所有图表API都在 `charts/api.py` 中统一注册，使用POST方法，并有完整的错误处理和日志记录。

**实际案例 (`Price Distribution`)**:

```python
# backend/dashboard/charts/api.py
from .pricing_analysis.models import PriceDistributionRequest, PriceDistributionResponse
from .pricing_analysis.services import PriceDistributionService

# 注意路由路径的简洁性
@router.post("/price-distribution", response_model=PriceDistributionResponse)
async def get_price_distribution(request: PriceDistributionRequest):
    """
    Get price distribution analysis data.
    (完整的API文档说明...)
    """
    try:
        logger.info(f"💰 Starting Price Distribution analysis for project {request.project_id}")
      
        from core.database.connection import get_supabase_client
        supabase = get_supabase_client()
      
        service = PriceDistributionService(supabase)
        response = service.get_price_distribution_data(request)
  
        logger.info(f"Price Distribution analysis completed for project {request.project_id}")
        return response
  
    except ValueError as e:
        logger.error(f"Validation error in Price Distribution analysis: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"System error in Price Distribution analysis: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")
```

**后续重构要点**:

- 路由路径应简洁且能清晰反映其功能，如 `/price-trend`。
- 必须包含 `try...except` 块，捕获 `ValueError` (400) 和 `Exception` (500)。
- 在关键步骤使用 `logger` 记录日志，便于调试。

## 4. 🚀 前端重构实施方案 (标准模板)

### 4.1. 数据服务集成 (`database-service.ts`)

**核心原则**: 在 `DatabaseService` 类中为每个API端点添加一个对应的数据获取方法。

**实际案例 (`getPriceDistributionData`)**:

```typescript
// frontend/src/components/analysis-db/data/database-service.ts
import { CHART_NAMES } from '../constants'
import { filterStateManager } from '../stores'

export class DatabaseService {
  
  // 从状态管理器获取过滤器，这是标准模式
  private getFiltersFromState(chartName: string) { ... }

  // 为新图表添加方法
  async getPriceDistributionData(projectId: string): Promise<any> { // 注意：类型为 any 是一个待改进点
    try {
      // 1. 从状态管理器获取过滤器
    const filters = this.getFiltersFromState(CHART_NAMES.PRICE_ANALYSIS)

      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
  
    const requestBody = {
      project_id: projectId,
        ...filters // 直接展开状态管理器的结果
    }
  
      // 2. 调用后端API
      const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/price-distribution`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(requestBody)
    })
  
    if (!response.ok) {
      throw new Error(`Price Distribution API call failed: ${response.status}`)
    }
  
    return await response.json()
  } catch (error) {
    console.error('Error fetching Price Distribution data:', error)
    throw error
  }
}
}

export const databaseService = new DatabaseService()
```

**后续重构要点**:

- **必须**使用 `getFiltersFromState` 从全局状态管理器获取过滤参数。
- **强烈建议**：为 `Promise<any>` 定义准确的TypeScript接口，与后端 `Response` 模型保持同步，消除 `any` 类型。
- 保留旧的数据获取方法（如 `getPricingAnalysisDataByProject`）直到所有相关图表都重构完毕，然后统一移除。

### 4.2. 数据刷新Hook创建 (`use-chart-data-refresh.ts`)

**核心原则**: 为每个数据服务方法创建一个对应的、可复用的数据刷新Hook。

**实际案例 (`usePriceDistributionDataRefresh`)**:

```typescript
// frontend/src/components/analysis-db/hooks/use-chart-data-refresh.ts
import { useChartDataRefresh, ChartDataRefreshConfig } from './use-chart-data-refresh' // 假设基础Hook已存在

// 为新图表创建专用Hook
export function usePriceDistributionDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'price-distribution', // 与CHART_NAMES中的常量对应
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      // 动态导入service，避免循环依赖
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getPriceDistributionData(projectId)
    }
  })
}
```

**后续重构要点**:

- 每个新图表都应有自己的 `use{ChartName}DataRefresh` Hook。
- `chartId` 应与 `CHART_NAMES` 常量保持一致。
- `refreshFunction` **必须**调用 `databaseService` 中对应的方法。

### 4.3. 组件重构 (`pricing-analysis/index.tsx`)

**核心原则**: 使用 `FilterRenderer` 和新建的 `Hook` 来重构组件，实现统一的交互和状态管理。

**实际案例 (`PricingAnalysis` 复合组件)**:

`Price Distribution` 的实现是一个复合组件，它内部管理了多个图表。这是一个常见的模式，可供其他复杂分析页面参考。

```typescript
// frontend/src/components/analysis-db/pricing-analysis/index.tsx
import { FilterRenderer } from "@/components/analysis-db/filters"
import { usePriceDistributionDataRefresh } from "@/components/analysis-db/hooks/use-chart-data-refresh"
import { CHART_NAMES } from "@/components/analysis-db/constants"
import { LoadingState, ErrorState } from "@/components/analysis-db/shared/states" // 假设的加载和错误组件

// 子组件，拥有自己的过滤器
function PriceDistributionByTypeChart({ projectId, priceDataLoading, refreshPriceData }) {
  const { filters, handleFiltersChange, handleFiltersReady } = usePricingAnalysisFilters(...)
  
  return (
    <div data-chart-id={CHART_NAMES.PRICE_ANALYSIS}>
      <FilterRenderer
        chartName={CHART_NAMES.PRICE_ANALYSIS}
        projectId={projectId}
        onChange={handleFiltersChange}
        // ...其他props
      />
      {/* 图表内容... */}
    </div>
  )
}

// 主容器组件
export function PricingAnalysis({ data: initialData, projectId, initialFilters }: PricingAnalysisProps) {
  // 1. 使用统一的Hook获取数据、加载和错误状态
  const {
    data: priceDistributionData,
    loading: priceDataLoading,
    error: priceDataError,
    refreshData: refreshPriceData
  } = usePriceDistributionDataRefresh(projectId || '', initialData)

  // 2. 处理无数据、加载、错误等状态
  if (priceDataLoading) return <LoadingState />
  if (priceDataError) return <ErrorState error={priceDataError} onRetry={() => refreshPriceData(...)} />
  if (!priceDistributionData) return <p>No data available.</p>

  // 3. 渲染子组件，并将数据和方法传递下去
  return (
    <section>
      <PriceDistributionByTypeChart 
        priceDistributionData={priceDistributionData}
        priceDataLoading={priceDataLoading}
        refreshPriceData={refreshPriceData}
        // ...其他props
      />
      {/* 其他图表... */}
    </section>
  )
}
```

**后续重构要点**:

- **必须**使用 `FilterRenderer` 代替旧的过滤器。
- **必须**使用 `use{ChartName}DataRefresh` Hook 来管理数据流。
- **必须**在UI中处理 `loading` 和 `error` 状态，提供清晰的用户反馈。
- 如果一个分析页面包含多个图表，可以采用“容器组件 + 子图表组件”的模式，由容器组件统一获取数据，然后分发给子组件。

### 4.4. 配置更新

1. **`frontend/src/components/analysis-db/constants/chart-names.ts`**:

   - 确保为新图表添加常量，如 `PRICE_TREND: 'price-trend'`。
2. **`frontend/src/components/analysis-db/configs/chart-filter-data.ts`**:

   - 为新图表配置可见的过滤器和默认值。

## 📊 目录结构对比分析

## 🔍 参数一致性对比分析

### 重构前后细节参数对比表

| 参数/选项                                              | 重构前（当前实现）                                                | 重构后（新设计）                     | 一致性  | 备注             |
| ------------------------------------------------------ | ----------------------------------------------------------------- | ------------------------------------ | ------- | ---------------- |
| **组件Props**                                    |                                                                   |                                      |         |                  |
| `data.priceDistribution`                             | `Array<{category, skuPrices, unitPrices, productCount, stats}>` | `Array<CategoryPriceData>`         | ✅ 一致 | 结构完全一致     |
| `data.brandPriceDistribution`                        | `Array<{category, brands}>`                                     | `Array<CategoryBrandDistribution>` | ✅ 一致 | 结构完全一致     |
| `projectId`                                          | `string \| undefined`                                            | `string \| undefined`               | ✅ 一致 | 参数类型一致     |
| `initialFilters`                                     | `ProjectFilters \| undefined`                                    | `ProjectFilters \| undefined`       | ✅ 一致 | 参数类型一致     |
| **价格类型**                                     |                                                                   |                                      |         |                  |
| `PriceType`                                          | `'sku' \| 'unit'`                                                | `'sku' \| 'unit'`                   | ✅ 一致 | 保持原有选项     |
| `priceType` 默认值                                   | `'unit'`                                                        | `'unit'`                           | ✅ 一致 | 默认值不变       |
| **统计数据结构**                                 |                                                                   |                                      |         |                  |
| `stats.sku`                                          | `{min, q1, median, mean, q3, max}`                              | `PriceStatistics`                  | ✅ 一致 | 字段名称完全一致 |
| `stats.unit`                                         | `{min, q1, median, mean, q3, max}`                              | `PriceStatistics`                  | ✅ 一致 | 字段名称完全一致 |
| **图表组件**                                     |                                                                   |                                      |         |                  |
| `PriceTypeSelector`                                  | ✅ 使用                                                           | ✅ 使用                              | ✅ 一致 | 保持原有组件     |
| `BrandViolinChart`                                   | ✅ 使用                                                           | ✅ 使用                              | ✅ 一致 | 保持原有组件     |
| `MultiSegmentViolinChart`                            | ✅ 使用                                                           | ✅ 使用                              | ✅ 一致 | 保持原有组件     |
| **颜色配置**                                     |                                                                   |                                      |         |                  |
| `getChartColor(index)`                               | ✅ 使用                                                           | ✅ 使用                              | ✅ 一致 | 保持颜色一致性   |
| **后端数据处理**                                 |                                                                   |                                      |         |                  |
| `_categorize_products_by_category_smart_combination` | ✅ 存在                                                           | ✅ 迁移                              | ✅ 一致 | 逻辑完全迁移     |
| `_filter_combinations_by_request`                    | ✅ 存在                                                           | ✅ 迁移                              | ✅ 一致 | 逻辑完全迁移     |
| `_format_combination_pricing_response`               | ✅ 存在                                                           | ✅ 迁移                              | ✅ 一致 | 逻辑完全迁移     |
| `calculate_price_stats`                              | ✅ 存在                                                           | ✅ 迁移                              | ✅ 一致 | 统计计算逻辑不变 |
| **数据获取方式**                                 |                                                                   |                                      |         |                  |
| 数据源                                                 | `product_wide_table`                                            | `product_wide_table`               | ✅ 一致 | 数据源不变       |
| 过滤器集成                                             | 手动处理                                                          | `get_filtered_asins`               | ✅ 升级 | 集成统一过滤器   |
| **响应格式**                                     |                                                                   |                                      |         |                  |
| `priceDistribution`                                  | `Array`                                                         | `data.category_distributions`      | ✅ 一致 | 结构化命名       |
| `brandPriceDistribution`                             | `Array`                                                         | `data.brand_distributions`         | ✅ 一致 | 结构化命名       |
| `totalProducts`                                      | `number`                                                        | `data.total_products`              | ✅ 一致 | 字段名一致       |

### 新增参数和功能

| 新增项                      | 描述                                                 | 目的                 |
| --------------------------- | ---------------------------------------------------- | -------------------- |
| `analysis_type`           | `'distribution' \| 'comparison' \| 'brand_analysis'` | 支持多种分析类型     |
| `include_brand_breakdown` | `boolean`                                          | 控制是否包含品牌细分 |
| `metadata`                | 完整的元数据                                         | 提供分析上下文信息   |
| `calculation_timestamp`   | 计算时间戳                                           | 用于缓存和调试       |

## 🔄 架构一致性检查表

### 与TAM饼图架构对比检查

| 修改项                 | TAM饼图实现                                      | Price Distribution设计                           | 一致性  | 备注               |
| ---------------------- | ------------------------------------------------ | ------------------------------------------------ | ------- | ------------------ |
| **后端架构**     |                                                  |                                                  |         |                    |
| 模块目录               | `charts/market_analysis/`                      | `charts/pricing_analysis/`                     | ✅ 一致 | 相同的模块化结构   |
| 数据模型文件           | `models.py`                                    | `models.py`                                    | ✅ 一致 | 相同的文件名       |
| 服务类文件             | `service.py`                                   | `service.py`                                   | ✅ 一致 | 相同的文件名       |
| API文档                | `README.md`                                    | `README.md`                                    | ✅ 一致 | 相同的文档结构     |
| **数据模型设计** |                                                  |                                                  |         |                    |
| Request模型            | `TAMMarketShareRequest(BaseRequestModel)`      | `PriceDistributionRequest(BaseRequestModel)`   | ✅ 一致 | 继承相同的基类     |
| Response模型           | `TAMMarketShareResponse`                       | `PriceDistributionResponse`                    | ✅ 一致 | 相同的结构设计     |
| 元数据模型             | `TAMMarketShareMetadata`                       | `PriceDistributionMetadata`                    | ✅ 一致 | 相同的元数据结构   |
| **服务类设计**   |                                                  |                                                  |         |                    |
| 服务类名               | `TAMMarketShareService`                        | `PriceDistributionService`                     | ✅ 一致 | 相同的命名规范     |
| 初始化方法             | `__init__(self, supabase_client)`              | `__init__(self, supabase_client)`              | ✅ 一致 | 相同的初始化参数   |
| 主方法名               | `get_tam_market_share_data`                    | `get_price_distribution_data`                  | ✅ 一致 | 相同的命名模式     |
| 过滤器集成             | `get_filtered_asins(self.supabase, request)`   | `get_filtered_asins(self.supabase, request)`   | ✅ 一致 | 相同的过滤器服务   |
| **API路由设计**  |                                                  |                                                  |         |                    |
| 路由路径               | `/market-analysis/tam-market-share`            | `/pricing-analysis/price-distribution`         | ✅ 一致 | 相同的路径结构     |
| 装饰器                 | `@router.post(..., response_model=...)`        | `@router.post(..., response_model=...)`        | ✅ 一致 | 相同的装饰器用法   |
| 错误处理               | `ValueError` -> 400, `Exception` -> 500      | `ValueError` -> 400, `Exception` -> 500      | ✅ 一致 | 相同的错误处理逻辑 |
| 日志记录               | `logger.info/error`                            | `logger.info/error`                            | ✅ 一致 | 相同的日志级别     |
| **前端架构**     |                                                  |                                                  |         |                    |
| 组件路径               | `market-analysis/brand-analysis.tsx`           | `market-analysis/pricing-analysis.tsx`         | ✅ 一致 | 相同的目录结构     |
| 过滤器组件             | `FilterRenderer`                               | `FilterRenderer`                               | ✅ 一致 | 相同的过滤器组件   |
| 数据刷新Hook           | `useTAMDataRefresh`                            | `usePriceDistributionDataRefresh`              | ✅ 一致 | 相同的Hook模式     |
| 数据服务方法           | `getTAMMarketShareData`                        | `getPriceDistributionData`                     | ✅ 一致 | 相同的命名规范     |
| **过滤器配置**   |                                                  |                                                  |         |                    |
| 配置常量               | `CHART_NAMES.MARKET_SHARE_ANALYSIS`            | `CHART_NAMES.PRICE_ANALYSIS`                   | ✅ 一致 | 相同的常量结构     |
| 配置结构               | `{chart_id, chart_type, visible_filters, ...}` | `{chart_id, chart_type, visible_filters, ...}` | ✅ 一致 | 相同的配置结构     |
| project_id处理         | 动态设置（函数中）                               | 动态设置（函数中）                               | ✅ 一致 | 相同的动态设置方式 |
| **状态管理**     |                                                  |                                                  |         |                    |
| loading状态            | `loading: boolean`                             | `loading: boolean`                             | ✅ 一致 | 相同的状态类型     |
| error状态              | `error: string \| null`                         | `error: string \| null`                         | ✅ 一致 | 相同的错误处理     |
| data状态               | `data: TAMMarketShareResponse`                 | `data: PriceDistributionResponse`              | ✅ 一致 | 相同的数据类型结构 |

### 重点检查项

✅ **完全一致的项目**：

- 后端模块化结构
- API路由设计和错误处理
- 前端组件目录结构
- 过滤器组件和配置
- 数据刷新Hook模式
- 状态管理方式

⚠️ **需要特别注意的项目**：

- 保持原有的所有参数和选项
- 保持原有的图表组件功能
- 保持原有的数据结构和计算逻辑

### TAM饼图 vs Price Distribution 目录结构对比

#### 后端目录结构对比

**TAM饼图（标准模板）：**

```
backend/dashboard/charts/market_analysis/
├── __init__.py                    # 模块导出
├── models.py                      # TAMMarketShareRequest/Response等
├── service.py                     # TAMMarketShareService类
└── README.md                      # API文档
```

**Price Distribution（当前状态）：**

```
backend/dashboard/services/
└── pricing_analysis_service.py    # 单文件，混合逻辑

backend/dashboard/models.py         # 通用模型文件中的Price相关模型
```

**Price Distribution（重构目标）：**

```
backend/dashboard/charts/pricing_analysis/
├── __init__.py                    # 模块导出
├── models.py                      # PriceDistributionRequest/Response等
├── service.py                     # PriceDistributionService类
└── README.md                      # API文档
```

#### 前端目录结构对比

**TAM饼图（标准模板）：**

```
frontend/src/components/analysis-db/
├── market-analysis/
│   └── brand-analysis.tsx         # TAM饼图集成在此组件中
├── hooks/
│   └── use-chart-data-refresh.ts  # useTAMDataRefresh Hook
├── data/
│   └── database-service.ts        # getTAMMarketShareData方法
└── configs/
    └── chart-filter-data.ts       # MARKET_SHARE_ANALYSIS配置
```

**Price Distribution（当前状态）：**

```
frontend/src/components/analysis-db/
├── market-analysis/
│   └── pricing-analysis.tsx       # 使用ChartWithFilters
├── data/
│   └── database-service.ts        # getPricingAnalysisDataByProject方法
└── （缺失专用Hook和过滤器配置）
```

**Price Distribution（重构目标）：**

```
frontend/src/components/analysis-db/
├── pricing-analysis
│   └── pricing-analysis.tsx       # 重构为FilterRenderer模式
├── hooks/
│   └── use-chart-data-refresh.ts  # 新增usePriceDistributionDataRefresh
├── data/
│   └── database-service.ts        # 新增getPriceDistributionData方法
└── configs/
    └── chart-filter-data.ts       # 新增PRICE_ANALYSIS配置
```

### 架构一致性分析

| 组件                   | TAM饼图                            | Price Distribution（当前）           | Price Distribution（目标）            | 一致性          |
| ---------------------- | ---------------------------------- | ------------------------------------ | ------------------------------------- | --------------- |
| **后端模块结构** | ✅ 模块化                          | ❌ 分散化                            | ✅ 模块化                             | ✅ 完全一致     |
| **API路由管理**  | ✅ 统一在charts/api.py             | ❌ 缺失                              | ✅ 统一在charts/api.py                | ✅ 完全一致     |
| **前端组件路径** | market-analysis/brand-analysis.tsx | market-analysis/pricing-analysis.tsx | pricing-analysis/pricing-analysis.tsx | ✅ 路径一致     |
| **数据获取方法** | getTAMMarketShareData              | getPricingAnalysisDataByProject      | getPriceDistributionData              | ✅ 命名规范一致 |
| **过滤器组件**   | FilterRenderer                     | ChartWithFilters                     | FilterRenderer                        | ✅ 完全一致     |
| **数据刷新Hook** | useTAMDataRefresh                  | 无                                   | usePriceDistributionDataRefresh       | ✅ 模式一致     |

## 📁 文件修改清单

### 需要新建的文件

#### 后端新建文件

1. **`backend/dashboard/charts/pricing_analysis/__init__.py`**

   ```python
   """Pricing Analysis Chart Module"""

   from .models import (
       PriceDistributionRequest,
       PriceDistributionResponse,
       PriceDistributionData,
       PriceDistributionMetadata
   )
   from .service import PriceDistributionService

   __all__ = [
       'PriceDistributionRequest',
       'PriceDistributionResponse', 
       'PriceDistributionData',
       'PriceDistributionMetadata',
       'PriceDistributionService'
   ]
   ```
2. **`backend/dashboard/charts/pricing_analysis/models.py`**

   - 完整的Pydantic数据模型定义
   - 包含Request、Response、Data、Metadata等所有模型
   - 支持多种分析类型和价格类型
   - 包含详细的字段说明和示例
3. **`backend/dashboard/charts/pricing_analysis/service.py`**

   - `PriceDistributionService`主服务类
   - 集成统一的过滤器服务 `get_filtered_asins`
   - 完整的数据处理和统计计算逻辑
   - 标准化的错误处理和日志记录
4. **`backend/dashboard/charts/pricing_analysis/README.md`**

   ```markdown
   # Price Distribution Analysis API

   ## 概述
   价格分布分析API，提供产品价格分布、统计分析和品牌对比功能。

   ## API端点
   - `POST /api/v1/dashboard/charts/pricing-analysis/price-distribution`

   ## 请求参数
   - analysis_type: 分析类型
   - price_type: 价格类型
   - 完整的过滤器支持

   ## 响应格式
   - 详细的价格分布数据
   - 统计信息和元数据

   ## 使用示例
   [详细的API使用示例]
   ```

### 需要修改的文件

#### 后端修改文件

1. **`backend/dashboard/charts/api.py`**
   - **修改内容**：添加Price Distribution的API路由
   - **具体操作**：
     - 添加模型导入：`from .pricing_analysis.models import ...`
     - 添加服务导入：`from .pricing_analysis.service import PriceDistributionService`
     - 添加路由定义：`@router.post("/pricing-analysis/price-distribution")`
     - 完整的错误处理和日志记录

#### 前端修改文件

2. **`frontend/src/components/analysis-db/data/database-service.ts`**

   - **修改内容**：添加 `getPriceDistributionData`方法
   - **具体操作**：
     - 集成过滤器状态管理器
     - 标准化的API调用逻辑
     - 完整的错误处理
3. **`frontend/src/components/analysis-db/hooks/use-chart-data-refresh.ts`**

   - **修改内容**：添加 `usePriceDistributionDataRefresh` Hook
   - **具体操作**：
     - 使用 `useChartDataRefresh`基础Hook
     - 集成新的数据获取方法
     - 支持过滤器变化时自动刷新
4. **`frontend/src/components/analysis-db/pricing-analysis/pricing-analysis.tsx`**

   - **修改内容**：完全重构组件实现
   - **具体操作**：
     - 替换 `ChartWithFilters`为 `FilterRenderer`
     - 集成新的数据刷新Hook
     - 添加统一的状态管理
     - 保持现有的图表功能
     - 保持与 `brand-analysis.tsx`相同的目录结构
5. **`frontend/src/components/analysis-db/configs/chart-filter-data.ts`**

   - **修改内容**：添加Price Analysis的过滤器配置
   - **具体操作**：
     - 添加 `CHART_NAMES.PRICE_ANALYSIS`配置项
     - 定义可见过滤器和默认值
     - 配置扩展字段选项
6. **`frontend/src/components/analysis-db/constants/chart-names.ts`**

   - **修改内容**：确保 `PRICE_ANALYSIS`常量存在
   - **具体操作**：
     - 验证 `PRICE_ANALYSIS: 'price-analysis'`定义
     - 更新相关的显示名称和描述
   - **注意**：project_id在配置函数中动态设置，与TAM保持一致

## 5. 🧪 测试与验证策略

### 5.1. 后端API测试

- **功能测试**: 使用 `curl` 或API测试工具，覆盖所有参数组合（特别是过滤器）。
- **边界测试**: 测试无匹配结果、空过滤器等情况，确保返回 `_get_empty_response` 的内容。
- **数据一致性验证**: 手动编写SQL查询，对比API返回的数据与数据库中的原始数据，确保统计计算的准确性。

### 5.2. 前端组件测试

- **渲染测试**: 验证 `FilterRenderer` 和图表组件在不同数据状态下（有数据、无数据、加载中、错误）的渲染是否正确。
- **数据流测试**: 验证过滤器变化时，是否正确触发 `refreshData`，以及数据是否成功更新。
- **集成测试**: 确保 `FilterRenderer`、`Hook` 和图表组件之间的协同工作没有问题。

## 6. 🚨 重要注意事项与经验总结

- **代码清理**: 在整个 **价格分析（Pricing Analysis）** 模块重构完成之前，**不要**删除任何旧的代码（如 `pricing_analysis_service.py` 或 `getPricingAnalysisDataByProject`），以避免破坏尚未重构的图表。清理工作应在所有图表迁移至新架构后统一进行。
- **前后端类型同步**: 这是一个关键的质量保证环节。后端Pydantic模型更新后，应及时在前端 `types` 目录下更新对应的TypeScript接口，并应用到 `database-service` 和组件 `props` 中，彻底消灭 `any` 类型。
- **本地Hook的使用**: 在重构过程中，可能会出现一些过渡性的本地Hook（如 `usePricingAnalysisFilters`）。这在开发阶段是允许的，但最终目标应该是将通用逻辑沉淀到全局的、可复用的Hook中。

## 7. 📈 子图表重构方案：Price vs Revenue 散点图 & Brand Price Distribution

### 7.1. 当前架构分析

基于对现有代码的深入分析，`PricingAnalysis` 组件内包含两个需要独立重构的子图表：

#### 7.1.1. Price vs Revenue Distribution of Top Selling 20 Products (散点图)

**当前实现特点**:
- **数据依赖**: 依赖 `getProductAnalysisDataByProject()` 获取 `topProducts` 数据
- **数据处理**: 在前端组件中通过 `getPriceVsRevenueData()` 函数处理散点图数据
- **过滤器状态**: 共享父组件的 `priceDistributionData`，没有独立的过滤器
- **交互功能**: 支持点击跳转到Amazon产品页面

**与TAM/Pricing对比**:
- ❌ **数据源分离**: 使用不同的API端点 (`product-analysis` vs `price-distribution`)
- ❌ **状态管理**: 没有独立的数据刷新机制
- ✅ **渲染逻辑**: 使用标准的Recharts组件，与其他图表一致

#### 7.1.2. Brand Price Distribution (品牌小提琴图)

**当前实现特点**:
- **数据依赖**: 使用 `priceDistributionData.brandPriceDistribution`
- **组件架构**: 使用独立的 `BrandViolinChart` 组件
- **过滤器集成**: 每个品牌小提琴图都有独立的过滤器逻辑
- **智能分类处理**: 支持 `Smart/Non-Smart` 的扩展字段过滤

**与TAM/Pricing对比**:
- ✅ **数据源统一**: 使用相同的 `price-distribution` API
- ✅ **组件独立**: `BrandViolinChart` 是独立的可复用组件
- ⚠️ **过滤器复杂**: 每个小提琴图都有自己的过滤逻辑，可能过于复杂

### 7.2. 重构策略与步骤

#### 7.2.1. Price vs Revenue 散点图重构方案

**步骤1: 后端数据整合**
- **目标**: 将散点图所需的 `topProducts` 数据整合到 `PriceDistributionResponse` 中
- **修改位置**: `backend/dashboard/charts/pricing_analysis/models.py`
- **具体操作**:
  ```python
  # 在 PriceDistributionResponse 中添加
  class PriceDistributionResponse(BaseModel):
      # ... 现有字段
      topProducts: Optional[TopProductsData] = None  # 新增散点图数据
      
  class TopProductsData(BaseModel):
      segments: Dict[str, List[ProductDetail]]
      dimmerSwitches: List[ProductDetail]  # 兼容性字段
      lightSwitches: List[ProductDetail]   # 兼容性字段
      
  class ProductDetail(BaseModel):
      id: str
      name: str
      brand: str
      price: float
      unitPrice: float
      revenue: float
      volume: float
      url: str
  ```

**步骤2: 后端服务扩展**
- **目标**: 在 `PriceDistributionService` 中集成产品分析逻辑
- **修改位置**: `backend/dashboard/charts/pricing_analysis/services.py`
- **具体操作**:
  ```python
  class PriceDistributionService:
      def get_price_distribution_data(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
          # ... 现有逻辑
          
          # 新增: 获取散点图数据
          top_products_data = self._get_top_products_data(filtered_asins)
          
          return self._format_response(
              category_price_data, 
              brand_price_distributions, 
              top_products_data,  # 新增参数
              request
          )
      
      def _get_top_products_data(self, filtered_asins: List[str]) -> Optional[TopProductsData]:
          # 集成ProductAnalysisService的核心逻辑
          # 获取segment assignments和产品数据
          # 按收入排序并返回Top 20产品
  ```

**步骤3: 前端数据流简化**
- **目标**: 移除对 `getProductAnalysisDataByProject` 的依赖
- **修改位置**: `frontend/src/components/analysis-db/pricing-analysis/index.tsx`
- **具体操作**:
  ```typescript
  // 移除这部分逻辑
  const topProductsData = priceDistributionData?.topProducts || initialData?.topProducts
  
  // 改为直接使用统一数据源
  const scatterData = useMemo(() => {
    return priceDistributionData?.topProducts ? 
      processScatterData(priceDistributionData.topProducts) : []
  }, [priceDistributionData])
  ```

**与参考架构的异同对比**:
- **与TAM相同**: ✅ 使用统一的API端点和数据刷新机制
- **与TAM不同**: ⚠️ 散点图的交互性更强，包含产品详情和跳转功能
- **与Pricing相同**: ✅ 作为 `PricingAnalysis` 的子组件，共享过滤器状态
- **与Pricing不同**: ⚠️ 数据处理逻辑更复杂，需要产品排序和Top N筛选

#### 7.2.2. Brand Price Distribution 重构方案

**步骤1: 组件架构优化**
- **目标**: 简化 `BrandViolinChart` 的过滤器逻辑
- **修改位置**: `frontend/src/components/analysis-db/charts/brand-violin-chart.tsx`
- **具体操作**:
  ```typescript
  // 简化props，移除复杂的filterMode逻辑
  interface BrandViolinChartProps {
    brands: BrandPriceData[]
    priceType: PriceType
    category: string
    projectId: string
    // 移除: filterMode, extendFieldsConfig
  }
  ```

**步骤2: 过滤器逻辑上移**
- **目标**: 将复杂的过滤器逻辑移到父组件中处理
- **修改位置**: `frontend/src/components/analysis-db/pricing-analysis/index.tsx`
- **具体操作**:
  ```typescript
  // 在父组件中处理Smart/Non-Smart分类
  const processedBrandData = useMemo(() => {
    return currentData?.brandPriceDistribution?.map(categoryData => ({
      ...categoryData,
      // 在这里处理分类逻辑，而不是在BrandViolinChart中
    }))
  }, [currentData])
  ```

**步骤3: 数据结构标准化**
- **目标**: 确保 `brandPriceDistribution` 数据结构与后端模型完全一致
- **修改位置**: 前后端数据模型同步
- **具体操作**: 验证 `CategoryBrandDistribution` 和前端使用的数据结构是否匹配

**与参考架构的异同对比**:
- **与TAM相同**: ✅ 使用统一的数据源和刷新机制
- **与TAM不同**: ⚠️ 支持多个分类的品牌分布，TAM只有单一饼图
- **与Pricing相同**: ✅ 作为子组件，继承父组件的过滤器状态
- **与Pricing不同**: ⚠️ 具有独立的交互逻辑（点击品牌查看产品详情）

### 7.3. 实施优先级与风险评估

#### 7.3.1. 优先级排序

1. **高优先级 - Brand Price Distribution**
   - **理由**: 已经使用统一的数据源，重构风险较低
   - **预计工期**: 2-3天
   - **主要工作**: 简化组件逻辑，优化过滤器处理

2. **中优先级 - Price vs Revenue 散点图**
   - **理由**: 需要后端数据整合，工作量较大
   - **预计工期**: 5-7天
   - **主要工作**: 后端API扩展，前端数据流重构

#### 7.3.2. 风险评估

**Brand Price Distribution**:
- **低风险**: 数据源已统一，主要是代码优化
- **潜在问题**: 过滤器逻辑简化后可能影响Smart/Non-Smart分类显示
- **缓解措施**: 保留现有逻辑作为备用，逐步迁移

**Price vs Revenue 散点图**:
- **中等风险**: 涉及后端API修改和数据整合
- **潜在问题**: 
  - 性能影响：在price-distribution API中集成更多数据可能影响响应时间
  - 数据一致性：需要确保散点图数据与原product-analysis API返回的数据一致
- **缓解措施**: 
  - 实施分阶段重构，先保留双API调用，验证数据一致性后再移除旧API
  - 添加性能监控，确保API响应时间在可接受范围内

### 7.4. 测试验证清单

#### 7.4.1. Brand Price Distribution 测试
- [ ] 验证所有分类的品牌分布正确显示
- [ ] 验证Smart/Non-Smart分类逻辑正确工作
- [ ] 验证Price Type切换功能正常
- [ ] 验证品牌点击交互功能
- [ ] 验证过滤器变化时数据正确更新

#### 7.4.2. Price vs Revenue 散点图测试
- [ ] 验证散点图显示Top 20产品
- [ ] 验证产品按收入正确排序
- [ ] 验证点击产品跳转到Amazon页面
- [ ] 验证不同过滤器下散点图数据正确变化
- [ ] 验证散点图的Tooltip信息准确
- [ ] 验证API响应时间在可接受范围内（<3秒）

本篇文档融合了理论标准与实践经验，为后续所有价格分析图表的重构工作提供了清晰、可行、高质量的指南。请严格遵循此规范，以确保项目代码的长期健康和可维护性。
