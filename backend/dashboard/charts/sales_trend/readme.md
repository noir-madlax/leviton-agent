# 销售趋势API文档

销售趋势API为前端StackedAreaChart提供品牌月度销售数据，支持revenue和volume双指标，完全聚合处理，前端直接渲染。

## 🛠️ API接口说明

### **POST** `/api/v1/dashboard/sales-trend`

**概述**: 获取品牌销售趋势数据，提供Top 10品牌的月度revenue和volume趋势分析。

**标签**: Dashboard, Sales Analysis, Trends

---

#### **请求参数**

**Content-Type**: `application/json`

**请求体Schema**:
```json
{
  "type": "object",
  "required": ["project_id"],
  "properties": {
    "project_id": {
      "type": "string",
      "format": "uuid",
      "description": "项目ID，用于ASIN过滤和数据范围限定",
      "example": "d2c02b80-4c82-44cc-8093-56708a7883f7"
    },
    "filters": {
      "type": "object",
      "description": "过滤条件，支持多维度筛选",
      "properties": {
        "categories": {
          "type": "array",
          "items": {"type": "string"},
          "description": "产品分类过滤，支持分类名称",
          "example": ["Light Switches", "Dimmer Switches"]
        },
        "brands": {
          "type": "array", 
          "items": {"type": "string"},
          "description": "品牌过滤，支持品牌名称",
          "example": ["Leviton", "Lutron"]
        },
        "segments": {
          "type": "array",
          "items": {"type": "string"}, 
          "description": "产品段过滤，基于产品细分结果",
          "example": ["Combination Switches", "Dual Function Dimmer Switches"]
        },
        "extend_fields": {
          "type": "object",
          "description": "扩展字段过滤，支持自定义属性筛选",
          "additionalProperties": true,
          "example": {"smart_capability": "Smart"}
        }
      }
    },
    "date_range": {
      "type": "object",
      "description": "时间范围筛选",
      "properties": {
        "start_date": {
          "type": "string",
          "format": "date",
          "description": "开始日期 (YYYY-MM-DD)",
          "example": "2025-01-01"
        },
        "end_date": {
          "type": "string", 
          "format": "date",
          "description": "结束日期 (YYYY-MM-DD)",
          "example": "2025-06-30"
        }
      }
    },
    "aggregation": {
      "type": "string",
      "enum": ["monthly"],
      "default": "monthly",
      "description": "数据聚合粒度，目前只支持月度聚合"
    }
  }
}
```

**请求示例**:
```json
{
  "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
  "filters": {
    "categories": ["Light Switches"],
    "brands": ["Leviton", "Lutron"],
    "extend_fields": {"smart_capability": "Smart"}
  },
  "date_range": {
    "start_date": "2025-01-01",
    "end_date": "2025-06-30"
  },
  "aggregation": "monthly"
}
```

---

#### **响应结果**

**成功响应 (200)**:

**Content-Type**: `application/json`

**响应体Schema**:
```json
{
  "type": "object",
  "required": ["trend_data", "brands", "summary"],
  "properties": {
    "trend_data": {
      "type": "array",
      "description": "月度趋势数据数组",
      "items": {
        "type": "object",
        "required": ["month"],
        "properties": {
          "month": {
            "type": "string",
            "pattern": "^\\d{4}-\\d{2}$",
            "description": "月份 (YYYY-MM格式)",
            "example": "2025-01"
          }
        },
        "additionalProperties": {
          "type": "object",
          "description": "品牌数据，键为品牌名称",
          "properties": {
            "revenue": {
              "type": "number",
              "format": "float",
              "description": "该品牌该月收入 (USD)",
              "example": 850000.0
            },
            "volume": {
              "type": "integer",
              "description": "该品牌该月销量 (units)",
              "example": 12000
            }
          }
        }
      }
    },
    "brands": {
      "type": "array",
      "items": {"type": "string"},
      "maxItems": 10,
      "description": "Top 10品牌列表，按总revenue降序排序",
      "example": ["Lutron", "Leviton", "Kasa Smart", "ELEGRP"]
    },
    "summary": {
      "type": "object",
      "required": ["total_brands", "date_range", "total_revenue", "total_volume"],
      "description": "汇总统计信息",
      "properties": {
        "total_brands": {
          "type": "integer",
          "description": "返回的品牌总数 (≤10)",
          "example": 10
        },
        "date_range": {
          "type": "object",
          "properties": {
            "start": {
              "type": "string",
              "description": "实际数据开始月份",
              "example": "2025-01"
            },
            "end": {
              "type": "string", 
              "description": "实际数据结束月份",
              "example": "2025-06"
            }
          }
        },
        "total_revenue": {
          "type": "number",
          "format": "float",
          "description": "总收入 (USD)",
          "example": 47339356.11
        },
        "total_volume": {
          "type": "integer",
          "description": "总销量 (units)",
          "example": 1756932
        }
      }
    }
  }
}
```

**响应示例**:
```json
{
  "trend_data": [
    {
      "month": "2025-01",
      "Lutron": {"revenue": 2690325.53, "volume": 62282},
      "Leviton": {"revenue": 1197689.18, "volume": 48873},
      "Kasa Smart": {"revenue": 1458801.50, "volume": 52171}
    },
    {
      "month": "2025-02", 
      "Lutron": {"revenue": 2450917.65, "volume": 56216},
      "Leviton": {"revenue": 1036356.69, "volume": 43544},
      "Kasa Smart": {"revenue": 1158479.13, "volume": 46580}
    }
  ],
  "brands": ["Lutron", "Kasa Smart", "Leviton", "ELEGRP", "Tapo"],
  "summary": {
    "total_brands": 5,
    "date_range": {"start": "2025-01", "end": "2025-02"},
    "total_revenue": 15230000.0,
    "total_volume": 89400
  }
}
```

---

#### **错误响应**

**客户端错误 (400)**:
```json
{
  "type": "object",
  "properties": {
    "status_code": {"type": "integer", "example": 400},
    "detail": {"type": "string", "example": "Invalid project_id or no ASINs found"}
  }
}
```

**服务器错误 (500)**:
```json
{
  "type": "object", 
  "properties": {
    "status_code": {"type": "integer", "example": 500},
    "detail": {"type": "string", "example": "Internal server error during sales trend analysis"}
  }
}
```

## 🧩 Service实现说明

### 核心业务流程
1. **获取项目ASIN**: 使用`BaseDashboardService.project_asins`和`_apply_combined_filters()`
2. **获取产品品牌**: 通过`_get_base_product_table().select('platform_id, brand')`
3. **查询月度销售**: 从`product_sales_history_monthly`获取时间范围内数据
4. **聚合计算**: 按month+brand聚合revenue和volume
5. **Top 10筛选**: 按总revenue排序，取前10品牌
6. **格式化输出**: 转换为前端可直接使用的结构

### 关键方法
- `SalesTrendService.get_data()` - 主业务逻辑
- `_get_filtered_asins()` - 获取过滤后的ASIN列表  
- `_get_asin_brand_mapping()` - 获取ASIN到品牌的映射
- `_query_monthly_sales()` - 查询月度销售数据
- `_aggregate_by_brand_month()` - 按品牌和月度聚合
- `_format_response()` - 格式化响应数据

### 数据库依赖
- `product_wide_table` - 产品信息（brand字段）
- `product_sales_history_monthly` - 月度销售数据
- `projects` - 项目ASIN列表

## 📁 目录结构
```
backend/dashboard/charts/sales_trend/
├── __init__.py          # 模块导出
├── api.py              # 路由说明（实际路由在主api.py中）
├── models.py           # Pydantic模型
├── services.py         # 业务逻辑
└── readme.md           # 本文档
```

## 🔄 集成说明

### 后端集成
路由已集成在`backend/dashboard/api.py`中：
```python
@router.post("/sales-trend", response_model=SalesTrendResponse)
async def get_sales_trend(request: SalesTrendRequest):
    # 实现代码...
```

### 前端调用
```typescript
const salesTrendData = await fetch('/api/v1/dashboard/sales-trend', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    project_id: projectId,
    filters: { categories: selectedCategories },
    date_range: { start_date: '2024-01-01', end_date: '2024-06-30' }
  })
});
```

## 📝 实现状态
- [x] 创建目录结构和文档
- [x] 实现Pydantic模型
- [x] 实现业务服务类
- [x] 实现API路由（集成到主api.py）
- [x] 完成所有功能实现

## 🔍 **过滤器详细说明**

### BaseDashboardService过滤器支持

本API依赖`BaseDashboardService`的过滤器系统，支持以下过滤条件：

#### 1. **Categories过滤**
- **字段名**: `categories`
- **数据类型**: `List[str]`
- **查询表**: `product_wide_table.category`
- **支持格式**: 分类名称（如："Light Switches", "Dimmer Switches"）
- **实现方法**: `_apply_category_filter()`
- **SQL逻辑**: `WHERE category IN ('Light Switches', 'Dimmer Switches')`

#### 2. **Brands过滤**
- **字段名**: `brands`
- **数据类型**: `List[str]`
- **查询表**: `product_wide_table.brand`
- **支持格式**: 品牌名称（如："Leviton", "Lutron"）
- **实现方法**: `_apply_brand_filter()`
- **SQL逻辑**: `WHERE brand IN ('Leviton', 'Lutron')`

#### 3. **Segments过滤**
- **字段名**: `segments`
- **数据类型**: `List[str]`
- **查询表**: `product_segment_assignments`
- **关联逻辑**: 
  1. 通过哈希项目ID在`product_segment_assignments`表查找`product_id`
  2. 使用`product_id`过滤`product_wide_table.id`
- **支持格式**: 段名称（如："Combination Switches", "Dimmer Switches"）
- **实现方法**: `_apply_segments_filter()`
- **SQL逻辑**: 
  ```sql
  -- 第一步：获取符合segment条件的product_id
  SELECT product_id FROM product_segment_assignments 
  WHERE project_id IN (hashed_project_ids) 
  AND segment_name IN ('Combination Switches')
  
  -- 第二步：使用product_id过滤主表
  WHERE id IN (product_ids_from_step1)
  ```

#### 4. **Extend Fields过滤**
- **字段名**: `extend_fields`
- **数据类型**: `Dict[str, Any]`
- **查询表**: `project_extend_data`
- **关联逻辑**:
  1. 在`project_extend_data`表中查找匹配的`asins`
  2. 使用`asins`过滤`product_wide_table.platform_id`
- **支持格式**: 键值对（如：`{"smart_capability": "Smart"}`）
- **实现方法**: `_apply_extend_fields_filter()`
- **SQL逻辑**:
  ```sql
  -- 查找符合扩展字段条件的ASINs
  SELECT asins FROM project_extend_data 
  WHERE project_id = 'project_id' 
  AND extend->>'smart_capability' = 'Smart'
  
  -- 使用ASINs过滤主表
  WHERE platform_id IN (asins_from_extend_data)
  ```

#### 5. **项目ASIN过滤**（安全边界）
- **查询表**: `projects.selected_product_asins`
- **实现方法**: `_apply_asin_filter()`
- **作用**: 确保所有查询都限制在项目选定的产品范围内
- **SQL逻辑**: `WHERE platform_id IN (project_selected_asins)`

### 过滤器组合逻辑

所有过滤器使用**AND逻辑**组合：
```python
query = self._apply_asin_filter(query)          # 项目ASIN边界
query = self._apply_category_filter(query)      # categories过滤
query = self._apply_brand_filter(query)         # brands过滤  
query = self._apply_segments_filter(query)      # segments过滤
query = self._apply_extend_fields_filter(query) # extend_fields过滤
```

### 数据表依赖关系

```
projects.selected_product_asins 
    ↓ (ASIN边界过滤)
product_wide_table (主表)
    ← product_segment_assignments (segments过滤)
    ← project_extend_data (extend_fields过滤)
    ↓ (brand映射)
product_sales_history_monthly (销售数据)
``` 