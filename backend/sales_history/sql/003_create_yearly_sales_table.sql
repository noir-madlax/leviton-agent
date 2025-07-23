-- Migration: Create Yearly Product Sales History Table
-- Version: 003
-- Description: Creates yearly aggregated product sales history table with proper constraints

-- =====================================================
-- Yearly Aggregated Product Sales History Table
-- =====================================================

CREATE TABLE IF NOT EXISTS product_sales_history_yearly (
    id BIGSERIAL PRIMARY KEY,
    platform_id VARCHAR(20) NOT NULL,                    -- ASIN from product_wide_table
    platform_source VARCHAR(50) NOT NULL DEFAULT 'amazon', -- Platform source (amazon, walmart, etc.)
    api_source VARCHAR(50) NOT NULL DEFAULT 'jungle_scout', -- Data source API (jungle_scout, etc.)
    year_start_date DATE NOT NULL,                        -- First day of the year period (YYYY-MM-DD)
    year_end_date DATE NOT NULL,                          -- Last day of the year period (YYYY-MM-DD)
    total_units_sold INTEGER NOT NULL CHECK (total_units_sold >= 0),  -- Sum of monthly units
    average_price DECIMAL(10,2) NOT NULL CHECK (average_price >= 0),  -- Average of monthly prices
    total_revenue DECIMAL(12,2) NOT NULL DEFAULT 0 CHECK (total_revenue >= 0),  -- Total revenue (sum of monthly revenues)
    months_in_year INTEGER NOT NULL CHECK (months_in_year >= 1),      -- Number of months with data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_platform_year UNIQUE (platform_id, platform_source, year_start_date),
    CONSTRAINT fk_product_sales_history_yearly_platform_id FOREIGN KEY (platform_id) REFERENCES product_wide_table(platform_id) ON DELETE CASCADE,
    CONSTRAINT valid_year_dates CHECK (year_end_date >= year_start_date)
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Yearly table indexes
CREATE INDEX IF NOT EXISTS idx_product_sales_history_yearly_platform_id ON product_sales_history_yearly (platform_id);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_yearly_platform_source ON product_sales_history_yearly (platform_source);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_yearly_year_start ON product_sales_history_yearly (year_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_yearly_year_end ON product_sales_history_yearly (year_end_date DESC);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_yearly_platform_year ON product_sales_history_yearly (platform_id, platform_source, year_start_date DESC);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_yearly_api_source ON product_sales_history_yearly (api_source);

-- =====================================================
-- Triggers for updated_at
-- =====================================================

-- Create trigger for yearly table
CREATE TRIGGER update_product_sales_history_yearly_updated_at 
    BEFORE UPDATE ON product_sales_history_yearly 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Revenue Handling
-- =====================================================
-- Note: Revenue calculations are handled by application code
-- Yearly total_revenue = sum of monthly revenues for the year

-- =====================================================
-- Table Comments
-- =====================================================

COMMENT ON TABLE product_sales_history_yearly IS 'Yearly aggregated product sales history data (rolling year from latest scraping date)';
COMMENT ON COLUMN product_sales_history_yearly.platform_id IS 'Product ASIN from product_wide_table';
COMMENT ON COLUMN product_sales_history_yearly.platform_source IS 'Platform source (amazon, walmart, etc.)';
COMMENT ON COLUMN product_sales_history_yearly.api_source IS 'Data source API (jungle_scout, etc.)';
COMMENT ON COLUMN product_sales_history_yearly.year_start_date IS 'First day of the year period (YYYY-MM-DD)';
COMMENT ON COLUMN product_sales_history_yearly.year_end_date IS 'Last day of the year period (YYYY-MM-DD) - latest scraping date';
COMMENT ON COLUMN product_sales_history_yearly.total_units_sold IS 'Sum of monthly units sold in the year';
COMMENT ON COLUMN product_sales_history_yearly.average_price IS 'Average of monthly prices in the year';
COMMENT ON COLUMN product_sales_history_yearly.total_revenue IS 'Total revenue in the year (USD)';
COMMENT ON COLUMN product_sales_history_yearly.months_in_year IS 'Number of months with data in the year';

-- =====================================================
-- Migration Complete
-- ===================================================== 