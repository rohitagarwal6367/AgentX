"""
tools.py
--------
The three tools the agent is allowed to use.

🔌 LIVE API MODE (RapidAPI):
  - Product searches use the RapidAPI "Real-time Amazon Data" API for live results.
  - If the API call fails (no subscription / network error), it automatically
    falls back to the local Amazon.csv product catalogue.

📦 Orders always come from Amazon.csv via data.py.

To activate live API searches:
  1. Go to https://rapidapi.com/letscrape-6bRBa3Q3OId/api/real-time-amazon-data
  2. Click "Subscribe to Test" → choose the FREE plan
  3. Your API key is already set below.

Product IDs in the CSV use the format  P00001 … P00050.
Order  IDs in the CSV use the format   ORD0000001 … ORD0100000.
"""

import requests
from data import ORDERS, PRODUCTS

# ─────────────────────────────────────────────────────────────────────────────
# RapidAPI Configuration
# ─────────────────────────────────────────────────────────────────────────────
RAPIDAPI_KEY  = "abdfb37748mshcaaa31ed17cbcb8p1477bfjsn5fd59fbf6e6c"
RAPIDAPI_HOST = "real-time-amazon-data.p.rapidapi.com"

_API_HEADERS = {
    "x-rapidapi-key":  RAPIDAPI_KEY,
    "x-rapidapi-host": RAPIDAPI_HOST,
}

# Set to False to always use local CSV data (useful for offline testing)
USE_LIVE_API = True


def _search_amazon_api(query: str, category: str = None, max_price: float = None) -> list:
    """
    Call the RapidAPI Real-time Amazon Data endpoint.
    Returns a list of product dicts in the same shape as PRODUCTS values.
    Returns None if the API call fails for any reason.
    """
    try:
        params = {
            "query":   query if query else (category or "products"),
            "page":    "1",
            "country": "IN",           # India (matches Amazon.csv)
            "sort_by": "LOWEST_PRICE", # most useful for price queries
        }
        resp = requests.get(
            f"https://{RAPIDAPI_HOST}/search",
            headers=_API_HEADERS,
            params=params,
            timeout=8,
        )

        if resp.status_code == 403:
            # Not subscribed to this API yet – fall back silently
            return None
        if resp.status_code != 200:
            return None

        data = resp.json()
        items = data.get("data", {}).get("products", [])
        if not items:
            return None

        results = []
        for item in items:
            price_raw = item.get("product_minimum_offer_price") or item.get("product_price") or ""
            # Strip currency symbols and commas, parse float
            price_str = str(price_raw).replace("₹", "").replace("$", "").replace(",", "").strip()
            try:
                price = float(price_str)
            except ValueError:
                price = 0.0

            # Apply max_price filter if provided
            if max_price is not None and price >= max_price and price > 0:
                continue

            # Apply category filter if provided (best-effort keyword match)
            item_title = (item.get("product_title") or "").lower()
            if category:
                cat_lower = category.lower()
                if cat_lower not in item_title:
                    # Loose match – skip only if we can clearly tell it's wrong
                    pass  # Amazon categories are implicit; don't filter too hard

            asin = item.get("asin", "")
            results.append({
                "product_id":   asin or f"LIVE_{len(results)+1:04d}",
                "name":         item.get("product_title", "Unknown Product"),
                "category":     category or "general",
                "brand":        item.get("product_brand") or "Amazon",
                "price":        round(price, 2),
                "description":  item.get("product_title", ""),
                "rating":       item.get("product_star_rating"),
                "url":          item.get("product_url", ""),
                "photo":        item.get("product_photo", ""),
                "source":       "live",
            })

        results.sort(key=lambda p: p["price"])
        return results if results else None

    except Exception:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# Tool 1 – get_order
# ─────────────────────────────────────────────────────────────────────────────

def get_order(order_id: str):
    """Fetch order details by order_id from Amazon.csv. Returns dict or None."""
    return ORDERS.get(order_id.strip())


# ─────────────────────────────────────────────────────────────────────────────
# Tool 2 – search_products
# ─────────────────────────────────────────────────────────────────────────────

def search_products(query: str, category: str = None, max_price: float = None):
    """
    Search products by keyword, optionally filtered by category / max_price.

    Order of preference:
      1. RapidAPI live results  (if USE_LIVE_API is True and subscription active)
      2. Local Amazon.csv data  (always available as fallback)

    Returns a list (possibly empty) of matching product dicts.
    """
    # ── Try live API first ───────────────────────────────────────────────────
    if USE_LIVE_API and query:
        api_results = _search_amazon_api(query, category=category, max_price=max_price)
        if api_results is not None:
            return api_results

    # ── Fallback: local CSV data ─────────────────────────────────────────────
    q = query.lower().strip()
    cat_filter = category.lower().strip() if category else None
    results = []
    for product in PRODUCTS.values():
        text_blob = (
            f"{product['name']} {product['description']} "
            f"{product['category']} {product['brand']}"
        ).lower()
        keyword_match = q == "" or any(word in text_blob for word in q.split() if word)
        category_match = cat_filter is None or cat_filter in product["category"]
        price_match    = max_price is None or product["price"] < max_price
        if keyword_match and category_match and price_match:
            results.append(dict(product, source="local"))

    results.sort(key=lambda p: p["price"])
    return results


# ─────────────────────────────────────────────────────────────────────────────
# Tool 3 – get_product
# ─────────────────────────────────────────────────────────────────────────────

def get_product(product_id: str):
    """
    Fetch a single product's details.
    Checks local PRODUCTS dict first (covers CSV product IDs like P00001).
    For live ASINs, returns None (the agent handles this gracefully).
    """
    pid = product_id.strip()
    return PRODUCTS.get(pid)
