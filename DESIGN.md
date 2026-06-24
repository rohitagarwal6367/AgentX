# Design Decisions Document

## 1. Overview

The agent answers customer questions about an online store, using three
tools: `get_order`, `search_products`, and `get_product`. The goal was to
make tool selection and chaining **transparent and explainable**, since
the evaluation explicitly involves discussing the implementation.

## 2. Why rule-based reasoning instead of an LLM call

I considered two approaches:

**A. LLM-driven planning** — send the question to an LLM with the tool
definitions and ask it to output a plan (which tools, in what order).

**B. Rule-based intent detection** — use regex/keyword matching to decide
tool calls directly in code.

I went with **B** for the core implementation, because:
- The problem space is small and well defined (3 tools, a handful of
  intents), so a hand-written decision tree is just as accurate and far
  more predictable.
- It removes a dependency on API keys/network access, so the project runs
  fully offline and is trivially testable (deterministic output).
- It is easy to explain line-by-line during an evaluation discussion —
  there is no "black box" step where I'd have to guess why the model
  chose a tool.

I kept an **optional hook** (`call_llm_polish` in `agent.py`) showing how
an LLM provider could be wired in to rephrase the final reply, to address
the bonus point without making the core logic depend on a paid API.

## 3. Tool selection logic

1. If the question contains an order id (`ORD-####`):
   - Call `get_order`.
   - If the question also mentions "cheaper"/"alternative", chain into
     `get_product` (to find each ordered item's category) and then
     `search_products(category=..., max_price=item_price)` to find a
     genuinely cheaper option in the same category.
   - Otherwise, just answer with order status + ETA.
2. Else if the question contains a product id (`PROD-###`):
   - Call `get_product` directly.
3. Else, treat it as a general search and call `search_products` with the
   cleaned-up keywords (filler words like "do/you/have/any" stripped).

This ordering matters: order-id detection is checked first because a
question can mention both an order id and implicitly a product (e.g. "the
shoes I ordered"), and the order is the more specific, more reliable
anchor to start the chain from.

## 4. Chaining example

For "Is there a cheaper alternative to the shoes I ordered in ORD-1001?":
1. `get_order("ORD-1001")` → returns the order with item "Running Shoes -
   Air Max" at ₹4999.
2. `get_product("PROD-200")` → returns category = "shoes".
3. `search_products("", category="shoes", max_price=4999)` → returns
   cheaper shoe options.
4. The cheapest of those is picked and presented to the customer.

This is a genuine 3-tool chain, driven entirely by data returned from
previous tool calls — nothing is hardcoded about which alternative to
suggest.

## 5. Error handling & avoiding fabrication

- `get_order`/`get_product` return `None` when not found (instead of
  raising or returning fake data); `run_agent` checks for `None` and
  replies with a clear, polite message.
- `search_products` returns an empty list when nothing matches; the
  formatter explicitly handles the empty case ("couldn't find any
  products...") rather than ever inventing a product name or price.
- All tool failures result in a customer-friendly sentence — the raw
  `None`/`[]` is never shown to the user.

## 6. Customer-friendly responses

Tool outputs are Python dicts — useful for code, useless for a customer.
Each intent has a dedicated formatter function
(`_format_order_status`, `_format_cheaper_alternatives`,
`_format_product_list`, `_format_product_detail`) that turns the dict(s)
into a short, plain-English sentence or bullet list. This separation also
makes it easy to swap in the optional `call_llm_polish` step later without
touching the decision logic.

## 7. Testing

`test_agent.py` covers: correct tool selection for orders/products/
search, multi-tool chaining for the "cheaper alternative" case (asserted
by checking which tools were logged), and graceful handling of invalid
order ids, invalid product ids, and empty search results.

## 8. What I'd improve given more time

- Use an LLM to parse messier/ambiguous natural language questions into a
  structured intent, falling back to the rule-based path when confidence
  is low.
- Add conversation memory so follow-up questions ("what about a cheaper
  one for the headphones too?") can refer to a previous order without
  repeating the order id.
- Swap the in-memory mock data for a real database/API layer.
