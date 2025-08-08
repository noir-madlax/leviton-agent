
### Data Import Design (Rainforest + Unwrangle into one table)

- Key decisions
  - Text fields can store boolean values as text for now to maximize compatibility. We will map Unwrangle boolean fields into existing text columns or new text columns if needed. No type change is planned in this round.
  - There are two category JSONB columns. One is often NULL. We will consistently save hierarchy JSON into the one that already has values (`category_hierarchy`) and ignore the empty one for writes. Read paths should prefer `category_hierarchy`.
  - Single table `amazon_products` remains the only sink. Upstream differences are hidden by provider-specific adapters returning a normalized product dict.

### Provider detection

- Rainforest JSON indicators:
  - Presence of top-level arrays `search_results` or `bestsellers_results`, each item containing fields like `ratings_total`, `image`, `prices`, `bestseller_badge`, `link`, etc.
- Unwrangle JSON indicators:
  - Presence of `request_parameters` with `type: "category"`, items under `category_results`, and item fields like `buybox_winner`, `search_alias`, `keywords_list`, `variants`, `a_plus_content`, `rating_breakdown`, `images_count`, etc.
- Pseudocode:
  - if `category_results` in data or `request_parameters` in data: provider = "unwrangle"
  - elif `search_results` in data or `bestsellers_results` in data: provider = "rainforest"
  - else: best-effort fallback by item signature

### Scope of changes (files and edits)

下面列出将要修改的文件与每处变更点，便于后续实施统计和评审。

- backend/scraping/common/result_processor.py

  - Add provider detection helper: DetectProvider(data) [1 edit]
  - Split mapping into provider-aware adapters:
    - RFAdapter.map(item) uses existing _extract_* helpers [1 edit]
    - UnwrangleAdapter.map(item) that maps:
      - price from buybox_winner.price.value
      - list_price from buybox_winner.list_price or prices is_rrp
      - image from main_image.link or images[0].link
      - rating from rating or derive from rating_breakdown
      - availability from buybox_winner.availability_status
      - features from specifications_flat + bullet points
      - categories array to existing category normalization
      - new extra fields into normalized dict (text/jsonb, see below)
    - Wire _extract_products_data to use detected provider and the respective adapter [1 edit]
  - Ensure category JSON is saved into `category_hierarchy` only [1 edit]
  - Total planned edits in this file: 4
- backend/core/services/data_import_service.py and/or backend/scraping/products/importer.py

  - Pass through batch_id set by caller (for tests 9999, 9998) without creating a new request when a test run dictates it; else follow current behavior [1 edit in importer]
  - Ensure source flag `data_provider` is included in each product row [1 edit]
  - Total planned edits across these two files: 2
- backend/core/repositories/amazon_product_repository.py

  - Keep existing insert behavior. No change required functionally.
  - Optionally add a new method batch_upsert_with_source if needed in later phase. Not required now. [0–1 optional edit]
- New constants/types (optional)

  - backend/scraping/common/providers.py (optional small helper): string constants "rainforest" | "unwrangle" [1 new file – optional]
- Total files to touch now: 2–3 files, 6 concrete edits (plus 0–1 optional file).

### Columns mapping recap and additional fields

- We will continue writing the normalized base fields already supported:
  - source, platform_id, title, brand, price_usd, list_price_usd, rating, reviews_count, position, image_url, product_url, availability, recent_sales, is_bestseller (text), unit_price (text), features, description, category, category_id, categories_flat, category_hierarchy (jsonb), category_l1_id..category_l6_id, category_deepest_level, extract_date, batch_id
- Additional Unwrangle fields to preserve (stored as text/jsonb; booleans as text):
  - parent_asin (text)
  - variant_asins_flat (text)
  - search_alias_title, search_alias_value (text)
  - keywords (text), keywords_list_json (jsonb)
  - proposition_65_warning (text: "true"/"false")
  - has_size_guide (text)
  - buybox_json (jsonb)
  - sold_by_amazon (text), fba (text), sold_by_third_party (text)
  - shipping_raw (text)
  - delivery_json (jsonb)
  - images_json (jsonb), images_count (text or int-as-text), images_flat (text)
  - videos_json (jsonb), videos_count (text or int-as-text)
  - a_plus_content_json (jsonb)
  - sub_title_text (text), sub_title_link (text)
  - marketplace_id (text)
  - specifications_json (jsonb), specifications_flat (text)
  - main_image_url (text)
  - rating_breakdown_json (jsonb)
  - raw_product_json (jsonb)
  - data_provider (text: "rainforest" | "unwrangle")

### Category strategy

- Write only to `category_hierarchy` (jsonb). Do not write to `categories_hierarchy`.
- Derive:
  - category = last category name (leaf)
  - category_id = last category_id (leaf)
  - categories_flat = joined by " > "
  - category_l1_id..category_l6_id and category_deepest_level using existing helper

### End-to-end steps per run

- Step 1: Load JSON and detect provider
- Step 2: Select the correct adapter
- Step 3: Transform each item to normalized product dict
- Step 4: Category normalization and hierarchy consolidation
- Step 5: Attach `data_provider`, `extract_date`, and test `batch_id` when provided
- Step 6: Batch insert to `amazon_products`

### Test plan

- We will run two manual tests, each on one JSON file:
  - Test A (batch_id = 9999): Use Unwrangle file `amazon_product_cat_6291359011_20250717_033759.json`
  - Test B (batch_id = 9998): Use Unwrangle file `amazon_product_cat_507840_20250717_034918.json`
  - Optionally Test C (batch_id = 9997): Use one existing Rainforest sample JSON to ensure backward compatibility
- Validation checklist after each import:
  - `platform_id`, `title`, `product_url` not null
  - Price/rating/reviews parsed when present
  - Category derived fields consistent: `category`, `category_id`, `categories_flat`, `category_l*`, `category_hierarchy`
  - `data_provider` correct
  - Text booleans (like `has_size_guide`, `proposition_65_warning`) saved as "true"/"false" if we create placeholders; otherwise skipped until columns exist
  - Row count matches processed distinct ASINs

### What we are not changing now

- No schema modifications in this round, per your request.
- No change to existing repository insert mechanics.
- No change to downstream analysis code; they will continue to read the normalized base columns.

### Risks / things to watch

- Some Unwrangle items may lack `buybox_winner` or categories; code must null-guard.
- Large JSONB blobs (when added in future migrations) may grow row size—consider later archiving strategy.
- Duplicate ASINs across providers: prefer insert-only with dedupe by `platform_id` in-memory; upsert behavior can be enabled later.

### Open questions (for future iterations)

- Should we add `data_provider` now as a text field in the table for observability? For now, we’ll include it only in the in-memory dict and skip writing if the column does not exist.
- Do we need an upsert-by-asin pathway to avoid duplicates across repeated tests? Current plan: leave as-is; rely on test batch_id separation.

---

- 实施统计

  - Files to modify: 2–3
  - Edits: 6 concrete edits
