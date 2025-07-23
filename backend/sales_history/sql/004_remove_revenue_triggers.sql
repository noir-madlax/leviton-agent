-- Migration: Remove Revenue Triggers and Convert to Regular Columns
-- Version: 004
-- Description: Removes revenue triggers and converts generated columns to regular columns

-- =====================================================
-- Drop Revenue-Related Triggers
-- =====================================================

-- Drop the cross-table revenue synchronization triggers
DROP TRIGGER IF EXISTS update_monthly_revenue_trigger ON product_sales_history_daily;
DROP TRIGGER IF EXISTS update_yearly_revenue_trigger ON product_sales_history_monthly;

-- Drop the revenue update functions
DROP FUNCTION IF EXISTS update_monthly_revenue_from_daily();
DROP FUNCTION IF EXISTS update_yearly_revenue_from_monthly();

-- =====================================================
-- Convert Generated Revenue Columns to Regular Columns
-- =====================================================

-- For daily table: Convert revenue from generated to regular column
ALTER TABLE product_sales_history_daily 
DROP COLUMN IF EXISTS revenue;

ALTER TABLE product_sales_history_daily 
ADD COLUMN revenue DECIMAL(12,2) DEFAULT 0 CHECK (revenue >= 0);

-- For monthly table: Convert total_revenue from generated to regular column
ALTER TABLE product_sales_history_monthly 
DROP COLUMN IF EXISTS total_revenue;

ALTER TABLE product_sales_history_monthly 
ADD COLUMN total_revenue DECIMAL(12,2) DEFAULT 0 CHECK (total_revenue >= 0);

-- For yearly table: Convert total_revenue from generated to regular column
ALTER TABLE product_sales_history_yearly 
DROP COLUMN IF EXISTS total_revenue;

ALTER TABLE product_sales_history_yearly 
ADD COLUMN total_revenue DECIMAL(12,2) DEFAULT 0 CHECK (total_revenue >= 0);

-- =====================================================
-- Update Comments for Revenue Columns
-- =====================================================

COMMENT ON COLUMN product_sales_history_daily.revenue IS 'Revenue (price * units) in USD - calculated by application code';
COMMENT ON COLUMN product_sales_history_monthly.total_revenue IS 'Total revenue in USD - sum of daily revenues for the month';
COMMENT ON COLUMN product_sales_history_yearly.total_revenue IS 'Total revenue in USD - sum of monthly revenues for the year';

-- =====================================================
-- Migration Complete
-- ===================================================== 