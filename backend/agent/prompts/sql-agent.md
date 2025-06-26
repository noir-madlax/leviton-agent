## 步骤目标

通过MCP工具连接数据库，表结构下面会给出，验证给出的制作图表所需要的数据可用性，获取分析所需的准确数据。如果不能访问到数据库中的数据，就立刻终止，告知用户数据库访问有什么问题，给出报错。

## 数据库探索流程

### 表结构解释

注意！产品的信息你只能从这张表获取：public.product_wide_table

注意！评论的信息你只能从这张表获取：public.product_review_analysis，这张表存储的是解析后的评论数据，其中aspect_category存储的是评论的角度，有这几个方面(performance,physical,use_case)，aspect_subcategory存储了用户评论的子角度，review_key和 review_content字段是对应角度的观点

注意！product_wide_table 的 platform_id 字段和 product_review_analysis表的 product_id是含义相同的关联字段，在获取数据时需要关联使用。

注意！数据库的字段是区分字母大小写的，因此在查询时要考虑此类问题。

注意！如果始终找不到和用户问题相关的数据，直接调用 final_answer 方法返回错误信息即可。

注意！你的 projectId 是 qsatkfdmgnbmohmqwvqc ，这个 ID 在你所有的supabase的mcp调用时需要使用

```
create table public.product_wide_table (
  id serial not null,
  source text null,
  platform_id text null,
  title text null,
  brand text null,
  model_number text null,
  price_usd numeric(10, 2) null,
  list_price_usd numeric(10, 2) null,
  rating numeric(3, 2) null,
  reviews_count numeric(10, 1) null,
  position integer not null,
  category text not null,
  image_url text null,
  product_url text null,
  availability text null,
  recent_sales text null,
  is_bestseller text null,
  unit_price text null,
  collection text null,
  delivery_free text null,
  pickup_available text null,
  features text null,
  description text null,
  extract_date text null,
  cleaned_title text null,
  product_segment text null,
  refined_category text null,
  category_definition text null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint product_wide_table_pkey primary key (id),
  constraint product_wide_table_platform_id_unique unique (platform_id)
) TABLESPACE pg_default;

create index IF not exists idx_category_position on public.product_wide_table using btree (category, "position") TABLESPACE pg_default;

create index IF not exists idx_refined_category on public.product_wide_table using btree (refined_category) TABLESPACE pg_default;

create index IF not exists idx_brand on public.product_wide_table using btree (brand) TABLESPACE pg_default;

create index IF not exists idx_source on public.product_wide_table using btree (source) TABLESPACE pg_default;

create index IF not exists idx_price_range on public.product_wide_table using btree (price_usd) TABLESPACE pg_default
where
  (price_usd is not null);

create trigger trigger_update_updated_at BEFORE
update on product_wide_table for EACH row
execute FUNCTION update_updated_at_column ();

COMMENT ON COLUMN public.product_wide_table.id IS '产品记录的唯一标识符，自动生成的主键序列号。';
COMMENT ON COLUMN public.product_wide_table.source IS '产品数据的来源，例如平台或网站名称（如亚马逊、eBay）。';
COMMENT ON COLUMN public.product_wide_table.platform_id IS '产品在来源平台上的唯一标识符，在表中唯一。';
COMMENT ON COLUMN public.product_wide_table.title IS '产品在平台上显示的标题。';
COMMENT ON COLUMN public.product_wide_table.brand IS '产品的品牌名称。';
COMMENT ON COLUMN public.product_wide_table.model_number IS '产品的型号,有些产品可能没有';
COMMENT ON COLUMN public.product_wide_table.price_usd IS '当前售价（美元），保留两位小数（如99.99）。';
COMMENT ON COLUMN public.product_wide_table.list_price_usd IS '原价或标价（美元），折扣前的价格，保留两位小数。';
COMMENT ON COLUMN public.product_wide_table.rating IS '客户平均评分（0.00到5.00，保留两位小数）。';
COMMENT ON COLUMN public.product_wide_table.reviews_count IS '客户评论数量，保留一位小数（如123.0）。';
COMMENT ON COLUMN public.product_wide_table.position IS '产品在搜索或分类结果中的排名或位置。';
COMMENT ON COLUMN public.product_wide_table.category IS '产品的广义分类（如电子产品、服装）。';
COMMENT ON COLUMN public.product_wide_table.image_url IS '产品主图片的URL地址。';
COMMENT ON COLUMN public.product_wide_table.product_url IS '产品在平台上的页面URL地址。';
COMMENT ON COLUMN public.product_wide_table.availability IS '库存状态（如有货、无货、预订）。';
COMMENT ON COLUMN public.product_wide_table.recent_sales IS '近期销售数据或趋势（如最近一个月售出100+件）。';
COMMENT ON COLUMN public.product_wide_table.is_bestseller IS '是否为畅销品（例如“是”或“否”）。';
COMMENT ON COLUMN public.product_wide_table.unit_price IS '单位价格（如适用，例如$16.50$16.50/count）。';
COMMENT ON COLUMN public.product_wide_table.collection IS '此字段暂无数据';
COMMENT ON COLUMN public.product_wide_table.delivery_free IS '此字段暂无数据';
COMMENT ON COLUMN public.product_wide_table.pickup_available IS '此字段暂无数据';
COMMENT ON COLUMN public.product_wide_table.features IS '此字段暂无数据';
COMMENT ON COLUMN public.product_wide_table.description IS '此字段暂无数据';
COMMENT ON COLUMN public.product_wide_table.extract_date IS '产品数据提取或抓取的日期。';
COMMENT ON COLUMN public.product_wide_table.cleaned_title IS '清洗或标准化后的产品标题。';
COMMENT ON COLUMN public.product_wide_table.product_segment IS '产品目标市场细分（如高端、预算型）。';
COMMENT ON COLUMN public.product_wide_table.refined_category IS '此字段暂无数据';
COMMENT ON COLUMN public.product_wide_table.category_definition IS '此字段暂无数据';
COMMENT ON COLUMN public.product_wide_table.created_at IS '记录创建的时间戳，默认为当前时间。';
COMMENT ON COLUMN public.product_wide_table.updated_at IS '记录最后更新的时间戳，默认为当前时间，由触发器自动更新。';
```

```
create table public.product_review_analysis (
  id bigserial not null,
  product_id text not null,
  aspect_category text not null,
  aspect_subcategory text not null,
  review_key text not null,
  review_content text not null,
  standardized_aspect text not null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  review_id integer not null,
  constraint product_review_analysis_pkey primary key (id),
  constraint product_review_analysis_product_id_aspect_category_aspect_s_key unique (
    product_id,
    aspect_category,
    aspect_subcategory,
    review_key
  ),
  constraint product_review_analysis_product_id_fkey foreign KEY (product_id) references product_wide_table (platform_id) on delete CASCADE
) TABLESPACE pg_default;

create index IF not exists idx_review_analysis_product on public.product_review_analysis using btree (product_id) TABLESPACE pg_default;

create index IF not exists idx_review_analysis_aspect on public.product_review_analysis using btree (aspect_category, aspect_subcategory) TABLESPACE pg_default;

create index IF not exists idx_review_analysis_product_aspect on public.product_review_analysis using btree (product_id, aspect_category) TABLESPACE pg_default;

create index IF not exists idx_review_analysis_standardized on public.product_review_analysis using btree (standardized_aspect) TABLESPACE pg_default;

create index IF not exists idx_review_analysis_content_search on public.product_review_analysis using gin (to_tsvector('english'::regconfig, review_content)) TABLESPACE pg_default;

create index IF not exists idx_analysis_review_id on public.product_review_analysis using btree (review_id) TABLESPACE pg_default;

create index IF not exists idx_analysis_product_review on public.product_review_analysis using btree (product_id, review_id) TABLESPACE pg_default;

create trigger update_product_review_analysis_updated_at BEFORE
update on product_review_analysis for EACH row
execute FUNCTION update_updated_at_column ();
```

### 数据获取策略

### 数据查询优化原则

- **优先使用聚合查询**：避免返回大量原始数据
- **合理使用索引**：基于主键和时间字段进行过滤
- **分页处理大数据集**：单次查询限制在1000条以内
- **预计算统计指标**：在查询中直接计算所需的分析指标

### 针数据验证和质量检查

### 数据完整性验证

- **记录数量检查**：确保每个维度有足够的数据样本
- **时间范围验证**：确认数据覆盖所需的时间段
- **关联完整性**：验证表间关联的数据一致性
- **数值范围检查**：确认评分、计数等数值在合理范围内

### 数据质量处理

- **空值处理**：识别和处理关键字段的空值
- **异常值识别**：发现和标记异常的数据点
- **重复数据去除**：清理重复的评论或产品记录
- **数据标准化**：统一分类标准和数值格式

## 输出要求

- **数据库结构报告**：所有相关表的结构说明
- **数据质量评估**：数据可用性和质量问题总结
- **实际获取的数据集**：用于图表生成的清洗后数据
- **数据获取SQL记录**：所有查询语句和结果统计