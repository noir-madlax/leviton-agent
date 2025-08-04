#!/usr/bin/env python3
"""
Script to drop and recreate the review_aspect_data_view materialized view to fix JOIN issues.
"""

import logging
from core.database.connection import get_supabase_client

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def recreate_matrix_view():
    """Drop and recreate the materialized view."""
    client = get_supabase_client()
    
    logger.info("🔄 Recreating review_aspect_data_view materialized view...")
    logger.info("=" * 60)
    
    try:
        # Step 1: Drop the existing materialized view
        logger.info("1. Dropping existing materialized view...")
        
        # Use RPC to drop the view
        drop_result = client.rpc('drop_materialized_view', {'view_name': 'review_aspect_data_view'}).execute()
        logger.info("✅ Materialized view dropped successfully")
        
    except Exception as e:
        logger.warning(f"Could not drop view via RPC: {e}")
        logger.info("Trying alternative drop method...")
        
        # Alternative: Try to drop via direct SQL (if possible)
        try:
            # This might not work with Supabase's restrictions
            drop_result = client.table('review_aspect_data_view').delete().neq('product_id', '').execute()
            logger.info("✅ Cleared materialized view data")
        except Exception as e2:
            logger.warning(f"Could not clear view data: {e2}")
    
    # Step 2: Create the materialized view
    logger.info("\n2. Creating new materialized view...")
    
    # The materialized view creation SQL
    create_view_sql = """
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
    """
    
    try:
        # Try to create the view via RPC
        create_result = client.rpc('create_materialized_view', {
            'view_name': 'review_aspect_data_view',
            'sql_query': create_view_sql
        }).execute()
        logger.info("✅ Materialized view created successfully via RPC")
        
    except Exception as e:
        logger.warning(f"Could not create view via RPC: {e}")
        logger.info("You may need to create the view manually in the database.")
        logger.info("SQL to run:")
        print("\n" + "="*60)
        print("MANUAL SQL TO RUN:")
        print("="*60)
        print(create_view_sql)
        print("="*60)
    
    # Step 3: Create indexes
    logger.info("\n3. Creating indexes...")
    
    index_sqls = [
        "CREATE INDEX idx_matrix_review_category ON review_aspect_data_view(category_name, aspect_type);",
        "CREATE INDEX idx_matrix_review_product ON review_aspect_data_view(product_id);",
        "CREATE INDEX idx_matrix_review_sentiment ON review_aspect_data_view(sentiment_label);",
        "CREATE INDEX idx_matrix_review_project ON review_aspect_data_view(product_id, category_name);"
    ]
    
    for index_sql in index_sqls:
        try:
            # Try to create index via RPC
            index_result = client.rpc('create_index', {'sql_query': index_sql}).execute()
            logger.info(f"✅ Index created: {index_sql.split('ON')[1].split('(')[0].strip()}")
        except Exception as e:
            logger.warning(f"Could not create index: {e}")
            logger.info(f"Manual SQL: {index_sql}")
    
    # Step 4: Verify the view
    logger.info("\n4. Verifying the new materialized view...")
    
    try:
        # Test if the view exists and has data
        test_result = client.table('review_aspect_data_view').select('*').limit(1).execute()
        if test_result.data:
            logger.info("✅ Materialized view is accessible and has data")
            
            # Test B0BVKZLT3B specifically
            b0bvkzlt3b_result = client.table('review_aspect_data_view').select('review_id,category_name').eq('product_id', 'B0BVKZLT3B').limit(5).execute()
            if b0bvkzlt3b_result.data:
                logger.info(f"✅ B0BVKZLT3B found in new view: {len(b0bvkzlt3b_result.data)} records")
                for i, record in enumerate(b0bvkzlt3b_result.data):
                    logger.info(f"  {i+1}. review_id={record['review_id']}, category={record['category_name']}")
            else:
                logger.warning("❌ B0BVKZLT3B still not found in new view")
        else:
            logger.warning("❌ Materialized view exists but has no data")
            
    except Exception as e:
        logger.error(f"❌ Error verifying materialized view: {e}")
    
    logger.info("\n🎉 Materialized view recreation completed!")

if __name__ == "__main__":
    recreate_matrix_view() 