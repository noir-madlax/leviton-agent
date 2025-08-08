# Unwrangle → amazon_products importer

This utility imports Unwrangle category JSON (with `category_results`) into the existing `amazon_products` table while preserving extra fields introduced by Unwrangle.

- No changes to the original import pipeline are required to run this tool.
- It writes booleans as text to maximize compatibility (e.g., "true"/"false").
- Category fields are normalized the same as the current RF pipeline and hierarchy JSON is saved only into `category_hierarchy`.

## Prerequisites
- Environment variables for Supabase:
  - `SUPABASE_URL`
  - `SUPABASE_SERVICE_KEY` (or `SUPABASE_KEY`)
- The script reuses `core.database.connection.get_supabase_service_client` if available; otherwise falls back to env-based client creation.

## Run
```bash
python unwrangle_into_DB/import_unwrangle_products.py --file backend/scraping/data/scraped/amazon/amazon_product_cat_6291359011_20250717_033759.json --batch-id 9999

python unwrangle_into_DB/import_unwrangle_products.py --file backend/scraping/data/scraped/amazon/amazon_product_cat_507840_20250717_034918.json --batch-id 9998
```
Optional limit:
```bash
python unwrangle_into_DB/import_unwrangle_products.py --file <path> --batch-id 9999 --limit 50
```

## Notes
- Deduplication: performed in-memory by `platform_id` (ASIN).
- Preserved Unwrangle fields (if present):
  - `parent_asin`, `variant_asins_flat`, `search_alias_title`, `search_alias_value`, `keywords`, `keywords_list_json`,
    `proposition_65_warning`, `has_size_guide`, `buybox_json`, `sold_by_amazon`, `fba`, `sold_by_third_party`,
    `shipping_raw`, `delivery_json`, `images_json`, `images_count`, `images_flat`, `videos_json`, `videos_count`,
    `a_plus_content_json`, `sub_title_text`, `sub_title_link`, `marketplace_id`, `specifications_json`,
    `specifications_flat`, `main_image_url`, `rating_breakdown_json`, `variants_json`, `raw_product_json`,
    `data_provider` (always `unwrangle`).
- Category normalization mirrors the existing logic: `category` (leaf name), `category_id` (leaf id), `categories_flat`,
  `category_l1_id..category_l6_id`, `category_deepest_level`, and `category_hierarchy` JSON.

## Testing
- Two recommended test runs:
  - Batch 9999: `amazon_product_cat_6291359011_20250717_033759.json`
  - Batch 9998: `amazon_product_cat_507840_20250717_034918.json`
- Validate in Supabase `amazon_products` table by filtering `batch_id` and checking core columns + the extra Unwrangle columns.

## Integration plan
- After validating this step, we will integrate the provider detection and adapter call into the existing import path with minimal changes, keeping most logic here to avoid regressions.


