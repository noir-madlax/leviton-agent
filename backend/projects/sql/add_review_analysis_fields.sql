-- Migration: Add Review Analysis fields to projects table
-- Created: 2025-01-28
-- Purpose: Support review analysis integration in project workflow

-- Add review analysis tracking fields to projects table
ALTER TABLE projects 
ADD COLUMN IF NOT EXISTS review_analysis_id TEXT,
ADD COLUMN IF NOT EXISTS review_analysis_started_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS review_analysis_completed_at TIMESTAMPTZ,
ADD COLUMN IF NOT EXISTS review_analysis_duration_seconds INTEGER,
ADD COLUMN IF NOT EXISTS review_analysis_status TEXT DEFAULT 'pending';

-- Create index for faster status queries
CREATE INDEX IF NOT EXISTS idx_projects_review_analysis_status 
ON projects(review_analysis_status);

-- Create index for project progress queries
CREATE INDEX IF NOT EXISTS idx_projects_review_analysis_timestamps 
ON projects(review_analysis_started_at, review_analysis_completed_at);

-- Add comments for documentation
COMMENT ON COLUMN projects.review_analysis_id IS 'ID of the review analysis run associated with this project';
COMMENT ON COLUMN projects.review_analysis_started_at IS 'Timestamp when review analysis started';
COMMENT ON COLUMN projects.review_analysis_completed_at IS 'Timestamp when review analysis completed';
COMMENT ON COLUMN projects.review_analysis_duration_seconds IS 'Duration of review analysis processing in seconds';
COMMENT ON COLUMN projects.review_analysis_status IS 'Status of review analysis: pending, processing, completed, failed';

-- Verify the changes
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'projects' 
  AND column_name LIKE '%review_analysis%'
ORDER BY column_name; 