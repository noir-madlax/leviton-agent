-- Drop the existing materialized view and its indexes
-- Run this before recreating the view with the updated schema

-- Drop indexes first (if they exist)
DROP INDEX IF EXISTS idx_review_aspect_data_category;
DROP INDEX IF EXISTS idx_review_aspect_data_product;
DROP INDEX IF EXISTS idx_review_aspect_data_sentiment;
DROP INDEX IF EXISTS idx_review_aspect_data_project;

-- Drop the materialized view
DROP MATERIALIZED VIEW IF EXISTS review_aspect_data_view;

-- Verify the view has been dropped
SELECT 'review_aspect_data_view dropped successfully' as status; 