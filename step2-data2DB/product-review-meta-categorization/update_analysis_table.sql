-- 修改product_review_analysis表结构
-- 迁移名称: add_review_id_to_analysis_table
-- 作用: 添加review_id字段建立与product_reviews表的关联

-- 1. 添加review_id列
ALTER TABLE product_review_analysis 
ADD COLUMN review_id INTEGER;

-- 2. 从review_key中提取review_id并更新
-- review_key格式通常是 "A@description" 或包含数字ID
UPDATE product_review_analysis 
SET review_id = (
    CASE 
        WHEN review_key ~ '^[A-Z]@.*' THEN 
            -- 如果是简单的字母@描述格式，生成基于内容的哈希ID
            ABS(HASHTEXT(product_id || '_' || review_key || '_' || review_content))::INTEGER % 999999 + 1
        WHEN review_key ~ '[0-9]+' THEN 
            -- 如果包含数字，提取第一个数字作为ID
            CAST(substring(review_key from '[0-9]+') AS INTEGER)
        ELSE 
            -- 其他情况，生成基于内容的哈希ID
            ABS(HASHTEXT(product_id || '_' || review_key || '_' || review_content))::INTEGER % 999999 + 1
    END
)
WHERE review_id IS NULL;

-- 3. 设置review_id非空约束
ALTER TABLE product_review_analysis 
ALTER COLUMN review_id SET NOT NULL;

-- 4. 创建索引
CREATE INDEX idx_analysis_review_id ON product_review_analysis(review_id);
CREATE INDEX idx_analysis_product_review ON product_review_analysis(product_id, review_id);

-- 5. 添加字段注释
COMMENT ON COLUMN product_review_analysis.review_id IS '评论ID，用于关联product_reviews表';

-- 6. 创建外键约束（在product_reviews表创建后执行）
-- 注意：这个约束需要在导入product_reviews数据后才能生效
-- ALTER TABLE product_review_analysis 
-- ADD CONSTRAINT fk_analysis_review 
-- FOREIGN KEY (product_id, review_id) 
-- REFERENCES product_reviews(product_id, review_id)
-- DEFERRABLE INITIALLY DEFERRED; 