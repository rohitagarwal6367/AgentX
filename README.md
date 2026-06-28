# AgentX

An AI-powered customer support agent that answers questions about orders and products using data from `Amazon.csv` (100,000 real orders, 50 products) **and live Amazon product data via RapidAPI**. Built as part of an Agentic AI.

---


## ⚙️ Requirements

- **Python 3.8 or higher**
- **pip** (Python package installer)

---

## 🚀 Quick Start (Step by Step)

### Step 1 – Download / Clone the project

Make sure you have all these files in one folder:

```
Amazon.csv
agent.py
app.py
data.py
tools.py
```

### Step 2 – Install dependencies

Open a terminal / Command Prompt in the project folder and run:

```bash
pip install streamlit pandas requests
```

### Step 3 – Run the web app

```bash
python -m streamlit run app.py
```

This will print something like:

```
You can now view your Streamlit app in your browser.
Local URL: http://localhost:8501
```

### Step 4 – Open in your browser

Go to **http://localhost:8501** in any browser (Chrome, Edge, Firefox).

---

## 💬 How to Use the App

1. **Type a question** in the white input box (text appears in black)
2. Press **Enter** or click the **Ask ✨** button
3. The agent's answer appears below as a chat bubble
4. Expand **"🔧 Tool calls"** to see which tools the agent used

### Example questions to try:

```
Where is order ORD0000001?
Is there a cheaper alternative for ORD0000002?
Tell me about product P00014
Show me electronics products
Do you have any wireless earbuds?
Find me a fitness band
What's the status of ORD0000050?
```

You can also click the **quick example chips** at the top of the page to auto-fill a question.

---

## 📂 Project Structure

```
├── Amazon.csv          ← Real dataset (100,000 orders, 50 products)
├── data.py             ← Loads Amazon.csv and builds ORDERS + PRODUCTS dicts
├── tools.py            ← 3 tool functions: get_order, search_products, get_product
├── agent.py            ← Core agent logic: run_agent(question) → answer string
├── app.py              ← Streamlit web UI
├── test_agent.py       ← Unit tests
├── README.md           ← This file

```

---



### How it works:
- **Orders** always come from `Amazon.csv` (your CSV data is preserved)
- **Product searches** try the live API first, then fall back to local data if the API is unavailable
- Results show a 🌐 *Live from Amazon* badge when using real-time data

---

## 🔧 Available Tools (used internally by the agent)

| Tool | What it does |
|------|-------------|
| `get_order(order_id)` | Fetch full order details by ID |
| `search_products(query, category, max_price)` | Search products by keyword / filter |
| `get_product(product_id)` | Fetch a single product's details |

---

## 📞 Contact

If you have any queries, suggestions, or issues regarding this project, feel free to reach out:

* 📧 Email: **[rohitagarwal.se@gmail.com](mailto:agrwalrohit7877@gmail.com)**
* 🌐 GitHub: [Follow Me](https://github.com/rohitagarwal6367)
* 🔗 LinkedIn: [Connect With Me](https://www.linkedin.com/in/rohit-agarwal6367/)

---
