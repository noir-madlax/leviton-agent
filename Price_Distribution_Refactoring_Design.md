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
- ❌ **后端分散**：代码在`services/pricing_analysis_service.py`，非模块化
- ❌ **模型混合**：数据模型定义在通用的`dashboard/models.py`中
- ❌ **缺失API**：没有在`charts/api.py`中注册统一路由
- ❌ **前端老旧**：使用`ChartWithFilters`而非`FilterRenderer`
- ❌ **数据服务缺失**：`database-service.ts`中没有对应方法
- ❌ **状态管理不统一**：缺乏标准化的状态处理

### 目标架构（TAM饼图标准）
- ✅ **模块化结构**：`backend/dashboard/charts/pricing_analysis/`
- ✅ **标准化模型**：完整的Pydantic模型定义
- ✅ **统一服务层**：`PriceDistributionService`类
- ✅ **集成API路由**：在`charts/api.py`中统一管理
- ✅ **现代化前端**：使用`FilterRenderer`和专用Hook
- ✅ **标准化数据服务**：`database-service.ts`中的专门方法
- ✅ **完整状态管理**：统一的loading/error/data状态

## 🏗️ 详细设计方案

### 1. 后端架构设计

#### 1.1 目录结构设计
```
backend/dashboard/charts/pricing_analysis/
├── __init__.py                 # 模块初始化
├── models.py                   # 数据模型定义
├── service.py                  # 业务逻辑服务
└── README.md                   # API文档和使用说明
```

#### 1.2 数据模型设计

**核心模型结构：**
```python
# models.py - 完整的Pydantic模型定义

class PriceDistributionRequest(BaseRequestModel):
    """价格分布分析请求模型"""
    analysis_type: Literal["distribution", "comparison", "brand_analysis"] = "distribution"
    price_type: Literal["sku", "unit"] = "unit"
    include_brand_breakdown: bool = True
    
class PriceStatistics(BaseModel):
    """价格统计数据模型"""
    min: float
    q1: float
    median: float
    mean: float
    q3: float
    max: float
    
class CategoryPriceData(BaseModel):
    """类别价格数据模型"""
    category: str
    sku_prices: List[float]
    unit_prices: List[float]
    product_count: int
    stats: Dict[str, PriceStatistics]  # sku/unit统计
    
class BrandPriceData(BaseModel):
    """品牌价格数据模型"""
    brand: str
    sku_prices: List[float]
    unit_prices: List[float]
    product_count: int
    
class CategoryBrandDistribution(BaseModel):
    """类别-品牌价格分布模型"""
    category: str
    brands: List[BrandPriceData]
    
class PriceDistributionData(BaseModel):
    """价格分布主数据模型"""
    category_distributions: List[CategoryPriceData]
    brand_distributions: List[CategoryBrandDistribution]
    total_products: int
    analysis_type: str
    price_type: str
    
class PriceDistributionMetadata(BaseModel):
    """价格分布元数据模型"""
    filtered_asins_count: int
    total_categories: int
    total_brands: int
    analysis_type: str
    price_type: str
    calculation_timestamp: str
    
class PriceDistributionResponse(BaseModel):
    """价格分布分析响应模型"""
    data: PriceDistributionData
    metadata: PriceDistributionMetadata
```

#### 1.3 服务层设计

**核心服务类：**
```python
# service.py - 业务逻辑实现

class PriceDistributionService:
    """价格分布分析服务类"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def get_price_distribution_data(self, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """获取价格分布分析数据"""
        try:
            # 1. 获取过滤后的ASINs - 使用统一过滤器服务
            filtered_asins = get_filtered_asins(self.supabase, request)
            
            # 2. 从product_wide_table获取产品数据
            product_data = self._get_product_data_from_wide_table(filtered_asins, request)
            
            # 3. 处理价格数据和统计计算
            processed_data = self._process_price_data(product_data, request)
            
            # 4. 生成响应数据
            return self._build_response(processed_data, request)
            
        except Exception as e:
            logger.error(f"Error in price distribution analysis: {e}")
            raise
    
    def _get_product_data_from_wide_table(self, filtered_asins: List[str], request: PriceDistributionRequest):
        """从product_wide_table获取产品数据"""
        # 实现数据查询逻辑
        
    def _process_price_data(self, product_data: List[Dict], request: PriceDistributionRequest):
        """处理价格数据和统计计算"""
        # 实现价格处理和统计逻辑
        
    def _build_response(self, processed_data: Dict, request: PriceDistributionRequest) -> PriceDistributionResponse:
        """构建响应数据"""
        # 实现响应构建逻辑
```

#### 1.4 API路由集成

**在 `charts/api.py` 中添加：**
```python
from .pricing_analysis.models import PriceDistributionRequest, PriceDistributionResponse
from .pricing_analysis.service import PriceDistributionService

@router.post("/pricing-analysis/price-distribution", response_model=PriceDistributionResponse)
async def get_price_distribution(request: PriceDistributionRequest):
    """Get Price Distribution analysis.
    
    完整的API文档说明，包含：
    - 请求参数说明
    - 响应格式说明
    - 错误处理说明
    - 使用示例
    """
    try:
        supabase_client = get_supabase_client()
        service = PriceDistributionService(supabase_client)
        response = service.get_price_distribution_data(request)
        
        logger.info(f"Price Distribution analysis completed for project {request.project_id}")
        return response
        
    except ValueError as e:
        logger.error(f"Validation error in Price Distribution: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"System error in Price Distribution: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

### 2. 前端架构设计

#### 2.1 数据服务集成

**在 `database-service.ts` 中添加：**
```typescript
// 🔑 Get Price Distribution data - 自动从过滤器状态管理器获取过滤器
async getPriceDistributionData(projectId: string): Promise<PriceDistributionResponse> {
  try {
    // 从过滤器状态管理器获取过滤器数据
    const filters = this.getFiltersFromState(CHART_NAMES.PRICE_ANALYSIS)
    
    const requestBody = {
      project_id: projectId,
      ...filters  // 直接展开过滤器状态
    }
    
    const response = await fetch(`${API_BASE_URL}/api/v1/dashboard/charts/pricing-analysis/price-distribution`, {
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
```

#### 2.2 数据刷新Hook创建

**在 `use-chart-data-refresh.ts` 中添加：**
```typescript
// Price Distribution 专用的数据刷新hook
export function usePriceDistributionDataRefresh(projectId: string, initialData?: any) {
  return useChartDataRefresh({
    chartId: 'price-distribution',
    projectId,
    initialData,
    refreshFunction: async (projectId: string, filters: ProjectFilters) => {
      const { databaseService } = await import('@/components/analysis-db/data/database-service')
      return await databaseService.getPriceDistributionData(projectId)
    }
  })
}
```

#### 2.3 组件重构设计

**重构 `market-analysis/pricing-analysis.tsx`：**
```typescript
export function PricingAnalysis({ projectId, initialFilters }: PricingAnalysisProps) {
  // 使用统一的数据刷新Hook
  const {
    data: priceDistributionData,
    loading: dataLoading,
    error: dataError,
    refreshData
  } = usePriceDistributionDataRefresh(projectId)
  
  // 过滤器处理
  const handleFiltersChange = useCallback((newFilters: ProjectFilters) => {
    refreshData(newFilters)
  }, [refreshData])
  
  return (
    <section>
      {/* 使用统一的FilterRenderer */}
      <FilterRenderer
        projectId={projectId || ''}
        chartName="price-analysis"
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
        <PriceDistributionCharts data={priceDistributionData} />
      )}
    </section>
  )
}
```

### 3. 配置和集成设计

#### 3.1 过滤器配置更新

**在 `chart-filter-data.ts` 中添加：**
```typescript
[CHART_NAMES.PRICE_ANALYSIS]: {
  chart_id: CHART_NAMES.PRICE_ANALYSIS,
  chart_type: CHART_NAMES.PRICE_ANALYSIS,
  project_id: 'd2c02b80-4c82-44cc-8093-56708a7883f7', // 动态设置，与TAM一致
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
    name: 'Price Analysis Filter',
    description: '价格分析图表的筛选器配置'
  }
}
```

#### 3.2 图表名称常量更新

**在 `chart-names.ts` 中确保：**
```typescript
export const CHART_NAMES = {
  // 现有的图表...
  PRICE_ANALYSIS: 'price-analysis',  // 确保存在
  // 其他图表...
}
```

## 📊 目录结构对比分析

## 🔍 参数一致性对比分析

### 重构前后细节参数对比表

| 参数/选项 | 重构前（当前实现） | 重构后（新设计） | 一致性 | 备注 |
|------------|------------------|------------------|--------|------|
| **组件Props** |||||
| `data.priceDistribution` | `Array<{category, skuPrices, unitPrices, productCount, stats}>` | `Array<CategoryPriceData>` | ✅ 一致 | 结构完全一致 |
| `data.brandPriceDistribution` | `Array<{category, brands}>` | `Array<CategoryBrandDistribution>` | ✅ 一致 | 结构完全一致 |
| `projectId` | `string \| undefined` | `string \| undefined` | ✅ 一致 | 参数类型一致 |
| `initialFilters` | `ProjectFilters \| undefined` | `ProjectFilters \| undefined` | ✅ 一致 | 参数类型一致 |
| **价格类型** |||||
| `PriceType` | `'sku' \| 'unit'` | `'sku' \| 'unit'` | ✅ 一致 | 保持原有选项 |
| `priceType` 默认值 | `'unit'` | `'unit'` | ✅ 一致 | 默认值不变 |
| **统计数据结构** |||||
| `stats.sku` | `{min, q1, median, mean, q3, max}` | `PriceStatistics` | ✅ 一致 | 字段名称完全一致 |
| `stats.unit` | `{min, q1, median, mean, q3, max}` | `PriceStatistics` | ✅ 一致 | 字段名称完全一致 |
| **图表组件** |||||
| `PriceTypeSelector` | ✅ 使用 | ✅ 使用 | ✅ 一致 | 保持原有组件 |
| `BrandViolinChart` | ✅ 使用 | ✅ 使用 | ✅ 一致 | 保持原有组件 |
| `MultiSegmentViolinChart` | ✅ 使用 | ✅ 使用 | ✅ 一致 | 保持原有组件 |
| **颜色配置** |||||
| `getChartColor(index)` | ✅ 使用 | ✅ 使用 | ✅ 一致 | 保持颜色一致性 |
| **后端数据处理** |||||
| `_categorize_products_by_category_smart_combination` | ✅ 存在 | ✅ 迁移 | ✅ 一致 | 逻辑完全迁移 |
| `_filter_combinations_by_request` | ✅ 存在 | ✅ 迁移 | ✅ 一致 | 逻辑完全迁移 |
| `_format_combination_pricing_response` | ✅ 存在 | ✅ 迁移 | ✅ 一致 | 逻辑完全迁移 |
| `calculate_price_stats` | ✅ 存在 | ✅ 迁移 | ✅ 一致 | 统计计算逻辑不变 |
| **数据获取方式** |||||
| 数据源 | `product_wide_table` | `product_wide_table` | ✅ 一致 | 数据源不变 |
| 过滤器集成 | 手动处理 | `get_filtered_asins` | ✅ 升级 | 集成统一过滤器 |
| **响应格式** |||||
| `priceDistribution` | `Array` | `data.category_distributions` | ✅ 一致 | 结构化命名 |
| `brandPriceDistribution` | `Array` | `data.brand_distributions` | ✅ 一致 | 结构化命名 |
| `totalProducts` | `number` | `data.total_products` | ✅ 一致 | 字段名一致 |

### 新增参数和功能

| 新增项 | 描述 | 目的 |
|--------|------|------|
| `analysis_type` | `'distribution' \| 'comparison' \| 'brand_analysis'` | 支持多种分析类型 |
| `include_brand_breakdown` | `boolean` | 控制是否包含品牌细分 |
| `metadata` | 完整的元数据 | 提供分析上下文信息 |
| `calculation_timestamp` | 计算时间戳 | 用于缓存和调试 |

## 🔄 架构一致性检查表

### 与TAM饼图架构对比检查

| 修改项 | TAM饼图实现 | Price Distribution设计 | 一致性 | 备注 |
|---------|-------------|----------------------|--------|------|
| **后端架构** |||||
| 模块目录 | `charts/market_analysis/` | `charts/pricing_analysis/` | ✅ 一致 | 相同的模块化结构 |
| 数据模型文件 | `models.py` | `models.py` | ✅ 一致 | 相同的文件名 |
| 服务类文件 | `service.py` | `service.py` | ✅ 一致 | 相同的文件名 |
| API文档 | `README.md` | `README.md` | ✅ 一致 | 相同的文档结构 |
| **数据模型设计** |||||
| Request模型 | `TAMMarketShareRequest(BaseRequestModel)` | `PriceDistributionRequest(BaseRequestModel)` | ✅ 一致 | 继承相同的基类 |
| Response模型 | `TAMMarketShareResponse` | `PriceDistributionResponse` | ✅ 一致 | 相同的结构设计 |
| 元数据模型 | `TAMMarketShareMetadata` | `PriceDistributionMetadata` | ✅ 一致 | 相同的元数据结构 |
| **服务类设计** |||||
| 服务类名 | `TAMMarketShareService` | `PriceDistributionService` | ✅ 一致 | 相同的命名规范 |
| 初始化方法 | `__init__(self, supabase_client)` | `__init__(self, supabase_client)` | ✅ 一致 | 相同的初始化参数 |
| 主方法名 | `get_tam_market_share_data` | `get_price_distribution_data` | ✅ 一致 | 相同的命名模式 |
| 过滤器集成 | `get_filtered_asins(self.supabase, request)` | `get_filtered_asins(self.supabase, request)` | ✅ 一致 | 相同的过滤器服务 |
| **API路由设计** |||||
| 路由路径 | `/market-analysis/tam-market-share` | `/pricing-analysis/price-distribution` | ✅ 一致 | 相同的路径结构 |
| 装饰器 | `@router.post(..., response_model=...)` | `@router.post(..., response_model=...)` | ✅ 一致 | 相同的装饰器用法 |
| 错误处理 | `ValueError` -> 400, `Exception` -> 500 | `ValueError` -> 400, `Exception` -> 500 | ✅ 一致 | 相同的错误处理逻辑 |
| 日志记录 | `logger.info/error` | `logger.info/error` | ✅ 一致 | 相同的日志级别 |
| **前端架构** |||||
| 组件路径 | `market-analysis/brand-analysis.tsx` | `market-analysis/pricing-analysis.tsx` | ✅ 一致 | 相同的目录结构 |
| 过滤器组件 | `FilterRenderer` | `FilterRenderer` | ✅ 一致 | 相同的过滤器组件 |
| 数据刷新Hook | `useTAMDataRefresh` | `usePriceDistributionDataRefresh` | ✅ 一致 | 相同的Hook模式 |
| 数据服务方法 | `getTAMMarketShareData` | `getPriceDistributionData` | ✅ 一致 | 相同的命名规范 |
| **过滤器配置** |||||
| 配置常量 | `CHART_NAMES.MARKET_SHARE_ANALYSIS` | `CHART_NAMES.PRICE_ANALYSIS` | ✅ 一致 | 相同的常量结构 |
| 配置结构 | `{chart_id, chart_type, visible_filters, ...}` | `{chart_id, chart_type, visible_filters, ...}` | ✅ 一致 | 相同的配置结构 |
| project_id处理 | 动态设置（函数中） | 动态设置（函数中） | ✅ 一致 | 相同的动态设置方式 |
| **状态管理** |||||
| loading状态 | `loading: boolean` | `loading: boolean` | ✅ 一致 | 相同的状态类型 |
| error状态 | `error: string \| null` | `error: string \| null` | ✅ 一致 | 相同的错误处理 |
| data状态 | `data: TAMMarketShareResponse` | `data: PriceDistributionResponse` | ✅ 一致 | 相同的数据类型结构 |

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
├── market-analysis/
│   └── pricing-analysis.tsx       # 重构为FilterRenderer模式
├── hooks/
│   └── use-chart-data-refresh.ts  # 新增usePriceDistributionDataRefresh
├── data/
│   └── database-service.ts        # 新增getPriceDistributionData方法
└── configs/
    └── chart-filter-data.ts       # 新增PRICE_ANALYSIS配置
```

### 架构一致性分析

| 组件 | TAM饼图 | Price Distribution（当前） | Price Distribution（目标） | 一致性 |
|------|---------|---------------------------|---------------------------|--------|
| **后端模块结构** | ✅ 模块化 | ❌ 分散化 | ✅ 模块化 | ✅ 完全一致 |
| **API路由管理** | ✅ 统一在charts/api.py | ❌ 缺失 | ✅ 统一在charts/api.py | ✅ 完全一致 |
| **前端组件路径** | market-analysis/brand-analysis.tsx | market-analysis/pricing-analysis.tsx | market-analysis/pricing-analysis.tsx | ✅ 路径一致 |
| **数据获取方法** | getTAMMarketShareData | getPricingAnalysisDataByProject | getPriceDistributionData | ✅ 命名规范一致 |
| **过滤器组件** | FilterRenderer | ChartWithFilters | FilterRenderer | ✅ 完全一致 |
| **数据刷新Hook** | useTAMDataRefresh | 无 | usePriceDistributionDataRefresh | ✅ 模式一致 |

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
   - 集成统一的过滤器服务`get_filtered_asins`
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
   - **修改内容**：添加`getPriceDistributionData`方法
   - **具体操作**：
     - 集成过滤器状态管理器
     - 标准化的API调用逻辑
     - 完整的错误处理

3. **`frontend/src/components/analysis-db/hooks/use-chart-data-refresh.ts`**
   - **修改内容**：添加`usePriceDistributionDataRefresh` Hook
   - **具体操作**：
     - 使用`useChartDataRefresh`基础Hook
     - 集成新的数据获取方法
     - 支持过滤器变化时自动刷新

4. **`frontend/src/components/analysis-db/market-analysis/pricing-analysis.tsx`**
   - **修改内容**：完全重构组件实现
   - **具体操作**：
     - 替换`ChartWithFilters`为`FilterRenderer`
     - 集成新的数据刷新Hook
     - 添加统一的状态管理
     - 保持现有的图表功能
     - 保持与`brand-analysis.tsx`相同的目录结构

5. **`frontend/src/components/analysis-db/configs/chart-filter-data.ts`**
   - **修改内容**：添加Price Analysis的过滤器配置
   - **具体操作**：
     - 添加`CHART_NAMES.PRICE_ANALYSIS`配置项
     - 定义可见过滤器和默认值
     - 配置扩展字段选项

6. **`frontend/src/components/analysis-db/constants/chart-names.ts`**
   - **修改内容**：确保`PRICE_ANALYSIS`常量存在
   - **具体操作**：
     - 验证`PRICE_ANALYSIS: 'price-analysis'`定义
     - 更新相关的显示名称和描述
   - **注意**：project_id在配置函数中动态设置，与TAM保持一致

## 🧪 测试策略设计

### 后端API测试方案

基于Sales Trend API的成功测试经验，为Price Distribution API制定完整的测试策略：

#### 1. **功能测试场景**

**测试端点**: `POST /api/v1/dashboard/price-distribution`

##### 场景1: 基础功能测试
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/price-distribution \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {},
    "timeframe": {"period": "year"}
  }'
```
**预期结果**: 返回完整的价格分布数据，包含所有分类的统计信息

##### 场景2: Category过滤测试
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/price-distribution \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {"categories": ["Light Switches"]},
    "timeframe": {"period": "year"}
  }'
```
**预期结果**: 只返回Light Switches分类的价格分布数据

##### 场景3: Brand过滤测试
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/price-distribution \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {"brands": ["Leviton", "Lutron"]},
    "timeframe": {"period": "year"}
  }'
```
**预期结果**: 只包含Leviton和Lutron品牌的价格分布数据

##### 场景4: Extend Fields过滤测试
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/price-distribution \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {
      "extend_fields": {"smart_capability": "Smart"}
    },
    "timeframe": {"period": "year"}
  }'
```
**预期结果**: 只包含智能产品的价格分布数据

##### 场景5: 复合过滤测试
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/price-distribution \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {
      "categories": ["Light Switches"],
      "brands": ["Leviton"],
      "extend_fields": {"smart_capability": "Smart"}
    },
    "timeframe": {"period": "year"}
  }'
```
**预期结果**: Leviton智能Light Switches的价格分布数据

##### 场景6: 边界测试
```bash
curl -X POST http://localhost:8000/api/v1/dashboard/price-distribution \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {"brands": ["NonExistentBrand"]},
    "timeframe": {"period": "year"}
  }'
```
**预期结果**: 返回空数据结构，正确处理无匹配结果的情况

#### 2. **数据一致性验证**

**验证点**:
1. **项目ASIN过滤**: 确保使用`projects.selected_product_asins`
2. **价格统计计算**: 验证min, q1, median, mean, q3, max的准确性
3. **品牌价格分布**: 验证每个品牌的价格数据正确性
4. **过滤器集成**: 确保所有过滤条件正确工作
5. **数据结构**: 验证响应格式符合前端期望

**数据库验证查询示例**:
```sql
-- 验证Light Switches分类的价格统计
SELECT 
  category,
  COUNT(*) as product_count,
  MIN(price) as min_price,
  PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY price) as q1,
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price) as median,
  AVG(price) as mean,
  PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY price) as q3,
  MAX(price) as max_price
FROM product_wide_table 
WHERE category = 'Light Switches' 
  AND platform_id IN (SELECT unnest(selected_product_asins) FROM projects WHERE id = 'project_id')
GROUP BY category;
```

#### 3. **性能测试**

- **响应时间**: < 3秒（包含复杂统计计算）
- **并发测试**: 支持10个并发请求
- **大数据量测试**: 支持10,000+ 产品的价格分布计算

#### 4. **错误处理测试**

- **无效project_id**: 返回400错误
- **无效过滤条件**: 返回400错误并提供详细信息
- **数据库连接失败**: 返回500错误
- **超时处理**: 确保长时间查询能够正确处理

### 前端组件测试方案

#### 1. **组件渲染测试**
- 验证`FilterRenderer`正确渲染
- 验证价格分布图表正确显示
- 验证品牌小提琴图正确渲染
- 验证散点图交互功能

#### 2. **数据流测试**
- 验证`usePriceDistributionDataRefresh` Hook正确工作
- 验证过滤器变化触发数据刷新
- 验证loading和error状态正确处理

#### 3. **集成测试**
- 验证与`FilterRenderer`的集成
- 验证与数据服务的集成
- 验证与图表组件的集成

## 📋 重构实施步骤

### 阶段一：后端架构重构 (预计2-3天)

#### Step 1: 创建模块化目录结构
- [ ] 创建`backend/dashboard/charts/pricing_analysis/`目录
- [ ] 创建`__init__.py`, `models.py`, `services.py`文件
- [ ] 设置模块导出和依赖

#### Step 2: 实现数据模型
- [ ] 定义`PriceDistributionRequest`模型
- [ ] 定义`PriceDistributionResponse`模型
- [ ] 定义所有子数据模型（CategoryPriceData等）
- [ ] 添加模型验证和示例

#### Step 3: 实现服务类
- [ ] 创建`PriceDistributionService`类
- [ ] 实现`get_price_distribution_data()`主方法
- [ ] 实现过滤器集成（使用`get_filtered_asins`）
- [ ] 实现价格统计计算逻辑
- [ ] 实现品牌价格分布计算
- [ ] 添加错误处理和日志记录

#### Step 4: 集成API路由
- [ ] 在`backend/dashboard/charts/api.py`中添加路由
- [ ] 实现请求处理逻辑
- [ ] 添加API文档和示例
- [ ] 配置错误处理

### 阶段二：后端测试验证 (预计1-2天)

#### Step 5: API功能测试
- [ ] 执行基础功能测试（场景1）
- [ ] 执行所有过滤器测试（场景2-5）
- [ ] 执行边界测试（场景6）
- [ ] 验证数据一致性
- [ ] 性能测试和优化

#### Step 6: 数据验证
- [ ] 对比API结果与数据库直接查询
- [ ] 验证统计计算准确性
- [ ] 验证过滤器正确性
- [ ] 创建测试报告文档

### 阶段三：前端架构重构 (预计2-3天)

#### Step 7: 数据服务层更新
- [ ] 在`database-service.ts`中添加`getPriceDistributionData`方法
- [ ] 集成过滤器状态管理
- [ ] 添加错误处理和加载状态
- [ ] 测试API调用功能

#### Step 8: Hook层实现
- [ ] 在`use-chart-data-refresh.ts`中添加`usePriceDistributionDataRefresh`
- [ ] 集成自动刷新逻辑
- [ ] 添加依赖项追踪
- [ ] 测试Hook功能

#### Step 9: 组件重构
- [ ] 重构`pricing-analysis.tsx`组件
- [ ] 替换`ChartWithFilters`为`FilterRenderer`
- [ ] 集成新的数据Hook
- [ ] 保持现有图表功能
- [ ] 测试组件渲染和交互

#### Step 10: 配置文件更新
- [ ] 更新`chart-filter-data.ts`配置
- [ ] 验证`chart-names.ts`常量
- [ ] 测试过滤器配置

### 阶段四：集成测试和验证 (预计1天)

#### Step 11: 端到端测试
- [ ] 测试完整的数据流（前端→后端→数据库）
- [ ] 验证过滤器功能
- [ ] 测试图表渲染和交互
- [ ] 验证性能表现

#### Step 12: 用户验收测试
- [ ] 对比重构前后的功能一致性
- [ ] 验证所有图表类型正确显示
- [ ] 验证数据准确性
- [ ] 收集反馈和优化

### 阶段五：代码清理和文档 (预计0.5天)

#### Step 13: 代码清理（在所有Pricing Charts完成后执行）
- [ ] ⚠️ **注意**: 此步骤需要等待整个Pricing Dashboard的所有Charts重构完成
- [ ] 移除`backend/dashboard/services/pricing_analysis_service.py`
- [ ] 移除`backend/dashboard/models.py`中的相关模型
- [ ] 清理前端老旧组件引用
- [ ] 移除未使用的导入和依赖

#### Step 14: 文档更新
- [ ] 创建API文档（参考Sales Trend格式）
- [ ] 更新架构文档
- [ ] 创建测试报告
- [ ] 更新README文件

## 🚨 重要注意事项

### 代码清理策略

**关键原则**: 老代码清理必须在整个Pricing Dashboard的所有Charts重构完成后统一进行

**原因**:
1. **依赖关系**: 其他Pricing Charts可能仍在使用`pricing_analysis_service.py`中的共享逻辑
2. **风险控制**: 避免在重构过程中破坏现有功能
3. **回滚能力**: 保持重构前的代码作为备份，直到所有功能验证完毕

**清理时机**:
- ✅ Price Distribution重构完成并验证
- ✅ 其他Pricing Charts（如Price Trend, Price Comparison等）重构完成
- ✅ 整个Pricing Dashboard功能验证通过
- ✅ 用户验收测试完成
- 🗑️ 执行统一的代码清理

### 质量保证

1. **数据一致性**: 每个步骤都必须验证数据准确性
2. **功能完整性**: 确保重构后功能不缺失
3. **性能标准**: 响应时间不能超过重构前的1.5倍
4. **用户体验**: 界面和交互保持一致性

### 风险缓解

1. **分阶段实施**: 每个阶段独立验证，降低风险
2. **并行开发**: 新旧代码并存，确保系统稳定
3. **快速回滚**: 如遇问题可快速切换回原实现
4. **充分测试**: 每个环节都有对应的测试验证

### 需要移除的代码（清理阶段）

#### 后端清理

1. **`backend/dashboard/services/pricing_analysis_service.py`**
   - **操作**：在新架构验证后移除此文件
   - **注意**：确保所有功能已迁移到新的模块化架构

2. **`backend/dashboard/models.py`**
   - **操作**：移除Price Distribution相关的模型定义
   - **具体移除**：
     - `PriceDistribution`类
     - `BrandPriceDistribution`类
     - `PricingAnalysisResponse`类
     - 相关的统计模型

#### 前端清理

3. **前端组件中的老旧代码**
   - **操作**：移除对老服务的引用
   - **具体清理**：
     - 移除`ChartWithFilters`的使用
     - 清理手动的数据获取逻辑
     - 移除分散的状态管理代码

## 🔄 实施流程

### 阶段1：后端重构（预计2-3小时）

1. **创建模块结构**（30分钟）
   - 创建`pricing_analysis`目录
   - 创建基础文件结构
   - 设置模块导入

2. **实现数据模型**（45分钟）
   - 定义完整的Pydantic模型
   - 迁移现有的数据结构
   - 添加新的分析类型支持

3. **实现服务层**（60分钟）
   - 创建`PriceDistributionService`类
   - 迁移现有的业务逻辑
   - 集成统一的过滤器服务
   - 优化数据处理逻辑

4. **集成API路由**（30分钟）
   - 在`charts/api.py`中添加路由
   - 实现完整的错误处理
   - 添加详细的API文档

5. **测试验证**（15分钟）
   - API功能测试
   - 数据准确性验证
   - 错误处理测试

### 阶段2：前端集成（预计2-3小时）

1. **数据服务集成**（45分钟）
   - 在`database-service.ts`中添加方法
   - 集成过滤器状态管理
   - 实现标准化的API调用

2. **创建数据Hook**（30分钟）
   - 实现`usePriceDistributionDataRefresh`
   - 集成自动刷新机制
   - 添加状态管理

3. **重构组件实现**（90分钟）
   - 替换`ChartWithFilters`为`FilterRenderer`
   - 集成新的数据获取机制
   - 实现统一的状态管理
   - 保持现有图表功能

4. **配置更新**（30分钟）
   - 更新过滤器配置
   - 验证图表名称常量
   - 更新相关配置文件

5. **集成测试**（15分钟）
   - 前端功能测试
   - 过滤器集成测试
   - 用户体验验证

### 阶段3：验证优化（预计1-2小时）

1. **功能验证**（45分钟）
   - 端到端功能测试
   - 数据准确性对比
   - 过滤器功能验证
   - 错误处理测试

2. **性能优化**（30分钟）
   - 响应时间对比
   - 数据加载性能测试
   - 内存使用优化

3. **清理工作**（15分钟）
   - 移除老旧代码
   - 清理无用导入
   - 更新文档

## ✅ 验证清单

### 后端验证

- [ ] **模块结构**：`pricing_analysis`目录结构正确
- [ ] **数据模型**：所有Pydantic模型定义完整
- [ ] **服务层**：`PriceDistributionService`功能正常
- [ ] **API路由**：在`charts/api.py`中正确注册
- [ ] **过滤器集成**：`get_filtered_asins`正常工作
- [ ] **错误处理**：完整的异常处理和日志记录
- [ ] **数据准确性**：计算结果与原实现一致

### 前端验证

- [ ] **数据服务**：`getPriceDistributionData`方法正常
- [ ] **数据Hook**：`usePriceDistributionDataRefresh`功能正常
- [ ] **组件集成**：`FilterRenderer`正确替换`ChartWithFilters`
- [ ] **状态管理**：loading/error/data状态正确处理
- [ ] **过滤器功能**：过滤器变化时自动刷新数据
- [ ] **用户界面**：保持原有的图表功能和用户体验
- [ ] **配置更新**：过滤器配置正确生效

### 整体验证

- [ ] **架构一致性**：与TAM饼图架构完全一致
- [ ] **功能完整性**：所有原有功能正常工作
- [ ] **性能表现**：响应时间和加载性能良好
- [ ] **代码质量**：代码结构清晰，注释完整
- [ ] **文档完整**：API文档和使用说明完整

## 🚨 风险评估与缓解

### 高风险项

1. **数据准确性风险**
   - **风险**：重构后计算结果与原实现不一致
   - **缓解**：详细的数据对比测试，保留原实现作为参考

2. **用户界面兼容性风险**
   - **风险**：重构影响现有的图表功能
   - **缓解**：保持原有的图表组件，只替换数据获取部分

### 中风险项

1. **过滤器集成风险**
   - **风险**：过滤器功能可能不正常
   - **缓解**：充分测试各种过滤器组合

2. **性能影响风险**
   - **风险**：新架构可能影响加载性能
   - **缓解**：性能测试和优化

### 低风险项

1. **配置更新风险**
   - **风险**：配置文件更新可能影响其他功能
   - **缓解**：谨慎的配置更新和充分测试

## 🎯 预期收益

### 短期收益

- **架构一致性**：与TAM饼图保持一致的架构模式
- **开发效率**：统一的开发模式和工具
- **维护性提升**：模块化结构便于维护和扩展

### 长期收益

- **技术债务减少**：消除架构不一致性
- **扩展性增强**：支持新功能和需求变化
- **团队协作**：统一的开发标准和最佳实践

## 📚 总结

本重构设计文档为Price Distribution图表提供了完整的现代化升级方案。通过采用TAM饼图的成功架构模式，将实现：

1. **完全统一的架构**：后端模块化、前端现代化
2. **标准化的实现**：API路由、数据服务、状态管理
3. **提升的用户体验**：统一的过滤器、自动刷新、错误处理
4. **增强的可维护性**：清晰的代码结构、完整的文档

重构完成后，Price Distribution将成为项目中架构标准化的典型示例，为后续其他图表的重构提供参考模板。
