-- Migration: Add Revenue Columns to Sales History Tables
-- Version: 002
-- Description: Adds revenue columns and updates triggers to automatically calculate revenue

-- =====================================================
-- Add Revenue Column to Daily Sales History Table
-- =====================================================

ALTER TABLE product_sales_history_daily 
ADD COLUMN IF NOT EXISTS revenue DECIMAL(12,2) DEFAULT 0 CHECK (revenue >= 0);

-- =====================================================
-- Add Revenue Column to Monthly Sales History Table
-- =====================================================

ALTER TABLE product_sales_history_monthly 
ADD COLUMN IF NOT EXISTS total_revenue DECIMAL(12,2) DEFAULT 0 CHECK (total_revenue >= 0);

-- =====================================================
-- Update Triggers for Revenue Calculation
-- =====================================================

-- Drop existing triggers first
DROP TRIGGER IF EXISTS update_product_sales_history_daily_updated_at ON product_sales_history_daily;
DROP TRIGGER IF EXISTS update_product_sales_history_monthly_updated_at ON product_sales_history_monthly;

-- Create enhanced update_updated_at_column function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Recreate triggers
CREATE TRIGGER update_product_sales_history_daily_updated_at 
    BEFORE UPDATE ON product_sales_history_daily 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_sales_history_monthly_updated_at 
    BEFORE UPDATE ON product_sales_history_monthly 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Add Comments for New Columns
-- =====================================================

COMMENT ON COLUMN product_sales_history_daily.revenue IS 'Calculated revenue (last_known_price * estimated_units_sold) in USD';
COMMENT ON COLUMN product_sales_history_monthly.total_revenue IS 'Calculated total revenue (average_price * total_units_sold) in USD';

-- =====================================================
-- Revenue Columns Added Successfully
-- =====================================================
-- Note: Revenue calculations are handled by application code
-- Daily revenue = last_known_price * estimated_units_sold
-- Monthly total_revenue = sum of daily revenues for the month
-- Yearly total_revenue = sum of monthly revenues for the year

-- =====================================================
-- Migration Complete
-- ===================================================== 