-- Review Analysis Core Tables
-- This migration creates the canonical tables used by the review-analysis
-- pipeline.  All names are prefixed with *review_analysis_* per project
-- convention.

-- ---------------------------------------------------------------------
-- 1) review_analysis_aspects – dimension table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.review_analysis_aspects (
    aspect_pk       BIGSERIAL PRIMARY KEY,
    project_id      VARCHAR NOT NULL,
    product_id      TEXT    NOT NULL,
    aspect_type     VARCHAR(8) NOT NULL,                        -- "phy" | "perf" | "use"
    local_id        TEXT    NOT NULL,                           -- Prompt-local identifier (A/a/… or use-case string)
    parent_group_name TEXT   NOT NULL,                          -- PHYSICAL / PERF / USE header
    detail_text     TEXT    NOT NULL,
    category_pk     BIGINT       ,                              -- FK → categories.category_pk (set later)
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, product_id, aspect_type, local_id)
);

-- ---------------------------------------------------------------------
-- 2) review_analysis_aspect_categories – lookup table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.review_analysis_aspect_categories (
    category_pk BIGSERIAL PRIMARY KEY,
    project_id  VARCHAR NOT NULL,
    aspect_type VARCHAR(8) NOT NULL,                            -- "phy" | "perf" | "use" - categories are specific to aspect type
    name        TEXT    NOT NULL,
    stage       VARCHAR(16) NOT NULL DEFAULT 'categorisation',  -- categorisation | consolidation | final
    definition  TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (project_id, aspect_type, name, stage)
);

-- Link FK now that category table exists
ALTER TABLE public.review_analysis_aspects
    ADD CONSTRAINT fk_review_analysis_aspects_category
    FOREIGN KEY (category_pk) REFERENCES public.review_analysis_aspect_categories(category_pk)
    ON UPDATE CASCADE ON DELETE SET NULL;

-- ---------------------------------------------------------------------
-- 3) review_analysis_aspect_occurrences – fact table
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.review_analysis_aspect_occurrences (
    id         BIGSERIAL PRIMARY KEY,
    aspect_pk  BIGINT NOT NULL REFERENCES public.review_analysis_aspects(aspect_pk)
               ON UPDATE CASCADE ON DELETE CASCADE,
    review_id  TEXT   NOT NULL,
    sentiment  VARCHAR(8) NOT NULL,                             -- "+" | "-"
    causes     BIGINT[] DEFAULT '{}',                           -- Array of aspect_pks that are causes
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indices for join / filter performance
CREATE INDEX IF NOT EXISTS idx_review_analysis_aspects_project ON public.review_analysis_aspects(project_id);
CREATE INDEX IF NOT EXISTS idx_review_analysis_aspect_occurrences_aspect ON public.review_analysis_aspect_occurrences(aspect_pk); 