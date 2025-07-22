# 销售趋势API模版工程

这是一个专门用于Matrix Chart的销售价格和趋势分析API的完整模版工程。该API遵循项目的统一API规范，提供销售数据的时间序列分析功能。

## 📁 项目结构

```
backend/dashboard/api/trending/
├── models.py              # API请求和响应模型定义
├── services.py           # 销售趋势数据服务类
├── api.py               # FastAPI路由接口
├── readme.md            # 本文档
├── api-rule.mdc         # API规则配置（待完善）
├── leviton_B08SJ3Z8XD_sales_20250720_184936.csv  # 示例数据
└── test/
    ├── __init__.py
    ├── sample_requests.json   # 测试请求示例
    └── test_curl.sh          # curl测试脚本
```

## 🚀 API概览

### 接口信息
- **端点**: `POST /api/v1/dashboard/trending/sales-trend`
- **方法**: POST
- **Content-Type**: application/json
- **响应格式**: JSON

### 核心功能
1. **销售趋势分析** - 提供时间序列的销量、价格、收入数据
2. **统计汇总** - 计算总销量、平均价格、增长率等关键指标
3. **灵活筛选** - 支持项目标准筛选条件和时间范围筛选
4. **多维度查询** - 支持单产品或项目汇总分析

## 📊 数据结构

### CSV数据结构（参考文件：leviton_B08SJ3Z8XD_sales_20250720_184936.csv）

| 字段名 | 类型 | 描述 | 示例 |
|--------|------|------|------|
| date | string | 日期 (YYYY-MM-DD) | "2024-07-19" |
| estimated_units_sold | integer | 估计销售量 | 53 |
| last_known_price | float | 最后已知价格(USD) | 3.5 |

### 数据库表结构建议

**表名**: `sales_trend_data`

```sql
CREATE TABLE sales_trend_data (
    id SERIAL PRIMARY KEY,
    asin VARCHAR(20) NOT NULL,                    -- 产品ASIN
    date DATE NOT NULL,                           -- 销售日期
    estimated_units_sold INTEGER NOT NULL,       -- 估计销售量
    last_known_price DECIMAL(10,2) NOT NULL,     -- 最后已知价格
    estimated_revenue DECIMAL(12,2),             -- 估计收入（计算字段）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_asin_date (asin, date),
    INDEX idx_date (date),
    
    -- 约束
    UNIQUE KEY unique_asin_date (asin, date)
);
```

## 🎯 API规范

### 前后端契约设计

遵循项目统一的API设计模式：

#### 1. 请求格式 (SalesTrendRequest)
```json
{
  "project_id": "string (必填)",
  "filters": {
    "categories": ["string"],
    "brands": ["string"], 
    "segments": ["string"],
    "extend_fields": {"key": "value"}
  },
  "date_range": {
    "start_date": "YYYY-MM-DD",
    "end_date": "YYYY-MM-DD"
  },
  "asin": "string (可选，不填则返回项目汇总)",
  "metric_type": "sales|price|revenue (默认: sales)",
  "aggregation": "daily|weekly|monthly (默认: daily)"
}
```

#### 2. 响应格式 (SalesTrendResponse)
```json
{
  "trend_data": [
    {
      "date": "2024-07-19",
      "estimated_units_sold": 53,
      "last_known_price": 3.5,
      "estimated_revenue": 185.5
    }
  ],
  "summary_stats": {
    "total_period_sales": 18234,
    "average_daily_sales": 95.3,
    "average_price": 3.52,
    "price_volatility": 0.85,
    "total_revenue": 64183.68,
    "growth_rate": 15.2
  },
  "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
  "asin": "B08SJ3Z8XD",
  "date_range": {
    "start_date": "2024-07-19",
    "end_date": "2025-07-19"
  },
  "metric_type": "sales",
  "aggregation": "daily",
  "total_data_points": 365,
  "applied_filters": {}
}
```

## 🔧 技术实现

### 服务架构
- **继承BaseDashboardService** - 自动获得项目ASIN过滤和标准筛选功能
- **遵循装饰器模式** - 使用`@log_request_response`记录请求日志
- **Pydantic模型验证** - 确保请求响应数据的类型安全
- **Mock数据支持** - 便于开发测试，实际部署时替换为数据库查询

### 核心组件

#### 1. 模型层 (models.py)
- `SalesTrendRequest` - 请求模型，支持标准筛选条件和业务参数
- `SalesTrendResponse` - 响应模型，包含趋势数据和统计信息
- `SalesTrendDataPoint` - 单个数据点模型
- `SalesTrendSummaryStats` - 汇总统计模型

#### 2. 服务层 (services.py) 
- `SalesTrendService` - 继承BaseDashboardService
- 支持ASIN筛选、日期范围筛选、数据聚合
- 提供统计计算功能（增长率、波动率等）
- Mock数据生成器（便于开发测试）

#### 3. API层 (api.py)
- FastAPI路由实现
- 统一的错误处理
- 请求参数验证和响应格式化

## 🧪 测试指南

### 1. 使用curl测试
```bash
# 运行测试脚本
cd backend/dashboard/api/trending/test
./test_curl.sh
```

### 2. 手动测试示例

#### 基础请求
```bash
curl -X POST "http://localhost:8000/api/v1/dashboard/trending/sales-trend" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "asin": "B08SJ3Z8XD",
    "metric_type": "sales",
    "aggregation": "daily"
  }'
```

#### 带筛选条件的请求
```bash
curl -X POST "http://localhost:8000/api/v1/dashboard/trending/sales-trend" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "d2c02b80-4c82-44cc-8093-56708a7883f7",
    "filters": {
      "categories": ["Light Switches"],
      "brands": ["Leviton"],
      "segments": ["Premium"]
    },
    "date_range": {
      "start_date": "2024-07-01",
      "end_date": "2024-12-31"
    },
    "asin": "B08SJ3Z8XD",
    "metric_type": "revenue"
  }'
```

### 3. 测试文件
- `sample_requests.json` - 包含各种测试场景的请求示例
- `test_curl.sh` - 自动化curl测试脚本

## 📈 业务逻辑说明

### 数据处理流程
1. **项目ASIN过滤** - 自动应用项目配置的产品ASIN列表
2. **标准筛选应用** - 处理categories, brands, segments, extend_fields
3. **时间范围筛选** - 按指定日期范围过滤数据
4. **数据聚合** - 按日/周/月聚合（目前只实现daily）
5. **统计计算** - 生成汇总统计信息

### 关键指标计算
- **增长率**: (期末销量 - 期初销量) / 期初销量 × 100%
- **价格波动率**: 价格数据的标准差
- **估计收入**: 销量 × 价格

## 🔄 集成指南

### 前端集成
参考现有dashboard组件的调用方式：

```typescript
// 使用现有的callDashboardAPI函数
const salesTrendData = await callDashboardAPI('trending/sales-trend', {
  project_id: projectId,
  filters: {
    categories: selectedCategories,
    brands: selectedBrands
  },
  asin: targetAsin,
  date_range: {
    start_date: '2024-01-01',
    end_date: '2024-12-31'
  },
  metric_type: 'sales'
});
```

### 后端路由注册
在主应用中注册路由：

```python
from backend.dashboard.api.trending.api import router as trending_router

app.include_router(
    trending_router, 
    prefix="/api/v1/dashboard/trending",
    tags=["trending"]
)
```

## 🚧 待完善功能

1. **数据库查询实现** - 替换Mock数据为实际查询
2. **周/月数据聚合** - 实现weekly和monthly聚合逻辑
3. **更多统计指标** - 添加移动平均、趋势预测等
4. **缓存优化** - 添加数据缓存提高性能
5. **批量导入工具** - CSV数据导入Supabase的工具

## 📋 数据导入指南

### CSV导入Supabase步骤
1. 在Supabase中创建`sales_trend_data`表
2. 使用Supabase Dashboard的导入功能
3. 或者使用Python脚本批量导入：

```python
import pandas as pd
from supabase import create_client

# 读取CSV
df = pd.read_csv('leviton_B08SJ3Z8XD_sales_20250720_184936.csv')

# 添加ASIN列
df['asin'] = 'B08SJ3Z8XD'

# 计算estimated_revenue
df['estimated_revenue'] = df['estimated_units_sold'] * df['last_known_price']

# 导入Supabase
supabase = create_client(url, key)
result = supabase.table('sales_trend_data').insert(df.to_dict('records')).execute()
```

## 🎨 前端图表建议

该API返回的数据非常适合以下图表类型：
- **折线图** - 显示销量/价格随时间的变化趋势
- **双轴图** - 同时显示销量和价格走势
- **柱状图** - 按周/月聚合的销量对比
- **统计卡片** - 显示汇总统计信息

---

**注意**: 这是一个模版工程，目前使用Mock数据。在生产环境中需要：
1. 实现真实的数据库查询逻辑
2. 完善错误处理和日志记录
3. 添加API认证和权限控制
4. 进行性能优化和缓存设计
