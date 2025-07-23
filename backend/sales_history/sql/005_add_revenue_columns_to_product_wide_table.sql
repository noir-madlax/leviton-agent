-- Migration: Add Revenue Columns to Product Wide Table
-- Version: 004
-- Description: Adds past_month_revenue, past_6_month_revenue, and past_year_revenue columns to product_wide_table
--              and populates them with data from sales history tables

-- =====================================================
-- Add Revenue Columns to Product Wide Table
-- =====================================================

-- Add past_month_revenue column
ALTER TABLE product_wide_table 
ADD COLUMN IF NOT EXISTS past_month_revenue DECIMAL(12,2) DEFAULT 0 CHECK (past_month_revenue >= 0);

-- Add past_6_month_revenue column
ALTER TABLE product_wide_table 
ADD COLUMN IF NOT EXISTS past_6_month_revenue DECIMAL(12,2) DEFAULT 0 CHECK (past_6_month_revenue >= 0);

-- Add past_year_revenue column
ALTER TABLE product_wide_table 
ADD COLUMN IF NOT EXISTS past_year_revenue DECIMAL(12,2) DEFAULT 0 CHECK (past_year_revenue >= 0);

-- =====================================================
-- Create Indexes for Performance
-- =====================================================

-- Create indexes for the new revenue columns
CREATE INDEX IF NOT EXISTS idx_product_wide_table_past_month_revenue ON product_wide_table (past_month_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_product_wide_table_past_6_month_revenue ON product_wide_table (past_6_month_revenue DESC);
CREATE INDEX IF NOT EXISTS idx_product_wide_table_past_year_revenue ON product_wide_table (past_year_revenue DESC);

-- =====================================================
-- Populate Revenue Data from Sales History Tables
-- =====================================================

-- Update past_month_revenue from daily sales history (most recent 30 days)
UPDATE product_wide_table 
SET past_month_revenue = COALESCE(
    (SELECT SUM(revenue)
     FROM product_sales_history_daily 
     WHERE product_sales_history_daily.platform_id = product_wide_table.platform_id
     AND product_sales_history_daily.platform_source = 'amazon'
     AND product_sales_history_daily.date >= (
         SELECT MAX(date) - INTERVAL '29 days'
         FROM product_sales_history_daily
         WHERE platform_id = product_wide_table.platform_id
         AND platform_source = 'amazon'
     )
     AND product_sales_history_daily.date <= (
         SELECT MAX(date)
         FROM product_sales_history_daily
         WHERE platform_id = product_wide_table.platform_id
         AND platform_source = 'amazon'
     )), 0
)
WHERE EXISTS (
    SELECT 1 
    FROM product_sales_history_daily 
    WHERE product_sales_history_daily.platform_id = product_wide_table.platform_id
);

-- Update past_6_month_revenue from monthly sales history (last 6 months)
UPDATE product_wide_table 
SET past_6_month_revenue = COALESCE(
    (SELECT SUM(total_revenue)
     FROM product_sales_history_monthly 
     WHERE product_sales_history_monthly.platform_id = product_wide_table.platform_id
     AND product_sales_history_monthly.platform_source = 'amazon'
     AND product_sales_history_monthly.year_month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '6 months')
     AND product_sales_history_monthly.year_month < DATE_TRUNC('month', CURRENT_DATE)), 0
)
WHERE EXISTS (
    SELECT 1 
    FROM product_sales_history_monthly 
    WHERE product_sales_history_monthly.platform_id = product_wide_table.platform_id
);

-- Update past_year_revenue from yearly sales history
UPDATE product_wide_table 
SET past_year_revenue = COALESCE(
    (SELECT total_revenue 
     FROM product_sales_history_yearly 
     WHERE product_sales_history_yearly.platform_id = product_wide_table.platform_id
     AND product_sales_history_yearly.platform_source = 'amazon'
     AND product_sales_history_yearly.year_start_date = DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')
     LIMIT 1), 0
)
WHERE EXISTS (
    SELECT 1 
    FROM product_sales_history_yearly 
    WHERE product_sales_history_yearly.platform_id = product_wide_table.platform_id
);

-- =====================================================
-- Add Comments for New Columns
-- =====================================================

COMMENT ON COLUMN product_wide_table.past_month_revenue IS 'Total revenue from the most recent 30 days (USD)';
COMMENT ON COLUMN product_wide_table.past_6_month_revenue IS 'Total revenue from the last 6 months (USD)';
COMMENT ON COLUMN product_wide_table.past_year_revenue IS 'Total revenue from the previous year (USD)';

-- =====================================================
-- Create Function to Update Revenue Columns
-- =====================================================

-- Create a function to update revenue columns for a specific product
CREATE OR REPLACE FUNCTION update_product_revenue_columns(product_asin VARCHAR(20))
RETURNS VOID AS $$
BEGIN
    -- Update past_month_revenue (most recent 30 days from daily sales)
    UPDATE product_wide_table 
    SET past_month_revenue = COALESCE(
        (SELECT SUM(revenue)
         FROM product_sales_history_daily 
         WHERE product_sales_history_daily.platform_id = product_wide_table.platform_id
         AND product_sales_history_daily.platform_source = 'amazon'
         AND product_sales_history_daily.date >= (
             SELECT MAX(date) - INTERVAL '29 days'
             FROM product_sales_history_daily
             WHERE platform_id = product_wide_table.platform_id
             AND platform_source = 'amazon'
         )
         AND product_sales_history_daily.date <= (
             SELECT MAX(date)
             FROM product_sales_history_daily
             WHERE platform_id = product_wide_table.platform_id
             AND platform_source = 'amazon'
         )), 0
    )
    WHERE platform_id = product_asin;

    -- Update past_6_month_revenue
    UPDATE product_wide_table 
    SET past_6_month_revenue = COALESCE(
        (SELECT SUM(total_revenue)
         FROM product_sales_history_monthly 
         WHERE product_sales_history_monthly.platform_id = product_wide_table.platform_id
         AND product_sales_history_monthly.platform_source = 'amazon'
         AND product_sales_history_monthly.year_month >= DATE_TRUNC('month', CURRENT_DATE - INTERVAL '6 months')
         AND product_sales_history_monthly.year_month < DATE_TRUNC('month', CURRENT_DATE)), 0
    )
    WHERE platform_id = product_asin;

    -- Update past_year_revenue
    UPDATE product_wide_table 
    SET past_year_revenue = COALESCE(
        (SELECT total_revenue 
         FROM product_sales_history_yearly 
         WHERE product_sales_history_yearly.platform_id = product_wide_table.platform_id
         AND product_sales_history_yearly.platform_source = 'amazon'
         AND product_sales_history_yearly.year_start_date = DATE_TRUNC('year', CURRENT_DATE - INTERVAL '1 year')
         LIMIT 1), 0
    )
    WHERE platform_id = product_asin;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Create Function to Update All Products Revenue
-- =====================================================

-- Create a function to update revenue columns for all products
CREATE OR REPLACE FUNCTION update_all_products_revenue_columns()
RETURNS VOID AS $$
DECLARE
    product_record RECORD;
BEGIN
    FOR product_record IN 
        SELECT DISTINCT platform_id 
        FROM product_wide_table 
        WHERE platform_id IN (
            SELECT DISTINCT platform_id FROM product_sales_history_daily
            UNION
            SELECT DISTINCT platform_id FROM product_sales_history_monthly
            UNION
            SELECT DISTINCT platform_id FROM product_sales_history_yearly
        )
    LOOP
        PERFORM update_product_revenue_columns(product_record.platform_id);
    END LOOP;
END;
$$ LANGUAGE plpgsql;

-- =====================================================
-- Migration Complete
-- =====================================================
-- Note: The revenue columns are now available in product_wide_table
-- Use update_product_revenue_columns(asin) to update a specific product
-- Use update_all_products_revenue_columns() to update all products
-- The columns will be automatically populated with data from sales history tables 