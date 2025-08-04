-- SQL Script to Drop Duplicate Rows from product_wide_table
-- Keeps the row with the most non-null fields for each platform_id

-- =====================================================
-- Step 1: Create a temporary table to identify duplicates
-- =====================================================

WITH duplicate_analysis AS (
    SELECT 
        id,
        platform_id,
        -- Count non-null fields for each row
        (
            CASE WHEN source IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN brand IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN model_number IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN price_usd IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN list_price_usd IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN rating IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN reviews_count IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN product_url IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN availability IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN recent_sales IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN is_bestseller IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN unit_price IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN collection IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN delivery_free IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN pickup_available IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN features IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN extract_date IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN product_segment IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN refined_category IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN category_definition IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN past_month_revenue IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN past_6_month_revenue IS NOT NULL THEN 1 ELSE 0 END +
            CASE WHEN past_year_revenue IS NOT NULL THEN 1 ELSE 0 END
        ) AS non_null_count,
        -- Row number within each platform_id group, ordered by non-null count (desc) and id (asc)
        ROW_NUMBER() OVER (
            PARTITION BY platform_id 
            ORDER BY 
                -- First priority: most non-null fields
                (
                    CASE WHEN source IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN brand IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN model_number IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN price_usd IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN list_price_usd IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN rating IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN reviews_count IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN product_url IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN availability IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN recent_sales IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN is_bestseller IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN unit_price IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN collection IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN delivery_free IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN pickup_available IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN features IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN extract_date IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN product_segment IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN refined_category IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN category_definition IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN past_month_revenue IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN past_6_month_revenue IS NOT NULL THEN 1 ELSE 0 END +
                    CASE WHEN past_year_revenue IS NOT NULL THEN 1 ELSE 0 END
                ) DESC,
                -- Second priority: earliest id (oldest record)
                id ASC
        ) AS row_rank
    FROM product_wide_table
    WHERE platform_id IS NOT NULL
)

-- =====================================================
-- Step 2: Show summary of duplicates found
-- =====================================================

SELECT 
    'DUPLICATE_ANALYSIS' as analysis_type,
    COUNT(*) as total_rows,
    COUNT(CASE WHEN row_rank > 1 THEN 1 END) as duplicate_rows_to_delete,
    COUNT(DISTINCT platform_id) as unique_platform_ids,
    COUNT(CASE WHEN row_rank = 1 THEN 1 END) as rows_to_keep
FROM duplicate_analysis;

-- =====================================================
-- Step 3: Delete duplicate rows (keep only row_rank = 1)
-- =====================================================

DELETE FROM product_wide_table 
WHERE id IN (
    SELECT id 
    FROM (
        SELECT 
            id,
            ROW_NUMBER() OVER (
                PARTITION BY platform_id 
                ORDER BY 
                    -- First priority: most non-null fields
                    (
                        CASE WHEN source IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN title IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN brand IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN model_number IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN price_usd IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN list_price_usd IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN rating IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN reviews_count IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN image_url IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN product_url IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN availability IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN recent_sales IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN is_bestseller IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN unit_price IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN collection IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN delivery_free IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN pickup_available IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN features IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN description IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN extract_date IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN cleaned_title IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN product_segment IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN refined_category IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN category_definition IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN past_month_revenue IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN past_6_month_revenue IS NOT NULL THEN 1 ELSE 0 END +
                        CASE WHEN past_year_revenue IS NOT NULL THEN 1 ELSE 0 END
                    ) DESC,
                    -- Second priority: earliest id (oldest record)
                    id ASC
            ) AS row_rank
        FROM product_wide_table
        WHERE platform_id IS NOT NULL
    ) ranked_rows
    WHERE row_rank > 1
);

-- =====================================================
-- Step 4: Verify results
-- =====================================================

SELECT 
    'VERIFICATION' as verification_type,
    COUNT(*) as total_rows_after_cleanup,
    COUNT(DISTINCT platform_id) as unique_platform_ids_after_cleanup,
    COUNT(*) - COUNT(DISTINCT platform_id) as remaining_duplicates
FROM product_wide_table 
WHERE platform_id IS NOT NULL; 