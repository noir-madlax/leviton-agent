# 现在产品Wide表，数据来源流程还没有

## 🔍 核心问题

**缺失的关键环节**: 爬虫原始数据(`amazon_products`, `amazon_reviews`) → `product_wide_table` 的转换步骤完全缺失。

目前所有Dashboard都依赖 `product_wide_table`，但这个表的数据来源和填充机制未定义，导致数据流程中存在断层。

## 📊 数据表层次结构对比

### 现状 (有问题)

```
爬虫数据 → amazon_products, amazon_reviews
    ❌ 断层：没有转换机制
Dashboard → 直接读取 product_wide_table (数据来源不明)
```

### 目标架构 (完整流程)

```
第一层：原始数据层
├── amazon_products (爬取的原始产品数据)
├── amazon_reviews (爬取的原始评论数据)  
└── homedepot_products (未来扩展)

第二层：统一数据层 (新增转换处理)
├── product_wide_table (多数据源统一格式)
└── product_review_analysis (评论分析结果)

第三层：项目业务层
├── projects (用户筛选的产品集合)
└── product_segment_* (产品细分相关表)

第四层：展示层
└── Dashboard APIs (基于项目ASIN过滤)
```

## ⏰ 数据处理时机

### 数据导入阶段 (立即处理)

1. **爬虫完成** → 数据存入原始表 (`amazon_products`)
2. **立即转换** → 自动转换并合并到 `product_wide_table（这个步骤没有！！！）`
3. **数据清洗** → 去重、标准化、字段映射

### 项目创建阶段 (用户操作时)

1. **数据筛选** → 从 `product_wide_table` 按条件筛选
2. **项目保存** → 记录筛选条件和ASIN列表到 `projects`
3. **产品细分** → 调用 `product_segment` 模块处理

### Dashboard展示阶段 (实时查询)

1. **ASIN过滤** → 基于项目的ASIN列表过滤数据
2. **聚合计算** → 从 `product_wide_table` 计算展示指标

## 🔧 需要调整的关键点

### 1. 新增数据转换服务

- 创建原始数据到Wide表的转换逻辑
- 支持多数据源统一格式化
- 处理字段映射和数据清洗

### 2. 修改数据导入流程

- 爬虫完成后自动触发转换
- 确保Wide表数据实时更新
- 添加转换状态跟踪

### 3. Wide表字段补充

- 添加缺失的业务字段 (月销量、收入估算等)
- 增加数据溯源字段 (来源表、批次ID)
- 优化索引支持Dashboard查询

### 4. 数据一致性保证

- 建立原始表到Wide表的映射关系
- 支持增量更新和全量重建
- 添加数据校验机制
