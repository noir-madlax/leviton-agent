# Data Transformation Module

## 概述

数据转换模块负责将`amazon_products`表的原始爬虫数据转换为`product_wide_table`表的业务数据格式。这是连接爬虫系统和Dashboard的关键环节。

## 核心功能

### 1. 字段映射和转换
- **直接映射**：将可以直接复制的字段照搬到目标表
- **类型转换**：确保数据类型正确（Decimal, int等）
- **空值处理**：为必需字段设置合理默认值

### 2. 业务字段计算
- **销量解析**：从`recent_sales`文本解析`monthly_sales_volume`
- **收入计算**：`estimated_revenue = price_usd × monthly_sales_volume`
- **包装处理**：从标题解析`pack_count`并计算单价
- **价格计算**：计算`list_price_usd`和`unit_price_calculated`

### 3. 数据质量保证
- **输入验证**：检查必需字段完整性
- **计算验证**：验证业务逻辑正确性
- **范围检查**：确保数值在合理范围内

## 架构设计

```
data_transformation/
├── services/
│   └── transformation_service.py    # 核心转换服务
├── parsers/
│   ├── sales_volume_parser.py      # 销量解析器
│   ├── pack_parser.py              # 包装解析器
│   └── price_calculator.py         # 价格计算器
├── validators/
│   └── data_validator.py           # 数据验证器
├── models.py                       # 数据模型
├── api.py                          # API接口
└── README.md                       # 文档
```

## 数据转换逻辑

### 销量解析
```python
# 示例转换
"3K+ bought in past month" → 3000
"500+ bought in past month" → 500
"1.5K bought" → 1500
```

### 包装处理
```python
# 示例解析
"[50 Pack] CML Decorator Wall Light Switch" → pack_count=50
"Single Pole Switch" → pack_count=1
"12-Pack Case" → pack_count=12
```

### 价格计算
```python
# Pack产品价格逻辑
total_price = 69.34  # 整包价格
pack_count = 50      # 包装数量
unit_price = 69.34 / 50 = 1.39  # 单价

# 字段映射
price_usd = 69.34           # 保持原包装价格
list_price_usd = 1.39       # 单品价格
unit_price_calculated = 1.39 # 单品价格
```

### 收入计算
```python
# 收入计算公式
estimated_revenue = price_usd × monthly_sales_volume

# 示例
price_usd = 42.99
monthly_sales_volume = 3000
estimated_revenue = 42.99 × 3000 = 128970.00
```

## API接口

### 执行转换
```http
POST /api/v1/data-transformation/transform
{
  "limit": 100,
  "batch_size": 50,
  "skip_existing": true,
  "validate_calculations": true,
  "dry_run": false
}
```

### 获取统计
```http
GET /api/v1/data-transformation/stats
```

## 使用方法

### 1. 基本转换
```python
from data_transformation.services import DataTransformationService

service = DataTransformationService()
result = service.transform_batch(limit=100)

print(f"处理了 {result.processed_count} 条记录")
print(f"成功率: {result.summary['success_rate']}%")
```

### 2. 自定义配置
```python
from data_transformation.models import TransformationConfig

config = TransformationConfig(
    batch_size=50,
    skip_existing=True,
    validate_calculations=True,
    dry_run=True  # 测试模式
)

service = DataTransformationService(config)
result = service.transform_batch()
```

### 3. 单独使用解析器
```python
from data_transformation.parsers import SalesVolumeParser, PackParser

# 解析销量
volume = SalesVolumeParser.parse("3K+ bought in past month")  # 返回 3000

# 解析包装
pack_count = PackParser.parse_pack_count("[20 Pack] Light Switch")  # 返回 20
```

## 配置选项

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| batch_size | int | 100 | 批次处理大小 |
| skip_existing | bool | True | 跳过已存在的记录 |
| validate_calculations | bool | True | 验证计算结果 |
| dry_run | bool | False | 测试模式，不写入数据库 |
| log_level | str | "INFO" | 日志级别 |

## 质量保证

### 1. 数据验证
- 必需字段检查
- 数据类型验证
- 业务逻辑验证
- 计算一致性检查

### 2. 错误处理
- 详细错误日志
- 批次级别容错
- 数据回滚支持

### 3. 性能优化
- 批量处理机制
- 数据库连接池
- 内存使用优化

## 注意事项

1. **数据一致性**：转换过程中确保数据完整性
2. **性能考虑**：大批量数据处理时建议分批执行
3. **错误恢复**：支持断点续传和错误重试
4. **监控日志**：关键操作都有详细日志记录

## 扩展指南

### 添加新的解析器
1. 在`parsers/`目录创建新解析器
2. 继承基础解析器类
3. 实现解析逻辑
4. 添加单元测试

### 添加新的验证规则
1. 在`validators/data_validator.py`中添加验证方法
2. 更新验证流程
3. 添加相应测试

### 添加新的API端点
1. 在`api.py`中添加新路由
2. 定义请求/响应模型
3. 实现业务逻辑
4. 添加API文档 