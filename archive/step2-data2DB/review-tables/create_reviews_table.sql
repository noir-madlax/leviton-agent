-- 创建产品评论详情表
-- 迁移名称: create_product_reviews_table
-- 作用: 存储完整的产品评论数据，包括评分、用户信息等

CREATE TABLE product_reviews (
    id BIGSERIAL PRIMARY KEY,
    
    -- 核心标识字段
    review_id INTEGER NOT NULL,                -- 评论ID
    product_id TEXT NOT NULL,                  -- 产品ID，关联product_wide_table.platform_id
    
    -- 评论内容字段
    review_text TEXT,                          -- 完整评论文本
    review_title TEXT,                         -- 评论标题
    rating TEXT,                               -- 评分（如"4.0 out of 5 stars"）
    review_date TEXT,                          -- 评论日期
    
    -- 用户信息字段
    verified BOOLEAN DEFAULT false,            -- 是否验证购买
    user_name TEXT,                           -- 用户名
    number_of_helpful INTEGER DEFAULT 0,      -- 有用投票数
    
    -- 分析关联字段
    aspect_key TEXT,                          -- 关联的评论方面标识符（如"A@button layout changed"）
    
    -- 元数据字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- 约束
    FOREIGN KEY (product_id) REFERENCES product_wide_table(platform_id) ON DELETE CASCADE,
    
    -- 唯一约束：同一产品的同一评论ID和方面标识符组合唯一
    UNIQUE(product_id, review_id, aspect_key)
);

-- 创建索引优化查询性能

-- 1. 产品查询优化
CREATE INDEX idx_reviews_product ON product_reviews(product_id);

-- 2. 评论ID查询优化
CREATE INDEX idx_reviews_review_id ON product_reviews(review_id);

-- 3. 评分统计优化
CREATE INDEX idx_reviews_rating ON product_reviews(rating) WHERE rating IS NOT NULL;

-- 4. 验证用户筛选优化
CREATE INDEX idx_reviews_verified ON product_reviews(verified);

-- 5. 有用性排序优化
CREATE INDEX idx_reviews_helpful ON product_reviews(number_of_helpful DESC);

-- 6. 日期范围查询优化
CREATE INDEX idx_reviews_date ON product_reviews(review_date) WHERE review_date IS NOT NULL;

-- 7. 方面关联查询优化
CREATE INDEX idx_reviews_aspect_key ON product_reviews(aspect_key) WHERE aspect_key IS NOT NULL;

-- 8. 复合查询优化
CREATE INDEX idx_reviews_product_rating ON product_reviews(product_id, rating);

-- 9. 全文搜索索引
CREATE INDEX idx_reviews_text_search ON product_reviews USING gin(to_tsvector('english', COALESCE(review_title, '') || ' ' || COALESCE(review_text, '')));

-- 添加表注释
COMMENT ON TABLE product_reviews IS '产品评论详情表：存储完整的产品评论数据，包括评分、用户信息、有用性投票等';
COMMENT ON COLUMN product_reviews.review_id IS '评论ID，来源于原始数据中的review_id';
COMMENT ON COLUMN product_reviews.product_id IS '产品ID，关联product_wide_table.platform_id';
COMMENT ON COLUMN product_reviews.review_text IS '完整的评论文本内容';
COMMENT ON COLUMN product_reviews.review_title IS '评论标题';
COMMENT ON COLUMN product_reviews.rating IS '评分，格式如"4.0 out of 5 stars"';
COMMENT ON COLUMN product_reviews.review_date IS '评论日期，格式如"Reviewed in the United States on March 3, 2024"';
COMMENT ON COLUMN product_reviews.verified IS '是否为验证购买的评论';
COMMENT ON COLUMN product_reviews.user_name IS '评论用户名';
COMMENT ON COLUMN product_reviews.number_of_helpful IS '有用投票数';
COMMENT ON COLUMN product_reviews.aspect_key IS '关联的评论方面标识符，用于连接评论分析数据';

-- 创建更新时间自动更新触发器
CREATE TRIGGER update_product_reviews_updated_at 
    BEFORE UPDATE ON product_reviews 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- 创建有用的视图

-- 1. 产品评分统计视图
CREATE VIEW product_rating_stats AS
SELECT 
    product_id,
    COUNT(*) as total_reviews,
    COUNT(DISTINCT review_id) as unique_reviews,
    COUNT(CASE WHEN verified THEN 1 END) as verified_reviews,
    AVG(
        CASE 
            WHEN rating ~ '^[0-9]+\.?[0-9]*' 
            THEN CAST(substring(rating from '^([0-9]+\.?[0-9]*)') AS NUMERIC)
            ELSE NULL 
        END
    ) as avg_rating,
    SUM(number_of_helpful) as total_helpful_votes
FROM product_reviews
WHERE rating IS NOT NULL
GROUP BY product_id;

COMMENT ON VIEW product_rating_stats IS '产品评分统计：包括评论数量、平均评分、验证购买评论数等';

-- 2. 高质量评论视图（验证购买且有有用投票）
CREATE VIEW high_quality_reviews AS
SELECT 
    r.*,
    p.title as product_title
FROM product_reviews r
JOIN product_wide_table p ON r.product_id = p.platform_id
WHERE r.verified = true 
    AND r.number_of_helpful >= 1
    AND LENGTH(r.review_text) >= 50
ORDER BY r.number_of_helpful DESC, r.review_date DESC;

COMMENT ON VIEW high_quality_reviews IS '高质量评论：验证购买、有有用投票且内容充实的评论';

-- 3. 评论时间趋势统计视图
CREATE VIEW review_time_trends AS
SELECT 
    product_id,
    EXTRACT(YEAR FROM TO_DATE(
        CASE 
            WHEN review_date ~ 'on ([A-Za-z]+ [0-9]+, [0-9]+)'
            THEN substring(review_date from 'on ([A-Za-z]+ [0-9]+, [0-9]+)')
            ELSE NULL
        END, 
        'Month DD, YYYY'
    )) as review_year,
    EXTRACT(MONTH FROM TO_DATE(
        CASE 
            WHEN review_date ~ 'on ([A-Za-z]+ [0-9]+, [0-9]+)'
            THEN substring(review_date from 'on ([A-Za-z]+ [0-9]+, [0-9]+)')
            ELSE NULL
        END, 
        'Month DD, YYYY'
    )) as review_month,
    COUNT(*) as review_count,
    AVG(
        CASE 
            WHEN rating ~ '^[0-9]+\.?[0-9]*' 
            THEN CAST(substring(rating from '^([0-9]+\.?[0-9]*)') AS NUMERIC)
            ELSE NULL 
        END
    ) as avg_rating
FROM product_reviews
WHERE review_date IS NOT NULL 
    AND review_date ~ 'on ([A-Za-z]+ [0-9]+, [0-9]+)'
GROUP BY product_id, review_year, review_month
ORDER BY product_id, review_year DESC, review_month DESC;

COMMENT ON VIEW review_time_trends IS '评论时间趋势：按年月统计产品评论数量和平均评分的变化趋势'; 