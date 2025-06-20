-- Migration: Create Product Segmentation Tables
-- Version: 001
-- Description: Creates all tables needed for product segmentation functionality

-- Segmentation run tracking
CREATE TABLE IF NOT EXISTS segmentation_runs (
    id              VARCHAR(50)  PRIMARY KEY,
    created_at      TIMESTAMPTZ  DEFAULT NOW(),
    status          VARCHAR(20)  DEFAULT 'running' CHECK (status IN ('running', 'completed', 'failed')),
    category        VARCHAR(255) NOT NULL,
    llm_config      JSONB,
    processing_params JSONB,
    total_products  INT,
    processed_products INT DEFAULT 0,
    result_summary  JSONB
);

-- Explicit product input list
CREATE TABLE IF NOT EXISTS run_products (
    run_id        VARCHAR(50) REFERENCES segmentation_runs(id) ON DELETE CASCADE,
    product_id    BIGINT      REFERENCES amazon_products(id),
    created_at    TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (run_id, product_id)
);

-- Generated taxonomies/categories
CREATE TABLE IF NOT EXISTS product_taxonomies (
    id           BIGSERIAL PRIMARY KEY,
    run_id       VARCHAR(50) REFERENCES segmentation_runs(id),
    category_name   VARCHAR(255) NOT NULL,
    definition      TEXT,
    product_count   INT DEFAULT 0,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Final product assignments
CREATE TABLE IF NOT EXISTS product_segments (
    run_id       VARCHAR(50) REFERENCES segmentation_runs(id),
    product_id   BIGINT      REFERENCES amazon_products(id),
    taxonomy_id  BIGINT      REFERENCES product_taxonomies(id),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (run_id, product_id)
);

-- Refined product assignments (from refinement phase)
CREATE TABLE IF NOT EXISTS refined_product_segments (
    run_id       VARCHAR(50) REFERENCES segmentation_runs(id),
    product_id   BIGINT      REFERENCES amazon_products(id),
    taxonomy_id  BIGINT      REFERENCES product_taxonomies(id),
    created_at   TIMESTAMPTZ DEFAULT NOW(),
    PRIMARY KEY (run_id, product_id)
);

-- LLM interaction file index
CREATE TABLE IF NOT EXISTS llm_interaction_index (
    id               BIGSERIAL PRIMARY KEY,
    run_id           VARCHAR(50) REFERENCES segmentation_runs(id),
    interaction_type VARCHAR(50) NOT NULL CHECK (interaction_type IN ('segmentation', 'consolidate_taxonomy', 'refine_assignments')),
    batch_id         INT,
    attempt          INT DEFAULT 1,
    file_path        TEXT NOT NULL,
    prompt_file      TEXT,
    cache_key        VARCHAR(32),
    created_at       TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_segmentation_runs_status ON segmentation_runs(status);
CREATE INDEX IF NOT EXISTS idx_segmentation_runs_created_at ON segmentation_runs(created_at);
CREATE INDEX IF NOT EXISTS idx_segmentation_runs_category ON segmentation_runs(category);
CREATE INDEX IF NOT EXISTS idx_run_products_product_id ON run_products(product_id);
CREATE INDEX IF NOT EXISTS idx_product_taxonomies_run_id ON product_taxonomies(run_id);
CREATE INDEX IF NOT EXISTS idx_product_segments_product_id ON product_segments(product_id);
CREATE INDEX IF NOT EXISTS idx_product_segments_taxonomy_id ON product_segments(taxonomy_id);
CREATE INDEX IF NOT EXISTS idx_llm_interaction_index_run_id ON llm_interaction_index(run_id);
CREATE INDEX IF NOT EXISTS idx_llm_interaction_index_cache_key ON llm_interaction_index(cache_key);
CREATE INDEX IF NOT EXISTS idx_llm_interaction_index_interaction_type ON llm_interaction_index(interaction_type);

-- Add comments for documentation
COMMENT ON TABLE segmentation_runs IS 'Tracks product segmentation jobs';
COMMENT ON TABLE run_products IS 'Explicit list of products to process in each run';
COMMENT ON TABLE product_taxonomies IS 'Generated product categories/segments';
COMMENT ON TABLE product_segments IS 'Final assignment of products to taxonomies';
COMMENT ON TABLE refined_product_segments IS 'Refined product assignments from refinement phase';
COMMENT ON TABLE llm_interaction_index IS 'Index of LLM interaction files stored on disk/S3'; 