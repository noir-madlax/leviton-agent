# Chart API 开发规范

## 📋 概述

本文档定义了 Dashboard Chart API 的开发规范，确保所有图表接口的一致性、可维护性和可扩展性。

## 🏗️ 后端架构规范

### 1. 目录结构

每个图表模块应遵循以下目录结构：

```
backend/dashboard/charts/
├── base_models.py                    # 基础模型（已存在）
├── api.py                           # 路由注册（已存在）
└── {chart_name}/                    # 图表模块目录
    ├── __init__.py                  # 模块导出
    ├── models.py                    # 数据模型
    └── services.py                  # 业务逻辑
```

### 2. 命名规范

- **目录名**: 使用 camelCase，如 `customerSatisfaction`, `salesTrend`
- **文件名**: 使用 kebab-case，如 `customer-satisfaction.py`
- **类名**: 使用 PascalCase，如 `CustomerSatisfactionService`
- **API 路径**: 使用 kebab-case，如 `/competitive/customer-satisfaction`

### 3. 基础模型规范

#### 3.1 基础模型定义

**必须在 `base_models.py` 中定义以下基础模型：**

```python
# backend/dashboard/charts/base_models.py
from typing import Dict, Any, Optional, Generic, TypeVar, List
from pydantic import BaseModel, Field
from datetime import datetime

# 泛型类型变量，用于BaseResponseModel
T = TypeVar('T')

class FiltersModel(BaseModel):
    """筛选条件模型 - 所有图表的标准筛选格式"""
    categories: List[str] = Field(default_factory=list, description="产品类别筛选")
    brands: List[str] = Field(default_factory=list, description="品牌筛选")
    segments: List[str] = Field(default_factory=list, description="细分市场筛选")
    extend_fields: Dict[str, Any] = Field(default_factory=dict, description="扩展字段筛选，字段名和值不固定")

    class Config:
        json_schema_extra = {
            "example": {
                "categories": ["Light Switches"],
                "brands": ["Leviton", "Lutron"],
                "segments": ["Premium"],
                "extend_fields": {"smart_capability": "Smart"}
            }
        }

class DateRangeModel(BaseModel):
    """时间范围模型 - 需要时间筛选的图表使用"""
    start_date: str = Field(..., description="开始日期，格式：YYYY-MM-DD")
    end_date: str = Field(..., description="结束日期，格式：YYYY-MM-DD")

    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-01-01",
                "end_date": "2024-06-30"
            }
        }

class BaseRequestModel(BaseModel):
    """Dashboard charts 基础请求模型 - 所有图表请求必须继承"""
    project_id: str = Field(..., description="项目ID，用于ASIN过滤")
    filters: Optional[FiltersModel] = Field(default=None, description="过滤条件对象")
    date_range: Optional[DateRangeModel] = Field(default=None, description="时间范围对象")

class BaseResponseModel(BaseModel, Generic[T]):
    """Dashboard charts 基础响应模型 - 所有图表响应必须继承"""
    status: str = Field(default="success", description="响应状态：success/error")
    message: Optional[str] = Field(default=None, description="响应消息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat(), description="响应时间戳")
    data: T = Field(..., description="响应数据")

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": None,
                "timestamp": "2024-01-15T10:30:00Z",
                "data": "具体的数据内容"
            }
        }
```

#### 3.2 请求模型继承规范

**每个图表的请求模型必须继承 `BaseRequestModel`：**

```python
# charts/{chartName}/models.py
from ..base_models import BaseRequestModel

class {ChartName}Request(BaseRequestModel):
    """图表请求模型 - 继承基础请求模型"""

    # 如果需要额外字段，在这里添加
    # additional_param: Optional[str] = Field(default=None, description="额外参数")

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "project_123",
                "filters": {
                    "categories": ["Light Switches"],
                    "brands": ["Leviton", "Lutron"],
                    "segments": ["Premium"],
                    "extend_fields": {"smart_capability": "Smart"}
                },
                "date_range": {  # 如果图表需要时间范围
                    "start_date": "2024-01-01",
                    "end_date": "2024-06-30"
                }
            }
        }
```

#### 3.3 响应模型继承规范

**每个图表的响应模型必须继承 `BaseResponseModel`：**

```python
# charts/{chartName}/models.py
from ..base_models import BaseResponseModel
from typing import List

class {ChartName}Data(BaseModel):
    """图表数据模型 - 定义单个数据项的结构"""
    id: str = Field(..., description="数据项ID")
    name: str = Field(..., description="数据项名称")
    value: float = Field(..., description="数据值")
    # 其他字段...

class {ChartName}Response(BaseResponseModel[List[{ChartName}Data]]):
    """图表响应模型 - 继承基础响应模型，指定数据类型"""

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": None,
                "timestamp": "2024-01-15T10:30:00Z",
                "data": [
                    {
                        "id": "item_1",
                        "name": "示例数据",
                        "value": 123.45
                    }
                ]
            }
        }
```

#### 3.4 继承模式示例

**不同数据类型的继承示例：**

```python
# 返回数组数据
class ProductListResponse(BaseResponseModel[List[ProductData]]):
    pass

# 返回单个对象
class SummaryResponse(BaseResponseModel[SummaryData]):
    pass

# 返回字典数据
class MetricsResponse(BaseResponseModel[Dict[str, Any]]):
    pass

# 返回嵌套结构
class ComplexResponse(BaseResponseModel[Dict[str, List[ProductData]]]):
    pass
```

### 4. 服务类规范

#### 4.1 继承结构和模型处理

```python
# charts/{chartName}/services.py
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

from dashboard.services.base_service import BaseDashboardService
from core.models.filters import ProjectFilters
from ..base_models import FiltersModel, DateRangeModel

logger = logging.getLogger(__name__)

class {ChartName}Service(BaseDashboardService):
    """图表服务类

    负责：
    1. 接收并处理继承的请求模型
    2. 数据查询和处理
    3. 业务逻辑计算
    4. 返回符合响应模型的数据
    """

    def __init__(self, project_id: str, filters: Optional[FiltersModel] = None,
                 date_range: Optional[DateRangeModel] = None):
        """初始化服务

        Args:
            project_id: 项目ID
            filters: 筛选条件对象（来自BaseRequestModel）
            date_range: 时间范围对象（来自BaseRequestModel，可选）
        """
        super().__init__(project_id)

        # 处理筛选器对象
        if filters:
            # 将 FiltersModel 转换为 ProjectFilters 所需的字典格式
            filters_dict = {
                "categories": filters.categories,
                "brands": filters.brands,
                "segments": filters.segments,
                "extend_fields": filters.extend_fields
            }
            project_filters = ProjectFilters.from_dict(filters_dict)
            self.set_project_filters(project_filters)

        # 处理时间范围对象
        self.date_range = None
        if date_range:
            self.date_range = {
                "start_date": date_range.start_date,
                "end_date": date_range.end_date
            }

        logger.info(f"{self.__class__.__name__} initialized for project {project_id}")

    def get_data(self) -> List[Dict[str, Any]]:
        """获取图表数据 - 必须实现

        Returns:
            List[Dict]: 符合响应模型 data 字段要求的数据

        Note:
            返回的数据结构必须与 {ChartName}Response 中定义的 data 类型匹配
        """
        try:
            # 1. 数据查询
            raw_data = self._query_data()

            # 2. 数据处理和计算
            processed_data = self._process_data(raw_data)

            # 3. 返回渲染就绪的数据
            return processed_data

        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}: {e}")
            return []  # 返回空数组，符合响应模型要求

    def _query_data(self) -> List[Dict[str, Any]]:
        """查询原始数据"""
        # 实现具体的数据查询逻辑
        pass

    def _process_data(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """处理数据，返回符合响应模型的格式"""
        # 实现数据处理逻辑，确保返回的字段与 {ChartName}Data 模型匹配
        pass
```

#### 4.2 数据处理原则

- **后端完成所有计算**: 满意度分数、排序、颜色编码等
- **返回渲染就绪数据**: 前端直接使用，无需额外处理
- **统一错误处理**: 返回空数组而不是抛出异常
- **日志记录**: 记录关键操作和错误信息

### 5. API 接口规范

#### 5.1 路由定义和模型使用

```python
# charts/api.py
from fastapi import APIRouter, HTTPException
import logging

# 导入继承的模型
from .{chartName}.models import {ChartName}Request, {ChartName}Response
from .{chartName}.services import {ChartName}Service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/{category}/{chart-name}", response_model={ChartName}Response)
async def get_{chart_name}(request: {ChartName}Request):
    """获取{图表名称}数据

    Args:
        request: 图表请求（继承自BaseRequestModel），包含：
                - project_id: 项目ID
                - filters: FiltersModel对象
                - date_range: DateRangeModel对象（可选）

    Returns:
        {ChartName}Response: 继承自BaseResponseModel的响应，包含：
                           - status: 响应状态
                           - message: 响应消息
                           - timestamp: 时间戳
                           - data: 图表数据

    Raises:
        HTTPException: 当请求处理失败时
    """
    try:
        # 创建服务实例，传入继承模型的字段
        service = {ChartName}Service(
            project_id=request.project_id,
            filters=request.filters,        # FiltersModel对象
            date_range=request.date_range   # DateRangeModel对象（如果需要）
        )

        # 获取数据
        chart_data = service.get_data()

        # 创建响应对象（自动包含status, message, timestamp）
        response = {ChartName}Response(data=chart_data)

        logger.info(f"{图表名称} analysis completed for project {request.project_id}: {len(response.data)} items analyzed")

        return response

    except Exception as e:
        logger.error(f"Error in {图表名称} analysis: {e}")
        # 返回错误响应（仍然符合BaseResponseModel格式）
        error_response = {ChartName}Response(
            status="error",
            message=str(e),
            data=[]  # 空数据
        )
        raise HTTPException(status_code=500, detail=error_response.dict())
```

#### 5.2 模型验证和错误处理

```python
# 完整的错误处理示例
@router.post("/{category}/{chart-name}", response_model={ChartName}Response)
async def get_{chart_name}(request: {ChartName}Request):
    try:
        # 1. 请求模型自动验证（Pydantic）
        # request.project_id, request.filters, request.date_range 已经过验证

        # 2. 业务逻辑验证
        if not request.project_id:
            raise ValueError("Project ID is required")

        # 3. 创建服务并处理
        service = {ChartName}Service(
            project_id=request.project_id,
            filters=request.filters,
            date_range=request.date_range
        )

        chart_data = service.get_data()

        # 4. 响应模型自动构建（包含基础字段）
        response = {ChartName}Response(data=chart_data)

        return response

    except ValueError as e:
        # 业务逻辑错误
        logger.error(f"Validation error in {图表名称}: {e}")
        raise HTTPException(status_code=400, detail=str(e))

    except Exception as e:
        # 系统错误
        logger.error(f"System error in {图表名称}: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

#### 5.2 路径规范

- **基础路径**: `/api/v1/dashboard/charts/`
- **分类路径**: `/{category}/{chart-name}`
- **示例**: `/competitive/customer-satisfaction`, `/sales/trend-analysis`

## 🎨 前端架构规范

### 1. 目录结构

```
frontend/src/app/chat/charts/
└── {chart_name}/                    # 图表模块目录
    ├── components/                  # 组件目录
    │   └── {chart-name}-chart.tsx   # 主图表组件
    ├── hooks/                       # Hooks目录
    │   └── use-{chart-name}-data.ts # 数据Hook
    ├── services/                    # 服务目录
    │   └── {chart-name}-api.ts      # API服务
    ├── types/                       # 类型目录
    │   └── {chart-name}.types.ts    # 类型定义
    └── index.ts                     # 模块导出
```

### 2. 类型定义规范

```typescript
// types/{chart-name}.types.ts
export interface {ChartName}Data {
  // 数据字段定义
}

export interface {ChartName}Filters {
  categories?: string[]
  brands?: string[]
  segments?: string[]
  extend_fields?: Record<string, any>
}

export interface {ChartName}Response {
  status: string
  message?: string
  timestamp: string
  data: {ChartName}Data[]
}

export interface {ChartName}Request {
  project_id: string
  filters?: {ChartName}Filters
}

export interface {ChartName}ChartProps {
  projectId: string
  filters?: {ChartName}Filters
  onDataClick?: (data: {ChartName}Data) => void
}
```

### 3. API 服务规范

```typescript
// services/{chart-name}-api.ts
import { ChartApiBase } from '../../shared/services/chart-api-base'

class {ChartName}Api extends ChartApiBase {
  constructor() {
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    super(baseUrl)
  }

  async get{ChartName}Data(
    projectId: string,
    filters?: {ChartName}Filters
  ): Promise<{ChartName}Response> {
    const requestBody: {ChartName}Request = {
      project_id: projectId,
      filters: filters || {}
    }

    return this.post<{ChartName}Response>('/api/v1/dashboard/charts/{category}/{chart-name}', requestBody)
  }
}

export const {chartName}Api = new {ChartName}Api()
```

### 4. 数据 Hook 规范

```typescript
// hooks/use-{chart-name}-data.ts
export function use{ChartName}Data(
  projectId: string,
  filters?: {ChartName}Filters
) {
  const [data, setData] = useState<{ChartName}Response | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!projectId) {
      setData(null)
      setError(null)
      return
    }

    const fetchData = async () => {
      setLoading(true)
      setError(null)

      try {
        const result = await {chartName}Api.get{ChartName}Data(projectId, filters)
        setData(result)
      } catch (err) {
        console.error('Failed to fetch {chart name} data:', err)
        setError(err instanceof Error ? err.message : 'Unknown error occurred')
        setData(null)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [projectId, JSON.stringify(filters)])

  return { data, loading, error, refetch: () => { /* refetch logic */ } }
}
```

### 5. 组件规范

```typescript
// components/{chart-name}-chart.tsx
export function {ChartName}Chart({ 
  projectId, 
  filters, 
  onDataClick 
}: {ChartName}ChartProps) {
  const { data, loading, error } = use{ChartName}Data(projectId, filters)

  if (loading) {
    return <LoadingComponent />
  }

  if (error) {
    return <ErrorComponent error={error} />
  }

  if (!data?.data || data.data.length === 0) {
    return <EmptyStateComponent />
  }

  return (
    <div className="space-y-4">
      {/* 图表内容 */}
    </div>
  )
}
```

## 🔧 完整继承示例

### 示例：销售趋势图表

**1. 请求模型继承：**
```python
# charts/salesTrend/models.py
from ..base_models import BaseRequestModel

class SalesTrendRequest(BaseRequestModel):
    """销售趋势请求模型 - 继承基础请求模型"""

    # 无需额外字段，使用基础模型的 project_id, filters, date_range

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "project_123",
                "filters": {
                    "categories": ["Smart Switches"],
                    "brands": ["Leviton"],
                    "segments": [],
                    "extend_fields": {}
                },
                "date_range": {
                    "start_date": "2024-01-01",
                    "end_date": "2024-06-30"
                }
            }
        }
```

**2. 响应模型继承：**
```python
# charts/salesTrend/models.py
from ..base_models import BaseResponseModel
from typing import List

class SalesTrendData(BaseModel):
    """销售趋势数据模型"""
    date: str = Field(..., description="日期")
    sales_volume: int = Field(..., description="销售量")
    revenue: float = Field(..., description="收入")
    product_asin: str = Field(..., description="产品ASIN")

class SalesTrendResponse(BaseResponseModel[List[SalesTrendData]]):
    """销售趋势响应模型 - 继承基础响应模型"""

    class Config:
        json_schema_extra = {
            "example": {
                "status": "success",
                "message": None,
                "timestamp": "2024-01-15T10:30:00Z",
                "data": [
                    {
                        "date": "2024-01-01",
                        "sales_volume": 150,
                        "revenue": 7500.0,
                        "product_asin": "B00NG0ELL0"
                    }
                ]
            }
        }
```

**3. 服务类处理继承模型：**
```python
# charts/salesTrend/services.py
from ..base_models import FiltersModel, DateRangeModel

class SalesTrendService(BaseDashboardService):
    def __init__(self, project_id: str, filters: Optional[FiltersModel] = None,
                 date_range: Optional[DateRangeModel] = None):
        super().__init__(project_id)

        # 处理 FiltersModel
        if filters:
            filters_dict = {
                "categories": filters.categories,
                "brands": filters.brands,
                "segments": filters.segments,
                "extend_fields": filters.extend_fields
            }
            project_filters = ProjectFilters.from_dict(filters_dict)
            self.set_project_filters(project_filters)

        # 处理 DateRangeModel
        self.start_date = date_range.start_date if date_range else None
        self.end_date = date_range.end_date if date_range else None

    def get_data(self) -> List[Dict[str, Any]]:
        # 返回符合 SalesTrendData 结构的数据
        return [
            {
                "date": "2024-01-01",
                "sales_volume": 150,
                "revenue": 7500.0,
                "product_asin": "B00NG0ELL0"
            }
        ]
```

**4. API 接口使用继承模型：**
```python
# charts/api.py
@router.post("/sales/trend", response_model=SalesTrendResponse)
async def get_sales_trend(request: SalesTrendRequest):
    try:
        service = SalesTrendService(
            project_id=request.project_id,      # 来自 BaseRequestModel
            filters=request.filters,            # FiltersModel 对象
            date_range=request.date_range       # DateRangeModel 对象
        )

        data = service.get_data()

        # 自动包含 status, message, timestamp
        response = SalesTrendResponse(data=data)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

## 📝 开发检查清单

### 后端开发

**基础模型检查：**
- [ ] 确认 `base_models.py` 中包含所有基础模型
- [ ] 验证 `BaseRequestModel` 包含 project_id, filters, date_range
- [ ] 验证 `BaseResponseModel` 包含 status, message, timestamp, data
- [ ] 验证 `FiltersModel` 包含 categories, brands, segments, extend_fields

**图表模型检查：**
- [ ] 创建图表目录结构
- [ ] 请求模型继承 `BaseRequestModel`
- [ ] 响应模型继承 `BaseResponseModel[T]`，指定正确的泛型类型
- [ ] 数据模型定义完整的字段和类型
- [ ] 添加完整的 Config 和示例

**服务类检查：**
- [ ] 服务类继承 `BaseDashboardService`
- [ ] 构造函数接收 `FiltersModel` 和 `DateRangeModel` 对象
- [ ] 正确转换 `FiltersModel` 为 `ProjectFilters`
- [ ] 正确处理 `DateRangeModel` 的时间范围
- [ ] `get_data()` 返回符合响应模型的数据结构

**API 接口检查：**
- [ ] 路由使用正确的请求/响应模型类型注解
- [ ] 正确传递继承模型的字段到服务类
- [ ] 添加 API 路由到 charts/api.py
- [ ] 确保路由已注册到主应用
- [ ] 添加完整的错误处理和日志
- [ ] 编写 API 文档和示例

### 前端开发

- [ ] 创建图表目录结构
- [ ] 定义 TypeScript 类型
- [ ] 实现 API 服务类
- [ ] 创建数据 Hook
- [ ] 实现图表组件
- [ ] 添加加载/错误/空状态处理
- [ ] 创建 index.ts 导出文件
- [ ] 集成到目标页面

### 测试验证

- [ ] 后端接口测试（Postman/cURL）
- [ ] 前端组件渲染测试
- [ ] 错误场景测试
- [ ] 性能测试
- [ ] 类型检查通过

## 🎯 最佳实践

1. **数据处理**: 后端完成所有业务逻辑，前端专注渲染
2. **错误处理**: 优雅降级，提供有意义的错误信息
3. **类型安全**: 完整的 TypeScript 类型定义
4. **性能优化**: 合理的缓存策略和加载状态
5. **用户体验**: 响应式设计和交互反馈
6. **代码复用**: 利用基础类和共享组件
7. **文档完整**: 清晰的注释和使用示例

遵循这些规范，可以确保所有图表接口的一致性和高质量。
