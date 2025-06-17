-- 创建产品评论分析表
-- 迁移名称: create_product_review_analysis_table
-- 作用: 存储每个产品在不同属性维度下的评论分析结果

CREATE TABLE product_review_analysis (
    id BIGSERIAL PRIMARY KEY,
    
    -- 核心关联字段
    product_id TEXT NOT NULL,                    -- 关联product_wide_table.platform_id
    
    -- 评论分析维度字段
    aspect_category TEXT NOT NULL,               -- physical/performance/use_case
    aspect_subcategory TEXT NOT NULL,            -- buttons/magnets/connectivity等具体子类别
    review_key TEXT NOT NULL,                    -- 原始标识符(A@, B@等)
    review_content TEXT NOT NULL,               -- 评论内容（@后的部分）
    standardized_aspect TEXT NOT NULL,          -- 标准化的方面名称（如Button Interface）
    
    -- 元数据字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 约束
    FOREIGN KEY (product_id) REFERENCES product_wide_table(platform_id) ON DELETE CASCADE,
    
    -- 唯一约束：同一产品的同一维度下不能有重复的review_key
    UNIQUE(product_id, aspect_category, aspect_subcategory, review_key)
);

-- 创建索引优化查询性能

-- 1. 产品维度查询优化（最常用）
CREATE INDEX idx_review_analysis_product 
ON product_review_analysis(product_id);

-- 2. 属性维度查询优化
CREATE INDEX idx_review_analysis_aspect 
ON product_review_analysis(aspect_category, aspect_subcategory);

-- 3. 复合查询优化（产品+维度）
CREATE INDEX idx_review_analysis_product_aspect 
ON product_review_analysis(product_id, aspect_category);

-- 4. 标准化方面查询优化
CREATE INDEX idx_review_analysis_standardized 
ON product_review_analysis(standardized_aspect);

-- 5. 全文搜索索引（用于评论内容搜索）
CREATE INDEX idx_review_analysis_content_search 
ON product_review_analysis USING gin(to_tsvector('english', review_content));

-- 添加表注释
COMMENT ON TABLE product_review_analysis IS '产品评论分析表：存储每个产品在不同属性维度下的评论分析结果';
COMMENT ON COLUMN product_review_analysis.product_id IS '产品ID，关联product_wide_table.platform_id';
COMMENT ON COLUMN product_review_analysis.aspect_category IS '属性大类：physical/performance/use_case';
COMMENT ON COLUMN product_review_analysis.aspect_subcategory IS '属性子类：如buttons、magnets、connectivity等';
COMMENT ON COLUMN product_review_analysis.review_key IS '原始评论标识符，如A@、B@等';
COMMENT ON COLUMN product_review_analysis.review_content IS '评论内容，从review_key中@后提取';
COMMENT ON COLUMN product_review_analysis.standardized_aspect IS '标准化的方面名称，如Button Interface';

-- 创建更新时间自动更新触发器
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_product_review_analysis_updated_at 
    BEFORE UPDATE ON product_review_analysis 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 创建一些有用的视图

-- 1. 产品评论维度统计视图
CREATE VIEW product_review_dimension_stats AS
SELECT 
    product_id,
    aspect_category,
    aspect_subcategory,
    COUNT(*) as review_count,
    COUNT(DISTINCT standardized_aspect) as unique_aspects
FROM product_review_analysis
GROUP BY product_id, aspect_category, aspect_subcategory;

COMMENT ON VIEW product_review_dimension_stats IS '产品评论维度统计：每个产品在各维度下的评论数量和唯一方面数';

-- 2. 维度热度统计视图
CREATE VIEW aspect_popularity_stats AS
SELECT 
    aspect_category,
    aspect_subcategory,
    standardized_aspect,
    COUNT(DISTINCT product_id) as product_count,
    COUNT(*) as total_mentions
FROM product_review_analysis
GROUP BY aspect_category, aspect_subcategory, standardized_aspect
ORDER BY product_count DESC, total_mentions DESC;

COMMENT ON VIEW aspect_popularity_stats IS '维度热度统计：各个标准化方面在所有产品中的覆盖度和提及频次';

-- 3. 产品完整性检查视图
CREATE VIEW product_review_completeness AS
SELECT 
    p.platform_id,
    p.title,
    p.product_segment,
    COALESCE(r.total_reviews, 0) as total_reviews,
    COALESCE(r.dimension_count, 0) as dimension_count,
    CASE 
        WHEN r.total_reviews IS NULL THEN '无评论分析'
        WHEN r.total_reviews < 10 THEN '评论较少'
        WHEN r.dimension_count < 3 THEN '维度不全'
        ELSE '数据完整'
    END as completeness_status
FROM product_wide_table p
LEFT JOIN (
    SELECT 
        product_id,
        COUNT(*) as total_reviews,
        COUNT(DISTINCT aspect_category) as dimension_count
    FROM product_review_analysis
    GROUP BY product_id
) r ON p.platform_id = r.product_id;

COMMENT ON VIEW product_review_completeness IS '产品评论完整性检查：显示每个产品的评论分析数据完整程度'; 