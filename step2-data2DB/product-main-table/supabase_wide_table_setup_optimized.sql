-- =====================================================
-- Supabase 产品数据宽表创建和数据导入脚本 (优化版本)
-- =====================================================

-- 预期数据统计（用于验证）
-- CSV总行数: 514行
-- Dimmer Switches: 约250行
-- Light Switches: 约264行

-- =====================================================
-- 第1步：环境准备和数据验证
-- =====================================================

-- 清理可能存在的旧数据
DROP TABLE IF EXISTS product_wide_table CASCADE;
DROP TABLE IF EXISTS temp_dimmer_taxonomy CASCADE;
DROP TABLE IF EXISTS temp_light_taxonomy CASCADE;

-- 创建数据导入统计表
CREATE TABLE import_stats (
    step_name TEXT,
    record_count INTEGER,
    timestamp TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 第2步：创建主表结构
-- =====================================================

CREATE TABLE product_wide_table (
    id SERIAL PRIMARY KEY,
    -- CSV原始字段
    source TEXT,
    platform_id TEXT,
    title TEXT,
    brand TEXT,
    model_number TEXT,
    price_usd DECIMAL(10,2),
    list_price_usd DECIMAL(10,2),
    rating DECIMAL(3,2),
    reviews_count DECIMAL(10,1),
    position INTEGER NOT NULL, -- 确保position不为空，用于映射
    category TEXT NOT NULL,    -- 确保category不为空，用于映射
    image_url TEXT,
    product_url TEXT,
    availability TEXT,
    recent_sales TEXT,
    is_bestseller TEXT,
    unit_price TEXT,
    collection TEXT,
    delivery_free TEXT,
    pickup_available TEXT,
    features TEXT,
    description TEXT,
    extract_date TEXT,
    cleaned_title TEXT,
    product_segment TEXT,
    
    -- 新增扩展字段
    refined_category TEXT,
    category_definition TEXT,
    
    -- 审计字段
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- 第3步：创建优化的索引
-- =====================================================

-- 创建复合索引用于精确映射
CREATE INDEX idx_category_position ON product_wide_table(category, position);
CREATE INDEX idx_refined_category ON product_wide_table(refined_category);
CREATE INDEX idx_brand ON product_wide_table(brand);
CREATE INDEX idx_source ON product_wide_table(source);
CREATE INDEX idx_price_range ON product_wide_table(price_usd) WHERE price_usd IS NOT NULL;

-- =====================================================
-- 第4步：创建更新触发器
-- =====================================================

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_updated_at 
    BEFORE UPDATE ON product_wide_table 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- 第5步：创建分类映射临时表
-- =====================================================

-- Dimmer Switches 分类映射表
CREATE TABLE temp_dimmer_taxonomy (
    category_name TEXT PRIMARY KEY,
    definition TEXT NOT NULL,
    product_ids INTEGER[] NOT NULL
);

-- Light Switches 分类映射表  
CREATE TABLE temp_light_taxonomy (
    category_name TEXT PRIMARY KEY,
    definition TEXT NOT NULL,
    product_ids INTEGER[] NOT NULL
);

-- =====================================================
-- 第6步：插入JSON分类映射数据
-- =====================================================

-- Dimmer Switches 精细分类数据
INSERT INTO temp_dimmer_taxonomy (category_name, definition, product_ids) VALUES
('Smart Wi-Fi Enabled Dimmer Switches', 
 'Dimmer switches with built-in Wi-Fi connectivity for direct wireless control and smart home integration without requiring separate hubs, e.g. wireless dimmers with app control, voice assistant compatible dimmers, WiFi-enabled smart home dimmers',
 ARRAY[0,4,9,11,13,19,32,35,43,75,80,93,149,163,164,197,200,204,215,216,217,221,223,224,226,254,259,261,279,281,406,472,491]),

('Smart Hub-Dependent Dimmer Switches',
 'Dimmer switches requiring a separate hub or bridge for smart functionality and wireless communication, e.g. hub-dependent smart dimmers, proprietary wireless protocol dimmers',
 ARRAY[17,33,46,74,79,82,84,85,90,114,116,199,206,266,269,276,299,323,376,382,389,397,399,414,431,432,437,445,454,466,479,481,490,495]),

('Toggle Style Dimmer Switches',
 'Dimmer switches featuring traditional toggle or flip-style controls for on/off and brightness adjustment, e.g. toggle dimmers, flip-style dimmers, toggle switches with integrated dimming',
 ARRAY[7,16,264,267,284,350,400,408,452,493]),

('Touch Activated Dimmer Switches',
 'Dimmer switches operated by touch interface without physical sliding or rotating controls, e.g. touch-sensitive dimmers, capacitive touch light controls, tap-activated dimmers',
 ARRAY[81,193,203,263,306,362,375,426,460]),

('Slide Control Dimmer Switches',
 'Dimmer switches with linear sliding controls for smooth brightness adjustment and precise light level control',
 ARRAY[1,2,3,5,18,25,29,30,31,38,39,47,48,67,73,77,78,83,88,91,92,96,97,148,192,207,208,209,214,219,222,225,257,265,270,274,275,278,283,286,298,302,303,308,310,318,320,324,329,330,331,333,335,339,340,341,342,343,345,346,349,351,352,353,354,355,358,359,361,365,366,367,371,372,374,377,378,380,381,384,385,387,388,390,391,393,395,396,398,401,402,403,405,407,409,410,412,413,415,417,418,419,421,422,423,425,428,429,430,433,434,435,436,438,440,441,442,443,446,447,448,449,451,453,455,456,457,458,459,461,462,463,464,465,467,468,469,470,471,473,474,475,476,477,478,480,482,484,485,486,487,488,489,492,494,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511,512,513]),

('LED Optimized Dimmer Switches',
 'Dimmer switches specifically designed and optimized for use with LED lighting technology for flicker-free operation',
 ARRAY[10,12,21,23,24,72,76,86,89,95,112,117,194,195,196,201,202,205,211,212,213,260,262,268,271,272,273,277,280,282,285,287,288,289,290,291,292,293,294,296,297,300,301,304,305,309,311,313,314,316,317,319,321,322,325,326,327,332,336,337,338,344,347,348,356,357,360,363,364,368,373,379,383,386,392,394,404,411,416,420,424,427,439,444,450]);

-- Light Switches 精细分类数据
INSERT INTO temp_light_taxonomy (category_name, definition, product_ids) VALUES
('Single Pole Toggle Switches',
 'Single pole traditional toggle style switches with flip-style actuators for basic on/off lighting control, e.g. standard toggle switches, grounding toggle switches, heavy duty toggle switches, illuminated toggle switches, toggle framed switches, commercial grade toggle switches',
 ARRAY[52,68,98,107,108,122,129,136,138,139,142,144,186,187,229,232,248,307]),

('Single Pole Rocker Switches', 
 'Single pole decorator/rocker style switches with paddle operation for basic on/off lighting control, e.g. standard single pole rocker switches, decorator paddle switches, quiet rocker switches, illuminated rocker switches, decorator rocker switches, paddle switches',
 ARRAY[50,55,60,65,99,100,102,103,104,105,106,110,113,118,119,120,125,128,131,168,169,171,175,176,180,183,230,233,237,245,315]),

('Three Way Multi-Location Control Switches',
 'Three-way switches that allow control of lighting from two different locations in both rocker and toggle styles, e.g. three-way rocker switches, three-way decorator switches, toggle three way switches, 3-way toggle switches, 3-way rocker switches',
 ARRAY[51,70,115,121,126,153,170,174,179,184,185,231,241,295,312,369,370]),

('Four Way Multi-Location Control Switches',
 'Four-way switches that work with three-way switches to control lighting from three or more locations in both rocker and toggle styles, e.g. four-way rocker switches, four-way decorator switches, paddle four way switches, 4-way decorator switches, 4-way paddle switches',
 ARRAY[66,124,135,143,162,165,227,239,253,334]),

('Multi-Function Combination Switches',
 'Switches that combine multiple individual switching functions in a single device for controlling multiple circuits, e.g. duplex rocker switches, combination decorator switches, dual rocker switches, triple rocker switches, dual paddle switches, double decorator switches, twin rocker switches, duplex switches, combination double switches',
 ARRAY[49,58,62,64,71,130,137,140,177,178,188,235,243,246,251,328]),

('WiFi Connected Smart Switches',
 'Smart switches with built-in Wi-Fi connectivity that can be controlled remotely via smartphone apps and voice assistants without requiring separate hubs',
 ARRAY[53,54,56,57,59,63,67,69,72,73,74,75,76,77,78,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94,95,96,97,101,109,111,112,114,116,117,123,127,132,133,134,141,145,146,147,148,149,150,151,152,154,155,156,157,158,159,160,161,163,164,166,167,172,173,181,182,189,190,191,192,193,194,195,196,197,198,199,200,201,202,203,204,205,206,207,208,209,210,211,212,213,214,215,216,217,218,219,220,221,222,223,224,225,226,228,234,236,238,240,242,244,247,249,250,252,254,255,256,257,258,259,260,261,262,263,264,265,266,267,268,269,270,271,272,273,274,275,276,277,278,279,280,281,282,283,284,285,286,287,288,289,290,291,292,293,294,296,297,298,299,300,301,302,303,304,305,306,308,309,310,311,313,314,316,317,318,319,320,321,322,323,324,325,326,327,329,330,331,332,333,335,336,337,338,339,340,341,342,343,344,345,346,347,348,349,350,351,352,353,354,355,356,357,358,359,360,361,362,363,364,365,366,367,368,371,372,373,374,375,376,377,378,379,380,381,382,383,384,385,386,387,388,389,390,391,392,393,394,395,396,397,398,399,400,401,402,403,404,405,406,407,408,409,410,411,412,413,414,415,416,417,418,419,420,421,422,423,424,425,426,427,428,429,430,431,432,433,434,435,436,437,438,439,440,441,442,443,444,445,446,447,448,449,450,451,452,453,454,455,456,457,458,459,460,461,462,463,464,465,466,467,468,469,470,471,472,473,474,475,476,477,478,479,480,481,482,483,484,485,486,487,488,489,490,491,492,493,494,495,496,497,498,499,500,501,502,503,504,505,506,507,508,509,510,511,512,513]);

-- 记录分类映射统计
INSERT INTO import_stats (step_name, record_count) 
SELECT 'dimmer_categories_loaded', COUNT(*) FROM temp_dimmer_taxonomy;

INSERT INTO import_stats (step_name, record_count) 
SELECT 'light_categories_loaded', COUNT(*) FROM temp_light_taxonomy;

-- =====================================================
-- 第7步：数据导入准备
-- =====================================================

-- 创建数据验证视图
CREATE OR REPLACE VIEW import_validation AS
SELECT 
    'CSV导入前检查' as check_type,
    NULL::INTEGER as expected_count,
    NULL::INTEGER as actual_count,
    '待导入CSV数据' as description;

-- =====================================================
-- 第8步：CSV数据导入占位符
-- =====================================================

/*
!! 重要提示 !!
在这里需要导入CSV数据到 product_wide_table 表中

可以使用以下方法之一：
1. Supabase Dashboard的CSV导入功能
2. 程序化导入（推荐）

导入后记录统计：
*/

-- 导入后执行统计（需要在CSV导入后运行）
-- INSERT INTO import_stats (step_name, record_count) 
-- SELECT 'csv_data_imported', COUNT(*) FROM product_wide_table;

-- =====================================================
-- 第9步：映射逻辑验证和数据更新
-- =====================================================

-- 映射逻辑验证函数
CREATE OR REPLACE FUNCTION validate_mapping_logic() 
RETURNS TABLE (
    category_type TEXT,
    total_products INTEGER,
    mapped_products INTEGER,
    unmapped_products INTEGER,
    mapping_rate NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    WITH mapping_stats AS (
        -- Dimmer Switches 映射统计
        SELECT 
            'Dimmer Switches' as cat_type,
            COUNT(*) as total,
            COUNT(CASE WHEN (p.position - 1) = ANY(
                SELECT unnest(dt.product_ids) FROM temp_dimmer_taxonomy dt
            ) THEN 1 END) as mapped
        FROM product_wide_table p 
        WHERE p.category = 'Dimmer Switches'
        
        UNION ALL
        
        -- Light Switches 映射统计
        SELECT 
            'Light Switches' as cat_type,
            COUNT(*) as total,
            COUNT(CASE WHEN (p.position - 1) = ANY(
                SELECT unnest(lt.product_ids) FROM temp_light_taxonomy lt
            ) THEN 1 END) as mapped
        FROM product_wide_table p 
        WHERE p.category = 'Light Switches'
    )
    SELECT 
        ms.cat_type,
        ms.total,
        ms.mapped,
        ms.total - ms.mapped,
        ROUND((ms.mapped::NUMERIC / ms.total * 100), 2)
    FROM mapping_stats ms;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 第10步：执行扩展字段更新
-- =====================================================

-- 更新 Dimmer Switches 的扩展字段
UPDATE product_wide_table 
SET 
    refined_category = dt.category_name,
    category_definition = dt.definition
FROM temp_dimmer_taxonomy dt
WHERE 
    product_wide_table.category = 'Dimmer Switches' 
    AND (product_wide_table.position - 1) = ANY(dt.product_ids);

-- 更新 Light Switches 的扩展字段
UPDATE product_wide_table 
SET 
    refined_category = lt.category_name,
    category_definition = lt.definition
FROM temp_light_taxonomy lt
WHERE 
    product_wide_table.category = 'Light Switches' 
    AND (product_wide_table.position - 1) = ANY(lt.product_ids);

-- 记录更新统计
INSERT INTO import_stats (step_name, record_count) 
SELECT 'refined_categories_updated', COUNT(*) 
FROM product_wide_table 
WHERE refined_category IS NOT NULL;

-- =====================================================
-- 第11步：完整性验证查询
-- =====================================================

-- 1. 基础数据完整性检查
CREATE OR REPLACE VIEW data_completeness_check AS
SELECT 
    'Total Records' as metric,
    COUNT(*) as count,
    '100%' as coverage
FROM product_wide_table

UNION ALL

SELECT 
    'Records with Refined Category' as metric,
    COUNT(*) as count,
    ROUND((COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM product_wide_table) * 100), 2) || '%' as coverage
FROM product_wide_table 
WHERE refined_category IS NOT NULL

UNION ALL

SELECT 
    'Records with Category Definition' as metric,
    COUNT(*) as count,
    ROUND((COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM product_wide_table) * 100), 2) || '%' as coverage
FROM product_wide_table 
WHERE category_definition IS NOT NULL

UNION ALL

SELECT 
    'Dimmer Switches Count' as metric,
    COUNT(*) as count,
    ROUND((COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM product_wide_table) * 100), 2) || '%' as coverage
FROM product_wide_table 
WHERE category = 'Dimmer Switches'

UNION ALL

SELECT 
    'Light Switches Count' as metric,
    COUNT(*) as count,
    ROUND((COUNT(*)::NUMERIC / (SELECT COUNT(*) FROM product_wide_table) * 100), 2) || '%' as coverage
FROM product_wide_table 
WHERE category = 'Light Switches';

-- 2. 字段完整性检查
CREATE OR REPLACE VIEW field_completeness_check AS
SELECT 
    column_name,
    non_null_count,
    total_count,
    ROUND((non_null_count::NUMERIC / total_count * 100), 2) as completeness_percentage
FROM (
    SELECT 
        'title' as column_name,
        COUNT(title) as non_null_count,
        COUNT(*) as total_count
    FROM product_wide_table
    
    UNION ALL
    
    SELECT 
        'brand' as column_name,
        COUNT(brand) as non_null_count,
        COUNT(*) as total_count
    FROM product_wide_table
    
    UNION ALL
    
    SELECT 
        'price_usd' as column_name,
        COUNT(price_usd) as non_null_count,
        COUNT(*) as total_count
    FROM product_wide_table
    
    UNION ALL
    
    SELECT 
        'rating' as column_name,
        COUNT(rating) as non_null_count,
        COUNT(*) as total_count
    FROM product_wide_table
    
    UNION ALL
    
    SELECT 
        'refined_category' as column_name,
        COUNT(refined_category) as non_null_count,
        COUNT(*) as total_count
    FROM product_wide_table
) subquery;

-- 3. 精细分类分布统计
CREATE OR REPLACE VIEW category_distribution AS
SELECT 
    category,
    refined_category,
    COUNT(*) as product_count,
    ROUND(AVG(price_usd), 2) as avg_price,
    ROUND(AVG(rating), 2) as avg_rating,
    COUNT(CASE WHEN price_usd IS NOT NULL THEN 1 END) as price_data_count
FROM product_wide_table 
WHERE refined_category IS NOT NULL
GROUP BY category, refined_category
ORDER BY category, product_count DESC;

-- =====================================================
-- 第12步：数据质量报告
-- =====================================================

-- 创建综合数据质量报告
CREATE OR REPLACE FUNCTION generate_data_quality_report() 
RETURNS TABLE (
    report_section TEXT,
    metric TEXT,
    value TEXT,
    status TEXT
) AS $$
BEGIN
    RETURN QUERY
    -- 基础统计
    SELECT 
        'Basic Stats'::TEXT as report_section,
        'Total Records'::TEXT as metric,
        COUNT(*)::TEXT as value,
        CASE WHEN COUNT(*) >= 500 THEN 'PASS' ELSE 'REVIEW' END as status
    FROM product_wide_table
    
    UNION ALL
    
    -- 扩展字段覆盖率
    SELECT 
        'Data Quality'::TEXT,
        'Refined Category Coverage'::TEXT,
        ROUND((COUNT(refined_category)::NUMERIC / COUNT(*) * 100), 2)::TEXT || '%',
        CASE WHEN COUNT(refined_category)::NUMERIC / COUNT(*) >= 0.95 THEN 'PASS' ELSE 'FAIL' END
    FROM product_wide_table
    
    UNION ALL
    
    -- 映射验证
    SELECT 
        'Mapping Validation'::TEXT,
        vm.category_type || ' Mapping Rate',
        vm.mapping_rate::TEXT || '%',
        CASE WHEN vm.mapping_rate >= 95 THEN 'PASS' ELSE 'FAIL' END
    FROM validate_mapping_logic() vm;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 第13步：清理和最终化
-- =====================================================

-- 清理临时表的函数（可选执行）
CREATE OR REPLACE FUNCTION cleanup_temp_tables() 
RETURNS TEXT AS $$
BEGIN
    DROP TABLE IF EXISTS temp_dimmer_taxonomy;
    DROP TABLE IF EXISTS temp_light_taxonomy;
    RETURN 'Temporary tables cleaned up successfully';
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- 执行指令总结
-- =====================================================

/*
执行顺序：

1. 运行此脚本到第8步（CSV导入前）
2. 使用程序化方式导入CSV数据
3. 运行第9-13步（映射更新和验证）
4. 查看数据质量报告：SELECT * FROM generate_data_quality_report();
5. 查看完整性检查：SELECT * FROM data_completeness_check;
6. 查看字段完整性：SELECT * FROM field_completeness_check;
7. 查看分类分布：SELECT * FROM category_distribution;

验证命令：
- SELECT * FROM validate_mapping_logic();
- SELECT * FROM import_stats ORDER BY timestamp;
- SELECT COUNT(*) FROM product_wide_table;
*/

-- =====================================================
-- 脚本结束
-- ===================================================== 