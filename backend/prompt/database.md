

create table public.product_wide_table (
  id serial not null,
  source text null,
  platform_id text null,
  title text null,
  brand text null,
  model_number text null,
  price_usd numeric(10, 2) null,
  list_price_usd numeric(10, 2) null,
  rating numeric(3, 2) null,
  reviews_count numeric(10, 1) null,
  position integer not null,
  category text not null,
  image_url text null,
  product_url text null,
  availability text null,
  recent_sales text null,
  is_bestseller text null,
  unit_price text null,
  collection text null,
  delivery_free text null,
  pickup_available text null,
  features text null,
  description text null,
  extract_date text null,
  cleaned_title text null,
  product_segment text null,
  refined_category text null,
  category_definition text null,
  created_at timestamp with time zone null default now(),
  updated_at timestamp with time zone null default now(),
  constraint product_wide_table_pkey primary key (id),
  constraint product_wide_table_platform_id_unique unique (platform_id)
) TABLESPACE pg_default;

create index IF not exists idx_category_position on public.product_wide_table using btree (category, "position") TABLESPACE pg_default;

create index IF not exists idx_refined_category on public.product_wide_table using btree (refined_category) TABLESPACE pg_default;

create index IF not exists idx_brand on public.product_wide_table using btree (brand) TABLESPACE pg_default;

create index IF not exists idx_source on public.product_wide_table using btree (source) TABLESPACE pg_default;

create index IF not exists idx_price_range on public.product_wide_table using btree (price_usd) TABLESPACE pg_default
where
  (price_usd is not null);

create trigger trigger_update_updated_at BEFORE
update on product_wide_table for EACH row
execute FUNCTION update_updated_at_column ();