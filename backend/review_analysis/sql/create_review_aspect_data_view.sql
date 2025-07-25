-- Materialized view for matrix review data with proper type casting
CREATE MATERIALIZED VIEW review_aspect_data_view AS
SELECT 
    -- Category information
    rac.category_pk,
    rac.name as category_name,
    rac.definition as category_definition,
    rac.aspect_type,
    
    -- Aspect information
    raa.aspect_pk,
    raa.product_id,
    raa.project_id,  -- Add missing project_id field
    raa.detail_text,
    raa.parent_group_name,
    
    -- Occurrence and sentiment data
    rao.sentiment,
    rao.review_id,
    
    -- Review content
    pr.review_title,
    pr.review_text,
    pr.rating,
    pr.verified,
    pr.review_date,
    
    -- Product information
    pwt.brand,
    pwt.title,  -- Add product title
    pwt.product_url,  -- Add product URL
    pwt.list_price_usd,  -- Add missing price fields
    pwt.price_usd,
    
    -- Computed fields
    CASE 
        WHEN rao.sentiment = '+' THEN 'positive'
        WHEN rao.sentiment = '-' THEN 'negative'
        ELSE 'neutral'
    END as sentiment_label,
    
    -- Review content for display
    COALESCE(pr.review_title, '') || ' - ' || COALESCE(pr.review_text, '') as full_review_content,
    
    -- Aspect description for matrix
    CASE 
        WHEN rac.aspect_type = 'use' THEN raa.aspect_pk::text || '#' || raa.detail_text
        ELSE raa.aspect_pk::text || '#' || COALESCE(raa.parent_group_name, '') || ': ' || raa.detail_text
    END as aspect_description

FROM review_analysis_aspect_categories rac
JOIN review_analysis_aspects raa ON rac.category_pk = raa.category_pk
JOIN review_analysis_aspect_occurrences rao ON raa.aspect_pk = rao.aspect_pk
JOIN product_reviews pr ON rao.review_id::text = pr.review_id::text AND raa.product_id = pr.product_id
JOIN product_wide_table pwt ON raa.product_id = pwt.platform_id
WHERE rac.stage = 'final' 
  AND rac.name != 'OUT_OF_SCOPE'
  AND pr.review_text IS NOT NULL;

-- Indexes for performance (fixed to use correct view name)
CREATE INDEX idx_review_aspect_data_category ON review_aspect_data_view(category_name, aspect_type);
CREATE INDEX idx_review_aspect_data_product ON review_aspect_data_view(product_id);
CREATE INDEX idx_review_aspect_data_sentiment ON review_aspect_data_view(sentiment_label);
CREATE INDEX idx_review_aspect_data_project ON review_aspect_data_view(project_id, category_name);