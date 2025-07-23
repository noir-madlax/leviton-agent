# 销售趋势API文档

销售趋势API为前端StackedAreaChart提供品牌月度销售数据，支持revenue和volume双指标，完全聚合处理，前端直接渲染。

## 🛠️ API接口说明

### **POST** `/api/v1/dashboard/sales-trend`

#### 请求体
```json
{
  "project_id": "项目ID",
  "filters": {
    "categories": ["Light Switches"],
    "brands": [],
    "segments": [],
    "extend_fields": {"smart_capability": "Smart"}
  },
  "date_range": {
    "start_date": "2024-01-01",
    "end_date": "2024-06-30"  
  },
  "aggregation": "monthly"
}
```

#### 响应体
```json
{
  "trend_data": [
    {
      "month": "2024-01",
      "Leviton": { "revenue": 850000, "volume": 12000 },
      "Lutron": { "revenue": 720000, "volume": 9000 },
      "GE": { "revenue": 680000, "volume": 11000 }
    },
    {
      "month": "2024-02", 
      "Leviton": { "revenue": 780000, "volume": 11500 },
      "Lutron": { "revenue": 890000, "volume": 12100 },
      "GE": { "revenue": 720000, "volume": 11800 }
    }
  ],
  "brands": ["Leviton", "Lutron", "GE", "Philips", "Legrand"],
  "summary": {
    "total_brands": 5,
    "date_range": {"start": "2024-01", "end": "2024-06"},
    "total_revenue": 15230000,
    "total_volume": 89400
  }
}
```

#### 字段说明
- **trend_data**: 月度趋势数据数组，每月包含Top 10品牌的revenue和volume
- **brands**: Top 10品牌列表（按总revenue排序）
- **summary**: 汇总信息，包含总品牌数、时间范围、总revenue、总volume

#### 错误响应
```json
{
  "status_code": 400,
  "detail": "Invalid project_id or no ASINs found"
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