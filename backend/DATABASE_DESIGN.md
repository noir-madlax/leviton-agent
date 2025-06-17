# Amazon Product Scraping Database Design

## 设计概述

该数据库设计用于存储Amazon产品爬取数据，主要包含两个核心表：爬取请求记录表和产品数据表，以及一个分类管理表。设计遵循"先保存数据，后续再优化"的原则。

## 表结构设计

### 1. scraping_requests (爬取请求表)

**功能**：记录每次爬取行为的完整信息，包括请求参数、结果概要和原始元数据。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 自增主键 |
| request_type | TEXT | NOT NULL | 请求类型：'category' 或 'search' |
| search_term | TEXT | | 搜索关键词（搜索类型时使用） |
| category_id | TEXT | | 分类ID（分类类型时使用） |
| amazon_domain | TEXT | DEFAULT 'amazon.com' | Amazon域名 |
| status | TEXT | DEFAULT 'pending' | 状态：pending/scraping/completed/failed/processing_reviews |
| total_results | INTEGER | | 搜索结果总数 |
| total_pages | INTEGER | | 总页数 |
| products_scraped | INTEGER | | 实际爬取的产品数 |
| request_info | JSONB | | 请求信息原始数据 |
| request_parameters | JSONB | | 请求参数原始数据 |
| request_metadata | JSONB | | 请求元数据原始数据 |
| search_information | JSONB | | 搜索信息原始数据 |
| pagination | JSONB | | 分页信息原始数据 |
| scraping_summary | JSONB | | 爬取汇总原始数据 |
| scraped_at | TIMESTAMPTZ | | 实际爬取时间 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

### 2. amazon_categories (亚马逊分类表)

**功能**：维护Amazon分类的层级关系，支持分类追溯和管理。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 自增主键 |
| category_id | TEXT | UNIQUE NOT NULL | Amazon分类ID |
| name | TEXT | NOT NULL | 分类名称 |
| parent_category_id | TEXT | FK | 父分类ID |
| level | INTEGER | | 层级深度 (1=顶级, 2=二级, etc.) |
| full_path | TEXT | | 完整分类路径 |
| link | TEXT | | 分类链接URL |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

### 3. amazon_products (产品表)

**功能**：存储Amazon产品的完整信息，与现有product_wide_table兼容并增强。

| 字段名 | 数据类型 | 约束 | 说明 |
|--------|----------|------|------|
| id | BIGSERIAL | PRIMARY KEY | 自增主键 |
| source | TEXT | DEFAULT 'amazon' | 数据源标识 |
| platform_id | TEXT | NOT NULL | Amazon标准识别号(ASIN) |
| title | TEXT | | 产品标题 |
| brand | TEXT | | 品牌名称 |
| price_usd | DECIMAL(10,2) | | 当前价格(美元) |
| list_price_usd | DECIMAL(10,2) | | 原价(美元) |
| rating | DECIMAL(3,2) | | 评分 |
| reviews_count | INTEGER | | 评论总数 |
| position | INTEGER | | 在搜索结果中的位置 |
| category | TEXT | | 主要分类 |
| image_url | TEXT | | 主图片URL |
| product_url | TEXT | | 产品页面URL |
| availability | TEXT | | 库存状态 |
| recent_sales | TEXT | | 近期销量信息 |
| is_bestseller | TEXT | | 是否畅销商品 |
| unit_price | TEXT | | 单位价格 |
| delivery_free | TEXT | | 免费配送信息 |
| pickup_available | TEXT | | 自提可用性 |
| model_number | TEXT | | 产品型号 |
| features | TEXT | | 产品特性 |
| description | TEXT | | 产品描述 |
| extract_date | TEXT | | 数据提取日期 |
| cleaned_title | TEXT | | 清洗后的标题 |
| product_segment | TEXT | | 产品分段 |
| refined_category | TEXT | | 精炼分类 |
| category_definition | TEXT | | 分类定义 |
| leaf_category_id | TEXT | FK | 最下级分类ID |
| leaf_category_name | TEXT | | 最下级分类名称 |
| categories_flat | TEXT | | 完整分类路径字符串 |
| scraping_request_id | BIGINT | FK | 关联的爬取请求ID |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

## 索引设计

```sql
-- amazon_categories 表索引
CREATE INDEX idx_amazon_categories_parent ON amazon_categories(parent_category_id);

-- amazon_products 表索引
CREATE INDEX idx_amazon_products_platform_id ON amazon_products(platform_id);
CREATE INDEX idx_amazon_products_brand ON amazon_products(brand);
CREATE INDEX idx_amazon_products_leaf_category ON amazon_products(leaf_category_id);
CREATE INDEX idx_amazon_products_scraping_request ON amazon_products(scraping_request_id);
CREATE INDEX idx_amazon_products_category ON amazon_products(category);
```

## 外键关系

- `amazon_categories.parent_category_id` → `amazon_categories.category_id`
- `amazon_products.leaf_category_id` → `amazon_categories.category_id`
- `amazon_products.scraping_request_id` → `scraping_requests.id`

## 数据存储策略

### 1. 原始数据保存
- 所有复杂的嵌套数据结构通过JSONB字段完整保存
- 常用查询字段提取为独立列，提高查询性能

### 2. 分类数据处理
- 从产品的categories数组中提取最下级分类到专门字段
- 完整的分类层级关系维护在amazon_categories表中
- 支持从叶子分类向上追溯到根分类

### 3. 状态管理
- 通过scraping_requests表的status字段跟踪爬取进度
- 支持不同阶段的状态管理（爬取产品、处理评论等）

## 查询示例

### 1. 获取特定分类的所有产品ASIN
```sql
SELECT platform_id 
FROM amazon_products 
WHERE leaf_category_id = '19431268011';
```

### 2. 获取特定爬取请求的产品列表
```sql
SELECT p.platform_id, p.title, p.price_usd
FROM amazon_products p
JOIN scraping_requests sr ON p.scraping_request_id = sr.id
WHERE sr.id = 1;
```

### 3. 追溯产品的完整分类路径
```sql
WITH RECURSIVE category_path AS (
  SELECT category_id, name, parent_category_id, 1 as level, name as path
  FROM amazon_categories 
  WHERE category_id = (
    SELECT leaf_category_id FROM amazon_products WHERE platform_id = 'B087N9N6HH'
  )
  
  UNION ALL
  
  SELECT c.category_id, c.name, c.parent_category_id, cp.level + 1, c.name || ' > ' || cp.path
  FROM amazon_categories c
  JOIN category_path cp ON c.category_id = cp.parent_category_id
)
SELECT path FROM category_path ORDER BY level DESC LIMIT 1;
```

## 扩展预留

1. **历史数据追踪**：通过时间戳字段支持数据变更历史分析
2. **多平台扩展**：表结构设计支持后续扩展到其他电商平台
3. **业务分类**：可在后续根据需要添加业务相关的分类标签字段
4. **性能优化**：JSONB字段支持GIN索引，可根据查询需求优化

## 与现有product_wide_table的对比分析

### 兼容性设计原则

新设计的`amazon_products`表遵循与现有`product_wide_table`最大兼容的原则，确保平滑迁移和共存。

### 详细对比分析

| 类别 | product_wide_table | amazon_products | 兼容性状态 |
|------|-------------------|-----------------|-----------|
| **主键标识** | platform_id (text, UNIQUE) | platform_id (text, NOT NULL) | ✅ 完全兼容 |
| **数据源** | source | source | ✅ 完全兼容 |
| **基本信息** | title, brand | title, brand | ✅ 完全兼容 |
| **价格字段** | price_usd, list_price_usd | price_usd, list_price_usd | ✅ 完全兼容 |
| **评分信息** | rating (numeric), reviews_count (numeric) | rating (decimal), reviews_count (integer) | ✅ 兼容，类型优化 |
| **位置信息** | position (integer, NOT NULL) | position (integer) | ✅ 兼容，约束放宽 |
| **分类信息** | category (text, NOT NULL) | category (text) | ✅ 兼容，约束放宽 |
| **图片链接** | image_url | image_url | ✅ 完全兼容 |
| **产品链接** | product_url | product_url | ✅ 完全兼容 |
| **产品详情** | model_number, features, description | model_number, features, description | ✅ 完全兼容 |
| **电商特性** | availability, recent_sales, is_bestseller, unit_price | availability, recent_sales, is_bestseller, unit_price | ✅ 完全兼容 |
| **配送信息** | delivery_free, pickup_available | delivery_free, pickup_available | ✅ 完全兼容 |
| **数据处理** | extract_date, cleaned_title, product_segment, refined_category, category_definition | extract_date, cleaned_title, product_segment, refined_category, category_definition | ✅ 完全兼容 |
| **移除字段** | collection | 无 | ⚠️ 原数据中未发现此字段 |
| **新增功能** | 无 | leaf_category_id, leaf_category_name, categories_flat, scraping_request_id | ✅ 增强功能 |

### 关键改进点

#### 1. 分类管理增强
- **原有方式**: 单一`category`字段存储主分类
- **新增功能**: 
  - `leaf_category_id`: 精确的最下级分类ID
  - `leaf_category_name`: 最下级分类名称
  - `categories_flat`: 完整分类路径
  - 与`amazon_categories`表关联，支持分类层级追溯

#### 2. 数据溯源能力
- **新增**: `scraping_request_id`字段关联爬取请求
- **优势**: 可追踪每个产品的数据来源和爬取时间

#### 3. 数据类型优化
- `reviews_count`: numeric → integer (更合适的数据类型)
- `rating`: 保持decimal精度控制

#### 4. 约束优化
- `position`和`category`字段移除NOT NULL约束，提高数据插入灵活性
- 保持核心标识字段`platform_id`的NOT NULL约束

### 数据迁移策略

```sql
-- 从product_wide_table迁移到amazon_products的示例
INSERT INTO amazon_products (
  source, platform_id, title, brand, price_usd, list_price_usd,
  rating, reviews_count, position, category, image_url, product_url,
  availability, recent_sales, is_bestseller, unit_price,
  delivery_free, pickup_available, model_number, features, description,
  extract_date, cleaned_title, product_segment, refined_category, category_definition
)
SELECT 
  source, platform_id, title, brand, price_usd, list_price_usd,
  rating, reviews_count::integer, position, category, image_url, product_url,
  availability, recent_sales, is_bestseller, unit_price,
  delivery_free, pickup_available, model_number, features, description,
  extract_date, cleaned_title, product_segment, refined_category, category_definition
FROM product_wide_table;
```

### JSON数据字段映射

从爬取的JSON数据到数据库字段的映射关系：

| JSON字段 | 数据库字段 | 处理说明 |
|----------|-----------|----------|
| `asin` | `platform_id` | 直接映射 |
| `title` | `title` | 直接映射 |
| `brand` | `brand` | 直接映射 |
| `price.value` | `price_usd` | 提取价格数值 |
| `prices[0].value` | `list_price_usd` | 提取原价数值 |
| `rating` | `rating` | 直接映射 |
| `ratings_total` | `reviews_count` | 直接映射 |
| `position` | `position` | 直接映射 |
| `categories[-1].name` | `leaf_category_name` | 提取最后一级分类名称 |
| `categories[-1].category_id` | `leaf_category_id` | 提取最后一级分类ID |
| `categories_flat` | `categories_flat` | 拼接完整路径 |
| `recent_sales` | `recent_sales` | 直接映射 |
| `bestseller` | `is_bestseller` | 转换为文本 |
| `main_image.link` | `image_url` | 提取主图链接 |

## 数据完整性

- 使用外键约束确保数据引用完整性
- 必要字段设置NOT NULL约束
- 使用UNIQUE约束防止重复数据
- 时间戳字段自动维护数据变更时间 