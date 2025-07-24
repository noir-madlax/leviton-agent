# Data Transformation Module

## 概述

数据转换模块负责将`amazon_products`表的原始爬虫数据转换为`product_wide_table`表的业务数据格式。这是连接爬虫系统和Dashboard的关键环节。

## 核心功能

### 1. 字段映射和转换
- **直接映射**：将可以直接复制的字段照搬到目标表
- **类型转换**：确保数据类型正确（Decimal, int等）
- **空值处理**：为必需字段设置合理默认值

### 2. 业务字段计算
- **销量解析**：从`recent_sales`文本解析`past_year_volume`
- **收入计算**：`past_year_revenue = price_usd × past_year_volume`
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
past_year_revenue = price_usd × past_year_volume

例如:
price_usd = 42.99
past_year_volume = 3000
past_year_revenue = 42.99 × 3000 = 128970.00
```