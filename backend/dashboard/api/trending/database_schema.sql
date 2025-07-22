-- 销售趋势数据表结构定义
-- Sales Trend Data Table Schema for Supabase

-- =====================================================
-- 表结构定义
-- =====================================================

-- 主表：销售趋势数据
CREATE TABLE IF NOT EXISTS sales_trend_data (
    -- 主键
    id BIGSERIAL PRIMARY KEY,
    
    -- 核心业务字段
    asin VARCHAR(20) NOT NULL,                      -- 产品ASIN标识
    date DATE NOT NULL,                             -- 销售日期
    estimated_units_sold INTEGER NOT NULL CHECK (estimated_units_sold >= 0),  -- 估计销售量
    last_known_price DECIMAL(10,2) NOT NULL CHECK (last_known_price >= 0),    -- 最后已知价格(USD)
    estimated_revenue DECIMAL(12,2) GENERATED ALWAYS AS (estimated_units_sold * last_known_price) STORED,  -- 计算字段：估计收入
    
    -- 元数据字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- 唯一约束：同一ASIN同一日期只能有一条记录
    CONSTRAINT unique_asin_date UNIQUE (asin, date)
);

-- =====================================================
-- 索引优化
-- =====================================================

-- 主要查询索引
CREATE INDEX IF NOT EXISTS idx_sales_trend_asin_date ON sales_trend_data (asin, date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_trend_date ON sales_trend_data (date DESC);
CREATE INDEX IF NOT EXISTS idx_sales_trend_asin ON sales_trend_data (asin);

-- 统计查询优化索引
CREATE INDEX IF NOT EXISTS idx_sales_trend_revenue ON sales_trend_data (estimated_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_sales_trend_volume ON sales_trend_data (estimated_units_sold DESC);

-- =====================================================
-- 行级安全策略 (RLS) - Supabase安全
-- =====================================================

-- 启用行级安全
ALTER TABLE sales_trend_data ENABLE ROW LEVEL SECURITY;

-- 示例安全策略（根据实际认证需求调整）
-- CREATE POLICY "Users can view sales trend data" ON sales_trend_data
--     FOR SELECT USING (auth.role() = 'authenticated');

-- CREATE POLICY "Service role can manage sales trend data" ON sales_trend_data
--     USING (auth.role() = 'service_role');

-- =====================================================
-- 触发器：自动更新时间戳
-- =====================================================

-- 创建更新时间戳函数
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 绑定触发器
CREATE TRIGGER update_sales_trend_data_updated_at 
    BEFORE UPDATE ON sales_trend_data 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 数据验证和约束
-- =====================================================

-- 添加业务规则约束
ALTER TABLE sales_trend_data 
    ADD CONSTRAINT check_valid_date 
    CHECK (date >= '2020-01-01' AND date <= CURRENT_DATE + INTERVAL '1 year');

ALTER TABLE sales_trend_data 
    ADD CONSTRAINT check_reasonable_price 
    CHECK (last_known_price <= 10000.00);  -- 价格不超过$10,000

ALTER TABLE sales_trend_data 
    ADD CONSTRAINT check_reasonable_volume 
    CHECK (estimated_units_sold <= 1000000);  -- 日销量不超过100万

-- =====================================================
-- 示例数据插入（基于CSV数据）
-- =====================================================

-- 插入示例数据 (来自leviton_B08SJ3Z8XD_sales_20250720_184936.csv)
INSERT INTO sales_trend_data (asin, date, estimated_units_sold, last_known_price) VALUES
    ('B08SJ3Z8XD', '2024-07-19', 53, 3.5),
    ('B08SJ3Z8XD', '2024-07-20', 45, 3.5),
    ('B08SJ3Z8XD', '2024-07-21', 66, 3.5),
    ('B08SJ3Z8XD', '2024-07-22', 37, 3.5),
    ('B08SJ3Z8XD', '2024-07-23', 46, 3.5),
    ('B08SJ3Z8XD', '2024-07-24', 35, 3.5),
    ('B08SJ3Z8XD', '2024-07-25', 34, 3.5),
    ('B08SJ3Z8XD', '2024-07-26', 38, 3.5),
    ('B08SJ3Z8XD', '2024-07-27', 30, 3.5),
    ('B08SJ3Z8XD', '2024-07-28', 41, 3.5)
ON CONFLICT (asin, date) DO NOTHING;  -- 避免重复插入

-- =====================================================
-- 查询示例
-- =====================================================

-- 1. 查询特定ASIN的销售趋势
-- SELECT 
--     date,
--     estimated_units_sold,
--     last_known_price,
--     estimated_revenue
-- FROM sales_trend_data 
-- WHERE asin = 'B08SJ3Z8XD' 
-- ORDER BY date DESC 
-- LIMIT 30;

-- 2. 查询日期范围内的数据
-- SELECT 
--     date,
--     estimated_units_sold,
--     last_known_price,
--     estimated_revenue
-- FROM sales_trend_data 
-- WHERE asin = 'B08SJ3Z8XD' 
--   AND date BETWEEN '2024-07-01' AND '2024-12-31'
-- ORDER BY date ASC;

-- 3. 统计查询示例
-- SELECT 
--     asin,
--     COUNT(*) as total_days,
--     SUM(estimated_units_sold) as total_sales,
--     AVG(estimated_units_sold) as avg_daily_sales,
--     AVG(last_known_price) as avg_price,
--     SUM(estimated_revenue) as total_revenue,
--     MIN(date) as start_date,
--     MAX(date) as end_date
-- FROM sales_trend_data 
-- WHERE asin = 'B08SJ3Z8XD'
-- GROUP BY asin;

-- =====================================================
-- 维护脚本
-- =====================================================

-- 清理过期数据（保留最近2年的数据）
-- DELETE FROM sales_trend_data 
-- WHERE date < CURRENT_DATE - INTERVAL '2 years';

-- 重建索引（定期维护）
-- REINDEX TABLE sales_trend_data;

-- 更新表统计信息
-- ANALYZE sales_trend_data;

-- =====================================================
-- 备份和恢复
-- =====================================================

-- 导出数据到CSV
-- COPY sales_trend_data TO '/path/to/backup.csv' 
-- WITH (FORMAT CSV, HEADER TRUE);

-- 从CSV导入数据
-- COPY sales_trend_data (asin, date, estimated_units_sold, last_known_price) 
-- FROM '/path/to/data.csv' 
-- WITH (FORMAT CSV, HEADER TRUE);

-- =====================================================
-- 表注释
-- =====================================================

COMMENT ON TABLE sales_trend_data IS '销售趋势数据表 - 存储产品销量、价格的时间序列数据';
COMMENT ON COLUMN sales_trend_data.asin IS '亚马逊产品标准识别号';
COMMENT ON COLUMN sales_trend_data.date IS '销售数据日期';
COMMENT ON COLUMN sales_trend_data.estimated_units_sold IS '估计销售量（单位：件）';
COMMENT ON COLUMN sales_trend_data.last_known_price IS '最后已知价格（单位：美元）';
COMMENT ON COLUMN sales_trend_data.estimated_revenue IS '估计收入，自动计算：销量×价格'; 