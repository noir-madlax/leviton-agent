# 链式过滤器系统

这是一个基于责任链模式设计的SQL过滤器系统，用于动态构建复杂的数据库查询条件。

## 🎯 设计目标

- **链式调用**: 支持多个过滤器的链式组合
- **动态SQL**: 根据输入参数动态生成SQL查询
- **参数化查询**: 防止SQL注入，支持参数化查询
- **可扩展**: 易于添加新的过滤器类型
- **类型安全**: 基于Pydantic模型的类型验证

## 📁 文件结构

```
backend/dashboard/charts/filters/
├── __init__.py              # 模块导出
├── chain_filter.py          # 核心过滤器实现
├── test_chain_filter.py     # 测试文件
├── usage_example.py         # 使用示例
└── README.md               # 说明文档
```

## 🚀 快速开始

### 基础用法

```python
from backend.dashboard.charts.filters import build_filtered_sql
from backend.dashboard.charts.base_models import FiltersModel

# 1. 只有project_id (必传)
project_id = "d2c02b80-4c82-44cc-8093-56708a7883f7"
sql, params = build_filtered_sql(project_id)

# 2. 完整过滤条件
filters = FiltersModel(
    brands=["Leviton", "Lutron"],
    categories=["Dimmer Switches", "Light Switches"],
    extend_fields={
        "smart_capability": ["Smart", "Non-Smart"]
    }
)
sql, params = build_filtered_sql(project_id, filters)
```

### 在服务中使用

```python
class BrandAnalysisService:
    def __init__(self, project_id: str):
        self.project_id = project_id
    
    def get_filtered_data(self, filters: FiltersModel = None):
        # 生成SQL
        sql, params = build_filtered_sql(self.project_id, filters)
        
        # 执行查询
        result = self.supabase.rpc('execute_safe_query', {
            'query_text': sql
        }).execute()
        
        return result.data
```

## 🔧 过滤器类型

### 1. ProjectIdFilter (必传)
- **作用**: 基于项目ID过滤产品
- **SQL**: 使用EXISTS子查询关联project_extend_data表
- **必传**: 是

### 2. BrandFilter (可选)
- **作用**: 基于品牌列表过滤
- **SQL**: 使用ANY操作符匹配品牌数组
- **必传**: 否

### 3. CategoryFilter (可选)
- **作用**: 基于类别列表过滤
- **SQL**: 使用ANY操作符匹配类别数组
- **必传**: 否

### 4. ExtendFieldsFilter (可选)
- **作用**: 基于扩展字段过滤
- **SQL**: 使用EXISTS子查询和JSON操作符
- **必传**: 否

## 📊 生成的SQL示例

### 完整过滤条件的SQL

```sql
select distinct pwt.platform_id
from product_wide_table pwt
where 1 = 1
  and (
    exists (
      select 1
      from project_extend_data ped
      where ped.asins = pwt.platform_id
        and ped.project_id = $1
    )
  )
  and (
    pwt.brand = any ($2::text[])
  )
  and (
    pwt.category = any ($3::text[])
  )
  and (
    exists (
      select 1
      from project_extend_data ped
      where ped.asins = pwt.platform_id
        and ped.project_id = $4
        and (
          ped.extend ->> 'smart_capability' = any ($5::text[])
        )
    )
  )
```

### 参数示例

```python
{
    'param_1': 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    'param_2': ['Leviton', 'Lutron'],
    'param_3': ['Dimmer Switches', 'Light Switches'],
    'param_4': 'd2c02b80-4c82-44cc-8093-56708a7883f7',
    'param_5': ['Smart', 'Non-Smart']
}
```

## 🧪 测试

运行测试文件：

```bash
cd backend/dashboard/charts/filters
python test_chain_filter.py
```

运行使用示例：

```bash
python usage_example.py
```

## 🔄 扩展新过滤器

### 1. 创建新的过滤器类

```python
class PriceRangeFilter(BaseFilter):
    def __init__(self):
        super().__init__("price_range")
    
    def apply_filter(self, builder: SQLQueryBuilder, project_id: str, filters: Optional[FiltersModel]) -> SQLQueryBuilder:
        if not filters or not hasattr(filters, 'price_range') or not filters.price_range:
            return builder
        
        min_price, max_price = filters.price_range
        
        if min_price:
            min_param = builder.add_param(min_price)
            builder.add_where_condition(f"{builder.alias}.price_usd >= {min_param}")
        
        if max_price:
            max_param = builder.add_param(max_price)
            builder.add_where_condition(f"{builder.alias}.price_usd <= {max_param}")
        
        return builder
```

### 2. 更新过滤器链

```python
def _build_default_chain(self) -> BaseFilter:
    project_filter = ProjectIdFilter()
    brand_filter = BrandFilter()
    category_filter = CategoryFilter()
    price_filter = PriceRangeFilter()  # 新增
    extend_filter = ExtendFieldsFilter()
    
    # 更新链式关系
    project_filter.set_next(brand_filter)\
                  .set_next(category_filter)\
                  .set_next(price_filter)\
                  .set_next(extend_filter)
    
    return project_filter
```

## 🎨 设计模式

### 责任链模式 (Chain of Responsibility)
- 每个过滤器负责处理特定的过滤逻辑
- 过滤器可以选择处理请求或传递给下一个过滤器
- 支持动态组合和扩展

### 建造者模式 (Builder)
- SQLQueryBuilder负责逐步构建SQL查询
- 支持链式调用添加查询条件
- 最终生成完整的SQL和参数

## 🚨 注意事项

1. **project_id必传**: 第一个过滤器ProjectIdFilter要求project_id不能为空
2. **参数化查询**: 所有参数都通过占位符传递，防止SQL注入
3. **性能考虑**: EXISTS子查询在大数据量时可能影响性能，建议添加适当索引
4. **扩展字段**: 支持单值和数组值的扩展字段过滤

## 📈 性能优化建议

1. **数据库索引**:
   ```sql
   CREATE INDEX idx_product_wide_table_brand ON product_wide_table(brand);
   CREATE INDEX idx_product_wide_table_category ON product_wide_table(category);
   CREATE INDEX idx_project_extend_data_asins ON project_extend_data(asins);
   CREATE INDEX idx_project_extend_data_project_id ON project_extend_data(project_id);
   ```

2. **查询优化**: 考虑使用JOIN替代EXISTS子查询（在某些情况下）

3. **缓存策略**: 对频繁查询的结果进行缓存
