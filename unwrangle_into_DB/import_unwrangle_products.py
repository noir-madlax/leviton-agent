import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional


def _add_project_paths() -> None:
    """Ensure this script can import the backend modules without altering the repo.
    Adds project root and backend/ to sys.path dynamically.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(current_dir, os.pardir))
    backend_dir = os.path.join(project_root, "backend")
    if project_root not in sys.path:
        sys.path.append(project_root)
    if backend_dir not in sys.path:
        sys.path.append(backend_dir)


_add_project_paths()

try:
    # Preferred: reuse existing connection helper
    from core.database.connection import get_supabase_service_client  # type: ignore
    _SUPABASE_PROVIDER = "internal"
except Exception:
    # Fallback: create client from environment
    from supabase import create_client  # type: ignore

    def get_supabase_service_client():  # type: ignore
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise RuntimeError("SUPABASE_URL and SUPABASE_SERVICE_KEY/KEY are required")
        return create_client(url, key)

    _SUPABASE_PROVIDER = "env"


logger = logging.getLogger("unwrangle_import")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


def read_json(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_str(value: Any) -> str:
    if value is None:
        return ""
    try:
        s = str(value).strip()
        # Remove non-visible non-ASCII
        return "".join(ch for ch in s if 32 <= ord(ch) <= 126)
    except Exception:
        return ""


def extract_price_unwrangle(product: Dict[str, Any]) -> Optional[float]:
    try:
        buybox = product.get("buybox_winner") or {}
        price = buybox.get("price") or {}
        val = price.get("value")
        if isinstance(val, (int, float)):
            return float(val)
        # fallback: first prices[] object
        if isinstance(product.get("prices"), list) and product["prices"]:
            p0 = product["prices"][0]
            if isinstance(p0, dict) and isinstance(p0.get("value"), (int, float)):
                return float(p0["value"])
        return None
    except Exception:
        return None


def extract_list_price_unwrangle(product: Dict[str, Any]) -> Optional[float]:
    try:
        buybox = product.get("buybox_winner") or {}
        list_price = buybox.get("list_price") or {}
        val = list_price.get("value")
        if isinstance(val, (int, float)):
            return float(val)
        # search prices with is_rrp
        for p in product.get("prices", []) or []:
            if isinstance(p, dict) and (p.get("is_rrp") is True):
                v = p.get("value")
                if isinstance(v, (int, float)):
                    return float(v)
        return None
    except Exception:
        return None


def extract_rating_unwrangle(product: Dict[str, Any]) -> Optional[float]:
    val = product.get("rating")
    if isinstance(val, (int, float)):
        return float(val)
    # derive from rating_breakdown if counts exist
    rb = product.get("rating_breakdown") or {}
    try:
        counts = []
        for star_key, star_value in rb.items():
            if not isinstance(star_value, dict):
                continue
            count = star_value.get("count")
            if isinstance(count, int):
                star_num = {
                    "one_star": 1,
                    "two_star": 2,
                    "three_star": 3,
                    "four_star": 4,
                    "five_star": 5,
                }.get(star_key)
                if star_num:
                    counts.append((star_num, count))
        total = sum(c for _, c in counts)
        if total > 0:
            return sum(star * c for star, c in counts) / float(total)
    except Exception:
        pass
    return None


def extract_reviews_count_unwrangle(product: Dict[str, Any]) -> Optional[int]:
    rb = product.get("rating_breakdown") or {}
    try:
        total = 0
        for star_value in rb.values():
            if isinstance(star_value, dict) and isinstance(star_value.get("count"), int):
                total += int(star_value.get("count"))
        return total if total > 0 else None
    except Exception:
        return None


def extract_image_url(product: Dict[str, Any]) -> str:
    main = product.get("main_image") or {}
    if isinstance(main, dict) and main.get("link"):
        return safe_str(main["link"])
    images = product.get("images") or []
    if isinstance(images, list) and images:
        first = images[0]
        if isinstance(first, dict) and first.get("link"):
            return safe_str(first["link"])
    return ""


def build_category_fields(categories: Any) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "category": "",
        "category_id": None,
        "categories_flat": "",
        "category_hierarchy": None,
        "category_l1_id": None,
        "category_l2_id": None,
        "category_l3_id": None,
        "category_l4_id": None,
        "category_l5_id": None,
        "category_l6_id": None,
        "category_deepest_level": 0,
    }
    try:
        if isinstance(categories, list) and categories:
            names: List[str] = []
            valid: List[Dict[str, str]] = []
            for i, cat in enumerate(categories):
                if not isinstance(cat, dict):
                    continue
                name = safe_str(cat.get("name"))
                cat_id = str(cat.get("category_id")) if cat.get("category_id") is not None else None
                if name:
                    names.append(name)
                if cat_id is not None:
                    level = i + 1
                    if level <= 6:
                        result[f"category_l{level}_id"] = cat_id
                        result["category_deepest_level"] = level
                if name and cat_id:
                    valid.append({"name": name, "category_id": cat_id})

            if names:
                result["category"] = names[-1]
                result["categories_flat"] = " > ".join(names)
            if valid:
                result["category_id"] = valid[-1]["category_id"]
                result["category_hierarchy"] = {"categories": valid, "total_levels": len(valid)}
    except Exception:
        pass
    return result


def map_unwrangle_item(item: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    asin = item.get("asin")
    if not asin:
        return None

    buybox = item.get("buybox_winner") or {}
    delivery = buybox.get("delivery") or {}

    row: Dict[str, Any] = {
        "source": "amazon",
        "data_provider": "unwrangle",
        "platform_id": safe_str(asin),
        "title": safe_str(item.get("title")),
        "brand": safe_str(item.get("brand")),
        "price_usd": extract_price_unwrangle(item),
        "list_price_usd": extract_list_price_unwrangle(item),
        "rating": extract_rating_unwrangle(item),
        "reviews_count": extract_reviews_count_unwrangle(item),
        "position": item.get("position") if isinstance(item.get("position"), int) else None,
        "image_url": extract_image_url(item),
        "product_url": safe_str(item.get("link")),
        "availability": safe_str(delivery.get("availability_status")) or safe_str(buybox.get("availability_status")),
        "recent_sales": "",
        "is_bestseller": safe_str(item.get("is_bestseller")),
        "unit_price": safe_str((buybox.get("unit_price") or {}).get("raw")),
        "features": safe_str(item.get("specifications_flat")),
        "description": safe_str(item.get("description")),
        "extract_date": datetime.now().strftime("%Y-%m-%d"),
        # Extra Unwrangle-preserving columns
        "parent_asin": safe_str(item.get("parent_asin")),
        "variant_asins_flat": safe_str(item.get("variant_asins_flat")),
        "search_alias_title": safe_str(((item.get("search_alias") or {}).get("title"))),
        "search_alias_value": safe_str(((item.get("search_alias") or {}).get("value"))),
        "keywords": safe_str(item.get("keywords")),
        "keywords_list_json": item.get("keywords_list"),
        "proposition_65_warning": safe_str(item.get("proposition_65_warning")),
        "has_size_guide": safe_str(item.get("has_size_guide")),
        "buybox_json": buybox or None,
        "sold_by_amazon": safe_str(buybox.get("is_sold_by_amazon")),
        "fba": safe_str(buybox.get("is_fulfilled_by_amazon")),
        "sold_by_third_party": safe_str(buybox.get("is_sold_by_third_party")),
        "shipping_raw": safe_str(((buybox.get("shipping") or {}).get("raw"))),
        "delivery_json": delivery or None,
        "images_json": item.get("images"),
        "images_count": item.get("images_count") if isinstance(item.get("images_count"), int) else None,
        "images_flat": safe_str(item.get("images_flat")),
        "videos_json": item.get("videos_additional"),
        "videos_count": item.get("videos_count") if isinstance(item.get("videos_count"), int) else None,
        "a_plus_content_json": item.get("a_plus_content"),
        "sub_title_text": safe_str(((item.get("sub_title") or {}).get("text"))),
        "sub_title_link": safe_str(((item.get("sub_title") or {}).get("link"))),
        "marketplace_id": safe_str(item.get("marketplace_id")),
        "specifications_json": item.get("specifications"),
        "specifications_flat": safe_str(item.get("specifications_flat")),
        "main_image_url": safe_str(((item.get("main_image") or {}).get("link"))),
        "rating_breakdown_json": item.get("rating_breakdown"),
        "variants_json": item.get("variants"),
        "raw_product_json": item,
    }

    # category fields
    row.update(build_category_fields(item.get("categories")))
    return row


def import_file(file_path: str, batch_id: int, limit: Optional[int] = None) -> Dict[str, Any]:
    data = read_json(file_path)
    items = []
    if isinstance(data, dict) and isinstance(data.get("category_results"), list):
        items = data["category_results"]
    elif isinstance(data, list):
        items = data
    else:
        raise ValueError("Unsupported Unwrangle JSON structure: expected category_results[] or list")

    rows: List[Dict[str, Any]] = []
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            continue
        row = map_unwrangle_item(item)
        if not row:
            continue
        asin = row.get("platform_id")
        if asin and asin in seen:
            continue
        row["batch_id"] = batch_id
        rows.append(row)
        if asin:
            seen.add(asin)
        if limit and len(rows) >= limit:
            break

    if not rows:
        return {"status": "empty", "inserted": 0}

    client = get_supabase_service_client()
    logger.info("Inserting %d rows (provider=%s)", len(rows), "unwrangle")
    res = client.table("amazon_products").insert(rows).execute()
    inserted = len(res.data or [])
    logger.info("Inserted %d rows into amazon_products", inserted)
    return {"status": "ok", "inserted": inserted}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Import Unwrangle category_results JSON into amazon_products")
    p.add_argument("--file", required=True, help="Path to Unwrangle JSON file")
    p.add_argument("--batch-id", type=int, default=9999, help="Batch id to tag rows (default: 9999)")
    p.add_argument("--limit", type=int, default=None, help="Optional max rows to import")
    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    result = import_file(args.file, args.batch_id, args.limit)
    print(json.dumps(result, ensure_ascii=False))


