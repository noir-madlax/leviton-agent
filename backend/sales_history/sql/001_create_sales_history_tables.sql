-- Migration: Create Product Sales History tables
-- Version: 001
-- Description: Creates daily and monthly product sales history tables with proper constraints

-- =====================================================
-- Daily Product Sales History Table
-- =====================================================

CREATE TABLE IF NOT EXISTS product_sales_history_daily (
    id BIGSERIAL PRIMARY KEY,
    platform_id VARCHAR(20) NOT NULL,                    -- ASIN from product_wide_table
    platform_source VARCHAR(50) NOT NULL DEFAULT 'amazon', -- Platform source (amazon, walmart, etc.)
    api_source VARCHAR(50) NOT NULL DEFAULT 'jungle_scout', -- Data source API (jungle_scout, etc.)
    date DATE NOT NULL,                                  -- Sales date
    estimated_units_sold INTEGER NOT NULL CHECK (estimated_units_sold >= 0),  -- Daily units sold
    last_known_price DECIMAL(10,2) NOT NULL CHECK (last_known_price >= 0),    -- Price on that date
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_platform_date UNIQUE (platform_id, platform_source, date),
    CONSTRAINT fk_product_sales_history_platform_id FOREIGN KEY (platform_id) REFERENCES product_wide_table(platform_id) ON DELETE CASCADE
);

-- =====================================================
-- Monthly Aggregated Product Sales History Table
-- =====================================================

CREATE TABLE IF NOT EXISTS product_sales_history_monthly (
    id BIGSERIAL PRIMARY KEY,
    platform_id VARCHAR(20) NOT NULL,                    -- ASIN from product_wide_table
    platform_source VARCHAR(50) NOT NULL DEFAULT 'amazon', -- Platform source (amazon, walmart, etc.)
    api_source VARCHAR(50) NOT NULL DEFAULT 'jungle_scout', -- Data source API (jungle_scout, etc.)
    year_month DATE NOT NULL,                            -- First day of month (YYYY-MM-01)
    total_units_sold INTEGER NOT NULL CHECK (total_units_sold >= 0),  -- Sum of daily units
    average_price DECIMAL(10,2) NOT NULL CHECK (average_price >= 0),  -- Average of daily prices
    days_in_month INTEGER NOT NULL CHECK (days_in_month >= 1),        -- Number of days with data
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT unique_platform_month UNIQUE (platform_id, platform_source, year_month),
    CONSTRAINT fk_product_sales_history_monthly_platform_id FOREIGN KEY (platform_id) REFERENCES product_wide_table(platform_id) ON DELETE CASCADE
);

-- =====================================================
-- Indexes for Performance
-- =====================================================

-- Daily table indexes
CREATE INDEX IF NOT EXISTS idx_product_sales_history_daily_platform_id ON product_sales_history_daily (platform_id);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_daily_platform_source ON product_sales_history_daily (platform_source);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_daily_date ON product_sales_history_daily (date DESC);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_daily_platform_date ON product_sales_history_daily (platform_id, platform_source, date DESC);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_daily_api_source ON product_sales_history_daily (api_source);

-- Monthly table indexes
CREATE INDEX IF NOT EXISTS idx_product_sales_history_monthly_platform_id ON product_sales_history_monthly (platform_id);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_monthly_platform_source ON product_sales_history_monthly (platform_source);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_monthly_year_month ON product_sales_history_monthly (year_month DESC);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_monthly_platform_month ON product_sales_history_monthly (platform_id, platform_source, year_month DESC);
CREATE INDEX IF NOT EXISTS idx_product_sales_history_monthly_api_source ON product_sales_history_monthly (api_source);

-- =====================================================
-- Triggers for updated_at
-- =====================================================

-- Create update_updated_at_column function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Bind triggers
CREATE TRIGGER update_product_sales_history_daily_updated_at 
    BEFORE UPDATE ON product_sales_history_daily 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_product_sales_history_monthly_updated_at 
    BEFORE UPDATE ON product_sales_history_monthly 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- =====================================================
-- Table Comments
-- =====================================================

COMMENT ON TABLE product_sales_history_daily IS 'Daily product sales history data from various APIs';
COMMENT ON COLUMN product_sales_history_daily.platform_id IS 'Product ASIN from product_wide_table';
COMMENT ON COLUMN product_sales_history_daily.platform_source IS 'Platform source (amazon, walmart, etc.)';
COMMENT ON COLUMN product_sales_history_daily.api_source IS 'Data source API (jungle_scout, etc.)';
COMMENT ON COLUMN product_sales_history_daily.date IS 'Sales date';
COMMENT ON COLUMN product_sales_history_daily.estimated_units_sold IS 'Estimated units sold on this date';
COMMENT ON COLUMN product_sales_history_daily.last_known_price IS 'Last known price on this date (USD)';

COMMENT ON TABLE product_sales_history_monthly IS 'Monthly aggregated product sales history data';
COMMENT ON COLUMN product_sales_history_monthly.platform_id IS 'Product ASIN from product_wide_table';
COMMENT ON COLUMN product_sales_history_monthly.platform_source IS 'Platform source (amazon, walmart, etc.)';
COMMENT ON COLUMN product_sales_history_monthly.api_source IS 'Data source API (jungle_scout, etc.)';
COMMENT ON COLUMN product_sales_history_monthly.year_month IS 'First day of the month (YYYY-MM-01)';
COMMENT ON COLUMN product_sales_history_monthly.total_units_sold IS 'Sum of daily units sold in the month';
COMMENT ON COLUMN product_sales_history_monthly.average_price IS 'Average of daily prices in the month';
COMMENT ON COLUMN product_sales_history_monthly.days_in_month IS 'Number of days with data in the month'; 