"""
agent.py
--------
The core of the assignment: run_agent(question: str) -> str

DESIGN (rule-based reasoning, no paid LLM call required):
We use regex + keyword matching to decide which tool(s) to call,
in which order, and how to combine results into a friendly reply.

Data now comes from Amazon.csv (100 000 orders, 50 products, 6 categories).

ID formats used in Amazon.csv
  Orders  : ORD0000001 – ORD0100000
  Products: P00001     – P00050

The function ALWAYS:
  1. Logs every tool call (see TOOL_LOG) – bonus requirement.
  2. Returns a customer-friendly string, never raw dicts.
  3. Handles invalid order/product ids and empty search results gracefully.
  4. Never invents data that wasn't returned by a tool.
"""

import re
from tools import get_order, search_products, get_product

# ─────────────────────────────────────────────────────────────────────────────
# Logging (bonus requirement: log every tool call)
# ─────────────────────────────────────────────────────────────────────────────
TOOL_LOG: list = []


def _log(tool_name: str, args: dict, result) -> None:
    found = result is not None and result != []
    TOOL_LOG.append({"tool": tool_name, "args": args, "result_found": found})


def _call_get_order(order_id: str):
    result = get_order(order_id)
    _log("get_order", {"order_id": order_id}, result)
    return result


def _call_search_products(query: str, category=None, max_price=None):
    result = search_products(query, category=category, max_price=max_price)
    _log("search_products", {"query": query, "category": category, "max_price": max_price}, result)
    return result


def _call_get_product(product_id: str):
    result = get_product(product_id)
    _log("get_product", {"product_id": product_id}, result)
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Intent helpers
# ─────────────────────────────────────────────────────────────────────────────

# Amazon.csv order IDs: ORD0000001  (7+ digits, no dash after ORD)
ORDER_ID_PATTERN = re.compile(r"\bORD\d{3,}\b", re.IGNORECASE)

# Amazon.csv product IDs: P00001  (P followed by digits)
PRODUCT_ID_PATTERN = re.compile(r"\bP\d{4,}\b", re.IGNORECASE)

CHEAPER_KEYWORDS = [
    "cheaper", "cheap", "alternative", "lower price", "less expensive",
    "budget", "affordable", "discount", "save money",
]
STATUS_KEYWORDS = [
    "where", "track", "status", "when will", "arrive", "delivery",
    "deliver", "shipped", "dispatch", "eta",
]
RETURN_KEYWORDS = ["return", "refund", "cancel", "cancelled"]


def _extract_order_id(question: str):
    match = ORDER_ID_PATTERN.search(question)
    return match.group(0).upper() if match else None


def _extract_product_id(question: str):
    match = PRODUCT_ID_PATTERN.search(question)
    return match.group(0).upper() if match else None


def _wants_cheaper_alternative(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in CHEAPER_KEYWORDS)


def _wants_status(question: str) -> bool:
    q = question.lower()
    return any(kw in q for kw in STATUS_KEYWORDS)


# ─────────────────────────────────────────────────────────────────────────────
# Status badge helper
# ─────────────────────────────────────────────────────────────────────────────
_STATUS_EMOJI = {
    "Delivered": "✅",
    "Shipped": "🚚",
    "Pending": "⏳",
    "Returned": "↩️",
    "Cancelled": "❌",
}


def _status_badge(status: str) -> str:
    emoji = _STATUS_EMOJI.get(status, "📦")
    return f"{emoji} {status}"


# ─────────────────────────────────────────────────────────────────────────────
# Response builders (friendly text, never raw dicts)
# ─────────────────────────────────────────────────────────────────────────────

def _format_order_status(order: dict) -> str:
    items_text = ", ".join(
        f"{it['name']} (×{it['qty']})" for it in order["items"]
    )
    location = f"{order.get('city', '')}, {order.get('state', '')}"
    lines = [
        f"📦 Order **{order['order_id']}** — {_status_badge(order['status'])}",
        f"👤 Customer : {order.get('customer_name', 'N/A')}",
        f"🗓️  Order date: {order.get('order_date', 'N/A')}",
        f"📍 Location : {location}",
        f"🛍️  Items     : {items_text}",
        f"💰 Total    : ${order.get('total', 'N/A')}",
        f"🕐 ETA      : {order['eta']}",
    ]
    return "\n".join(lines)


def _format_cheaper_alternatives(order: dict, alternatives_by_item: dict) -> str:
    lines = [f"💡 Cheaper alternatives for order **{order['order_id']}**:\n"]
    any_found = False
    for item_name, alts in alternatives_by_item.items():
        if alts:
            any_found = True
            cheapest = min(alts, key=lambda p: p["price"])
            lines.append(
                f"• For **'{item_name}'** → **'{cheapest['name']}'** "
                f"by {cheapest.get('brand', 'N/A')} "
                f"at **${cheapest['price']:.2f}** (ID: {cheapest['product_id']})"
            )
        else:
            lines.append(f"• For **'{item_name}'** → no cheaper alternative found right now.")
    if not any_found:
        lines.append("Sorry, no cheaper alternatives are available at the moment.")
    return "\n".join(lines)


def _format_product_list(products: list, query: str = "") -> str:
    if not products:
        return (
            f"🔍 No products found matching **'{query}'**.\n"
            "Try a different keyword or browse a category like 'electronics', 'books', or 'clothing'."
        )
    # Check if results are from live API
    is_live = any(p.get("source") == "live" for p in products)
    source_badge = " 🌐 *Live from Amazon*" if is_live else " 📂 *Local catalogue*"

    # Cap at 8 results to keep the reply readable
    shown = products[:8]
    lines = [f"🛒 Found **{len(products)}** product(s)" + (f" matching **'{query}'**" if query else "") + source_badge + ":\n"]
    for p in shown:
        rating_str = f" | ⭐ {p['rating']}" if p.get("rating") else ""
        url_str = f" | [View on Amazon]({p['url']})" if p.get("url") else ""
        price_str = f"${p['price']:.2f}" if p["price"] > 0 else "Price N/A"
        lines.append(
            f"• **{p['name']}** — {price_str} "
            f"| Brand: {p.get('brand', 'N/A')} "
            f"| ID: `{p['product_id']}`"
            f"{rating_str}{url_str}"
        )
    if len(products) > 8:
        lines.append(f"\n_… and {len(products) - 8} more result(s). Narrow your search for fewer results._")
    return "\n".join(lines)


def _format_product_detail(product: dict) -> str:
    is_live = product.get("source") == "live"
    source_badge = " 🌐 *Live*" if is_live else " 📂 *Local*"
    rating_line = f"• Rating  : ⭐ {product['rating']}\n" if product.get("rating") else ""
    url_line    = f"• Link    : [View on Amazon]({product['url']})\n" if product.get("url") else ""
    price_str   = f"${product['price']:.2f}" if product.get("price", 0) > 0 else "See link"
    return (
        f"🏷️  **{product['name']}**{source_badge}\n"
        f"• Price   : **{price_str}**\n"
        f"• Brand   : {product.get('brand', 'N/A')}\n"
        f"• Category: {product.get('category', 'N/A').title()}\n"
        f"• Info    : {product.get('description', '')}\n"
        f"{rating_line}"
        f"{url_line}"
        f"• ID      : `{product['product_id']}`"
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_agent(question: str) -> str:
    """
    Decide which tool(s) to call based on the question, chain them if
    needed, and return a single customer-friendly string.
    """
    if not question or not question.strip():
        return (
            "Could you please tell me your question? "
            "You can ask things like:\n"
            "• 'Where is order ORD0000042?'\n"
            "• 'Is there a cheaper alternative to my order ORD0000001?'\n"
            "• 'Show me wireless earbuds'\n"
            "• 'Tell me about product P00014'"
        )

    order_id = _extract_order_id(question)
    product_id = _extract_product_id(question)

    # ── Case 1: question contains an order ID ────────────────────────────────
    if order_id:
        order = _call_get_order(order_id)
        if order is None:
            return (
                f"❌ I couldn't find any order with ID **'{order_id}'**.\n"
                "Please double-check the order number. "
                "Amazon order IDs look like ORD0000042."
            )

        if _wants_cheaper_alternative(question):
            # Chain: for each item in the order, search for a cheaper product
            # in the same category, priced strictly below that item's price.
            alternatives_by_item: dict = {}
            for item in order["items"]:
                product = _call_get_product(item["product_id"])
                category = product["category"] if product else None
                alts = _call_search_products("", category=category, max_price=item["price"])
                # Remove the original product itself
                alts = [a for a in alts if a["product_id"] != item["product_id"]]
                alternatives_by_item[item["name"]] = alts
            return _format_cheaper_alternatives(order, alternatives_by_item)

        # Default: return order status / tracking info
        return _format_order_status(order)

    # ── Case 2: question contains a specific product ID ──────────────────────
    if product_id:
        product = _call_get_product(product_id)
        if product is None:
            return (
                f"❌ I couldn't find any product with ID **'{product_id}'**.\n"
                "Product IDs look like P00001 or P00050. "
                "Try searching by name instead!"
            )
        return _format_product_detail(product)

    # ── Case 3: general product search ───────────────────────────────────────
    _filler = {
        "do", "you", "have", "any", "show", "me", "a", "an", "the",
        "is", "there", "i", "want", "looking", "for", "find", "get",
        "please", "can", "could", "what", "search",
    }
    keywords = " ".join(
        w for w in question.lower().split() if w not in _filler
    ).strip()
    search_query = keywords if keywords else question
    products = _call_search_products(search_query)
    return _format_product_list(products, query=search_query)


# ─────────────────────────────────────────────────────────────────────────────
# Log access helpers
# ─────────────────────────────────────────────────────────────────────────────

def get_tool_log() -> list:
    """Returns a copy of the tool-call log (for debugging/demo)."""
    return list(TOOL_LOG)


def clear_tool_log() -> None:
    TOOL_LOG.clear()


# ─────────────────────────────────────────────────────────────────────────────
# OPTIONAL BONUS: plug in a real LLM to "polish" the final reply.
# Disabled by default – no external dependency required to run the core agent.
# ─────────────────────────────────────────────────────────────────────────────

def call_llm_polish(raw_reply: str) -> str:
    """
    Example hook for using an LLM provider (bonus point).
    Uncomment and add your API key to activate.
    """
    # from anthropic import Anthropic
    # client = Anthropic(api_key="YOUR_KEY")
    # resp = client.messages.create(
    #     model="claude-sonnet-4-6",
    #     max_tokens=300,
    #     messages=[{
    #         "role": "user",
    #         "content": f"Rewrite this customer support reply to sound warmer:\n{raw_reply}"
    #     }]
    # )
    # return resp.content[0].text
    return raw_reply


if __name__ == "__main__":
    # Quick smoke-test when running `python agent.py`
    demo_questions = [
        "Where is order ORD0000001?",
        "Is there a cheaper alternative in my order ORD0000002?",
        "Tell me about product P00014",
        "Do you have any wireless earbuds?",
        "Show me electronics under 500",
        "What's the status of ORD9999999?",
    ]
    for q in demo_questions:
        print(f"\nQ: {q}")
        clear_tool_log()
        print(f"A: {run_agent(q)}")
        print(f"   [Tools called: {[e['tool'] for e in get_tool_log()]}]")
