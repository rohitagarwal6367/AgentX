"""
app.py
------
Premium Streamlit web interface for the Agentic AI Store Support Agent.
Run with:  streamlit run app.py

Features:
  • Dark gradient theme with Amazon-inspired orange accents
  • Chat-bubble conversation history
  • Clickable example question chips
  • Collapsible tool-call timeline in the sidebar
  • Live stats dashboard (orders loaded, products, categories)
  • Animated typing indicator feel via st.spinner
"""

import streamlit as st
from agent import run_agent, get_tool_log, clear_tool_log
from data import ORDERS, PRODUCTS
from tools import USE_LIVE_API, RAPIDAPI_KEY, RAPIDAPI_HOST

# ─────────────────────────────────────────────────────────────────────────────
# Page config (must be first Streamlit call)
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentX - AI Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# Custom CSS – dark premium theme
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* ── Global reset & fonts ── */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    /* ── Global background – pure black ── */
    .stApp, .main, .block-container {
        background: #000000 !important;
        color: #ffffff !important;
        font-family: 'Inter', sans-serif !important;
    }

    /* Force all Streamlit default text to white */
    .stApp * { color: inherit; }
    p, span, li, label, div { color: #ffffff; }

    /* ── Hide default Streamlit chrome ── */
    #MainMenu, footer, header { visibility: hidden; }

    /* ── Top header bar ── */
    .hero-banner {
        background: #111111;
        border: 1px solid rgba(255,255,255,0.12);
        padding: 1.6rem 2rem;
        border-radius: 20px;
        margin-bottom: 1.5rem;
        box-shadow: 0 8px 40px rgba(255,255,255,0.04);
        text-align: center;
    }
    .hero-banner h1 {
        margin: 0 0 0.3rem;
        font-size: 2.4rem;
        font-weight: 900;
        color: #ffffff;
        -webkit-text-fill-color: #ffffff;
        letter-spacing: -1px;
    }
    .hero-banner p {
        margin: 0;
        font-size: 0.9rem;
        color: #888888;
        font-weight: 400;
    }

    /* ── Stat cards ── */
    .stat-card {
        background: #111111;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 12px;
        padding: 1rem 1.2rem;
        text-align: center;
        transition: border-color 0.25s;
    }
    .stat-card:hover { border-color: rgba(255,255,255,0.4); }
    .stat-number {
        font-size: 2rem;
        font-weight: 800;
        color: #ffffff;
        -webkit-text-fill-color: #ffffff;
    }
    .stat-label {
        font-size: 0.78rem;
        color: #888888;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-top: 2px;
    }

    /* ── Input box – dark bg + white text ── */
    .stTextInput input,
    .stTextInput > div > div > input,
    [data-testid="stTextInput"] input,
    input[type="text"],
    input[type="search"] {
        background: #111111 !important;
        border: 2px solid rgba(255,255,255,0.25) !important;
        border-radius: 12px !important;
        color: #ffffff !important;
        caret-color: #ffffff !important;
        font-size: 1rem !important;
        font-weight: 500 !important;
        padding: 0.7rem 1rem !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stTextInput input:focus,
    .stTextInput > div > div > input:focus {
        border-color: rgba(255,255,255,0.6) !important;
        box-shadow: 0 0 0 3px rgba(255,255,255,0.1) !important;
        outline: none !important;
        background: #111111 !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stTextInput input::placeholder,
    .stTextInput > div > div > input::placeholder {
        color: #555555 !important;
        -webkit-text-fill-color: #555555 !important;
        font-weight: 400 !important;
    }
    /* Streamlit form – hide helper text & border */
    [data-testid="stForm"] { border: none !important; padding: 0 !important; }
    /* Hide "Press Enter to submit form" text */
    .stTextInput [data-baseweb="input"] ~ div small,
    .stTextInput ~ div small,
    [data-testid="InputInstructions"],
    small[class*="Instructions"] { display: none !important; visibility: hidden !important; }

    /* ── Chip buttons (example questions) – equal size, black, white text ── */
    .stButton > button {
        background: #0a0a0a !important;
        color: #ffffff !important;
        font-weight: 600 !important;
        border: 1px solid rgba(255,255,255,0.25) !important;
        border-radius: 12px !important;
        padding: 0 1rem !important;
        font-size: 0.88rem !important;
        height: 80px !important;
        min-height: 80px !important;
        width: 100% !important;
        white-space: normal !important;
        word-wrap: break-word !important;
        line-height: 1.35 !important;
        text-align: center !important;
        transition: background 0.15s, border-color 0.15s, transform 0.15s !important;
        box-shadow: none !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stButton > button:hover {
        background: #1a1a1a !important;
        border-color: rgba(255,255,255,0.6) !important;
        transform: translateY(-1px) !important;
        box-shadow: none !important;
    }

    /* ── Ask submit button – same height as input ── */
    .stFormSubmitButton > button {
        background: #0a0a0a !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        border: 1px solid rgba(255,255,255,0.35) !important;
        border-radius: 12px !important;
        padding: 0 1.5rem !important;
        font-size: 0.95rem !important;
        height: 46px !important;
        min-height: 46px !important;
        width: 100% !important;
        white-space: nowrap !important;
        transition: background 0.15s, border-color 0.15s !important;
        box-shadow: none !important;
        -webkit-text-fill-color: #ffffff !important;
    }
    .stFormSubmitButton > button:hover {
        background: #1a1a1a !important;
        border-color: rgba(255,255,255,0.7) !important;
        box-shadow: none !important;
    }

    /* ── Chat bubbles ── */
    .bubble-user {
        background: #111111;
        border: 1px solid rgba(255,255,255,0.15);
        border-radius: 18px 18px 4px 18px;
        padding: 0.85rem 1.1rem;
        margin: 0.5rem 0 0.25rem auto;
        max-width: 80%;
        color: #ffffff;
        font-size: 0.97rem;
        box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    }
    .bubble-agent {
        background: #0a0a0a;
        border: 1px solid rgba(255,255,255,0.1);
        border-radius: 18px 18px 18px 4px;
        padding: 0.85rem 1.1rem;
        margin: 0.25rem auto 0.5rem 0;
        max-width: 85%;
        color: #e0e0e0;
        font-size: 0.95rem;
        line-height: 1.65;
        box-shadow: 0 4px 16px rgba(0,0,0,0.5);
    }
    .bubble-label {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 0.3rem;
    }
    .label-user  { color: #cccccc !important; }
    .label-agent { color: #ffffff !important; }

    /* ── Example chips ── */
    .chip-row { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.6rem 0 1.2rem; }
    .chip {
        background: #111111;
        border: 1px solid rgba(255,255,255,0.2);
        border-radius: 20px;
        padding: 0.35rem 0.9rem;
        font-size: 0.82rem;
        color: #dddddd;
        cursor: pointer;
        transition: background 0.2s, border-color 0.2s;
        white-space: nowrap;
    }
    .chip:hover { background: #1e1e1e; border-color: rgba(255,255,255,0.5); }

    /* ── Tool log timeline ── */
    .tool-entry {
        border-left: 3px solid rgba(255,255,255,0.4);
        padding: 0.4rem 0.7rem;
        margin: 0.4rem 0;
        background: #111111;
        border-radius: 0 8px 8px 0;
        font-size: 0.82rem;
        color: #cccccc;
    }
    .tool-found  { border-left-color: #00c853; }
    .tool-miss   { border-left-color: #ff5252; }

    /* ── Divider ── */
    hr { border-color: rgba(255,255,255,0.1) !important; }

    /* ── Sidebar – very dark, near black ── */
    section[data-testid="stSidebar"] {
        background: #0a0a0a !important;
        border-right: 1px solid rgba(255,255,255,0.08) !important;
    }
    section[data-testid="stSidebar"] * { color: #cccccc !important; }

    /* ── Scrollbar ── */
    ::-webkit-scrollbar { width: 6px; }
    ::-webkit-scrollbar-track { background: #000000; }
    ::-webkit-scrollbar-thumb { background: #333333; border-radius: 3px; }
    ::-webkit-scrollbar-thumb:hover { background: #ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ─────────────────────────────────────────────────────────────────────────────
# Computed stats from real data
# ─────────────────────────────────────────────────────────────────────────────
_total_orders = len(ORDERS)
_total_products = len(PRODUCTS)
_categories = sorted({p["category"].title() for p in PRODUCTS.values()})
_total_categories = len(_categories)

# ─────────────────────────────────────────────────────────────────────────────
# Session state
# ─────────────────────────────────────────────────────────────────────────────
if "history" not in st.session_state:
    st.session_state.history = []
if "pending_question" not in st.session_state:
    st.session_state.pending_question = ""

# ────────# ─────────────────────────────────────────────────────────────────────────────
# Shared helper – run agent and store result
# ─────────────────────────────────────────────────────────────────────────────
def _run_question(q: str):
    """Run the agent for question q and prepend result to history."""
    q = q.strip()
    if not q:
        return
    with st.spinner("🤖 Agent is thinking…"):
        clear_tool_log()
        answer = run_agent(q)
        log = get_tool_log()
    st.session_state.history.insert(0, {"q": q, "a": answer, "log": log})


# ─────────────────────────────────────────────────────────────────────────────
# Example chips – clicking immediately runs the agent
# ─────────────────────────────────────────────────────────────────────────────
EXAMPLES = [
    "Where is order ORD0000001?",
    "Is there a cheaper alternative for ORD0000002?",
    "Tell me about product P00014",
    "Show me electronics products",
    "Do you have any wireless earbuds?",
    "What's the status of ORD0000050?",
    "Find me a fitness band",
    "Show books under $300",
]

# ── Centered project title banner ──────────────────────────────────────────
st.markdown(
    """
    <div class="hero-banner">
        <h1>✦ Agentic AI</h1>
        <p>AgentX &nbsp;·&nbsp; AI-powered order &amp; product intelligence</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("**💡 Try an example:**")
chip_cols = st.columns(4)
for i, ex in enumerate(EXAMPLES):
    with chip_cols[i % 4]:
        if st.button(ex, key=f"chip_{i}", use_container_width=True):
            _run_question(ex)
            st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# Input row  (st.form → Enter key OR button click submits)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("---")

with st.form(key="question_form", clear_on_submit=True):
    col_inp, col_btn = st.columns([5, 1])
    with col_inp:
        question = st.text_input(
            "Your question",
            placeholder="e.g. Where is order ORD0000042? · Show me laptops · Tell me about P00007",
            label_visibility="collapsed",
            key="main_input",
        )
    with col_btn:
        ask_clicked = st.form_submit_button("Ask", use_container_width=True)

if ask_clicked and question.strip():
    _run_question(question)

# ─────────────────────────────────────────────────────────────────────────────
# Chat history (newest first)
# ─────────────────────────────────────────────────────────────────────────────
if st.session_state.history:
    st.markdown("<br>", unsafe_allow_html=True)
    for entry in st.session_state.history:
        # User bubble
        st.markdown(
            f'<div class="bubble-label label-user">🧑 You</div>'
            f'<div class="bubble-user">{entry["q"]}</div>',
            unsafe_allow_html=True,
        )
        # Agent bubble – render markdown inside it
        agent_html = entry["a"].replace("\n", "<br>")
        st.markdown(
            f'<div class="bubble-label label-agent">🤖 Agent</div>'
            f'<div class="bubble-agent">{agent_html}</div>',
            unsafe_allow_html=True,
        )
        # Tool call mini-log (inline, compact)
        if entry["log"]:
            with st.expander(f"🔧 Tool calls ({len(entry['log'])})", expanded=False):
                for step in entry["log"]:
                    found_cls = "tool-found" if step["result_found"] else "tool-miss"
                    found_txt = "✅ Found" if step["result_found"] else "❌ Not found"
                    args_str = ", ".join(f"{k}={v!r}" for k, v in step["args"].items() if v is not None)
                    st.markdown(
                        f'<div class="tool-entry {found_cls}">'
                        f'<strong>{step["tool"]}({args_str})</strong> → {found_txt}'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        st.markdown("---")

# ─────────────────────────────────────────────────────────────────────────────
# Sidebar
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(
        "<h2 style='color:#ff9900;margin-bottom:0.2rem;'> Catalogue</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='font-size:0.82rem;color:#888;margin-top:0;'>"
        "Browse all 50 local products by category</p>",
        unsafe_allow_html=True,
    )

    for cat in _categories:
        cat_products = [
            p for p in PRODUCTS.values()
            if p["category"].title() == cat
        ]
        with st.expander(f"{cat}  ({len(cat_products)})", expanded=False):
            for p in sorted(cat_products, key=lambda x: x["price"]):
                st.markdown(
                    f"<div style='font-size:0.82rem;padding:0.2rem 0;border-bottom:"
                    f"1px solid #222;'>"
                    f"<span style='color:#ff9900;font-weight:600;'>{p['product_id']}</span> "
                    f"{p['name']}<br>"
                    f"<span style='color:#888;'>${p['price']:.2f} · {p.get('brand','')}</span>"
                    f"</div>",
                    unsafe_allow_html=True,
                )

    st.markdown("---")
    st.markdown(
        "<h3 style='color:#ff9900;'>ℹ️ How to Ask</h3>",
        unsafe_allow_html=True,
    )
    tips = [
        ("📦 Order status", "ORD0000001"),
        ("💡 Cheaper options", "cheaper alternative ORD0000002"),
        ("🏷️ Product detail", "P00014"),
        ("🔍 Product search", "wireless earbuds"),
    ]
    for icon_label, example in tips:
        st.markdown(
            f"<div style='font-size:0.82rem;padding:0.35rem 0;'>"
            f"<strong style='color:#ccc;'>{icon_label}</strong><br>"
            f"<span style='color:#ff9900;font-style:italic;'>\"{example}\"</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")
