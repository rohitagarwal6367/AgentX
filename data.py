"""
data.py
--------
Loads real order and product data from Amazon.csv.
Builds ORDERS and PRODUCTS dicts consumed by tools.py.

ORDERS  key: "ORD0000001"  (exact OrderID from CSV)
PRODUCTS key: "P00001"      (exact ProductID from CSV)

Each order groups all rows with the same OrderID into a single
record with an 'items' list so the agent can iterate over them.
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Helper – derive ETA string from status
# ---------------------------------------------------------------------------
_STATUS_ETA = {
    "Delivered": "Already delivered",
    "Shipped": "2–4 business days",
    "Pending": "4–6 business days (processing)",
    "Returned": "Return processed",
    "Cancelled": "Order cancelled",
}


def _eta_from_status(status: str) -> str:
    return _STATUS_ETA.get(status, "Check with carrier")


# ---------------------------------------------------------------------------
# Load CSV once at import time
# ---------------------------------------------------------------------------
_CSV_PATH = os.path.join(os.path.dirname(__file__), "Amazon.csv")

try:
    _df = pd.read_csv(_CSV_PATH)
except FileNotFoundError:
    raise FileNotFoundError(
        f"Amazon.csv not found at {_CSV_PATH}. "
        "Please place Amazon.csv in the same folder as data.py."
    )

# ---------------------------------------------------------------------------
# Build PRODUCTS  {product_id -> product dict}
# ---------------------------------------------------------------------------
# Deduplicate: one entry per ProductID, use first-seen name/category/brand
# and the mean UnitPrice across all rows for that product.
_prod_agg = (
    _df.groupby("ProductID")
    .agg(
        ProductName=("ProductName", "first"),
        Category=("Category", "first"),
        Brand=("Brand", "first"),
        UnitPrice=("UnitPrice", "mean"),
    )
    .reset_index()
)

_CORRECT_CATEGORIES = {
    "P00001": "electronics", "P00002": "electronics", "P00003": "electronics",
    "P00004": "electronics", "P00005": "electronics", "P00006": "electronics",
    "P00007": "electronics", "P00008": "electronics", "P00009": "electronics",
    "P00010": "electronics", "P00011": "sports & outdoors", "P00012": "electronics",
    "P00013": "electronics", "P00014": "toys & games", "P00015": "home & kitchen",
    "P00016": "home & kitchen", "P00017": "home & kitchen", "P00018": "home & kitchen",
    "P00019": "home & kitchen", "P00020": "home & kitchen", "P00021": "sports & outdoors",
    "P00022": "sports & outdoors", "P00023": "home & kitchen", "P00024": "sports & outdoors",
    "P00025": "clothing", "P00026": "clothing", "P00027": "clothing", "P00028": "clothing",
    "P00029": "clothing", "P00030": "clothing", "P00031": "toys & games", "P00032": "toys & games",
    "P00033": "toys & games", "P00034": "home & kitchen", "P00035": "home & kitchen",
    "P00036": "home & kitchen", "P00037": "electronics", "P00038": "electronics",
    "P00039": "electronics", "P00040": "electronics", "P00041": "electronics",
    "P00042": "electronics", "P00043": "electronics", "P00044": "electronics",
    "P00045": "electronics", "P00046": "electronics", "P00047": "electronics",
    "P00048": "electronics", "P00049": "books", "P00050": "books"
}

PRODUCTS: dict = {}
for _, row in _prod_agg.iterrows():
    pid = str(row["ProductID"]).strip()
    cat = _CORRECT_CATEGORIES.get(pid, str(row["Category"]).strip().lower())
    PRODUCTS[pid] = {
        "product_id": pid,
        "name": str(row["ProductName"]).strip(),
        "category": cat,
        "brand": str(row["Brand"]).strip(),
        "price": round(float(row["UnitPrice"]), 2),
        "description": (
            f"{row['Brand']} brand product in the '{cat.title()}' category. "
            "Available on Amazon India."
        ),
    }

# ---------------------------------------------------------------------------
# Build ORDERS  {order_id -> order dict}
# ---------------------------------------------------------------------------
ORDERS: dict = {}
for order_id, group in _df.groupby("OrderID"):
    first = group.iloc[0]
    items = [
        {
            "product_id": str(item_row["ProductID"]).strip(),
            "name": str(item_row["ProductName"]).strip(),
            "price": round(float(item_row["UnitPrice"]), 2),
            "qty": int(item_row["Quantity"]),
        }
        for _, item_row in group.iterrows()
    ]
    oid = str(order_id).strip()
    ORDERS[oid] = {
        "order_id": oid,
        "status": str(first["OrderStatus"]).strip(),
        "eta": _eta_from_status(str(first["OrderStatus"]).strip()),
        "customer_name": str(first["CustomerName"]).strip(),
        "order_date": str(first["OrderDate"]).strip(),
        "city": str(first["City"]).strip(),
        "state": str(first["State"]).strip(),
        "country": str(first["Country"]).strip(),
        "total": round(float(first["TotalAmount"]), 2),
        "payment_method": str(first["PaymentMethod"]).strip(),
        "items": items,
    }
