# Munder Difflin Multi-Agent System - Design Notes

## 1. System Overview

This project automates paper supply operations for Munder Difflin using **smolagents** and a **text-only** multi-agent workflow. All customer input goes through one entry point; specialists handle inventory, quotes, and orders.

**Framework:** `smolagents` (`ToolCallingAgent`, `OpenAIServerModel`, `@tool`)  
**Model:** `gpt-4o-mini` via Vocareum OpenAI-compatible API  
**Data:** SQLite (`munder_difflin.db`) with starter helpers for transactions, stock, quotes, and financial reports

**Agent count:** 4 (within the 5-agent limit)


| Agent                 | Role                                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------- |
| **Orchestrator**      | Reads the customer request, picks specialists, merges results, returns one customer reply |
| **Inventory Agent**   | Stock checks, reorder checks, supplier stock orders                                       |
| **Quoting Agent**     | Historical quotes, unit prices, line-item quotes with bulk discounts                      |
| **Fulfillment Agent** | Feasibility checks, sales transactions, delivery estimates                                |


See `implementation_diagram.mmd` for the full workflow (agents, tools, database, supplier API).

---

## 2. Architecture and Flow

### 2.1 Why this design

- **One orchestrator** avoids a separate router agent and stays under the agent limit.
- **Three specialists** match the business: stock, pricing, and orders.
- **Tools wrap starter DB functions** so agents work with real inventory and transactions, not invented data.

### 2.2 Request flow

1. `run_test_scenarios()` loads `quote_requests_sample.csv`, initializes the DB, and builds each request as:
  `{request text} (Date of request: YYYY-MM-DD)`
2. `Orchestrator.handle_customer_request()` runs the main LLM with coordination tools.
3. The orchestrator calls specialists when needed:
  - `consult_inventory_agent` → `InventoryAgent`
  - `consult_quoting_agent` → `QuotingAgent`
  - `consult_fulfillment_agent` → `FulfillmentAgent`
4. Each specialist runs its own LLM with a narrow tool set and `as_of_date` in every tool call.
5. The orchestrator ends with `final_answer` for the customer.

**Typical paths**

- **Quote only:** Customer → Orchestrator → Quoting → (optional Inventory) → Customer  
- **Order with stock:** Customer → Orchestrator → Inventory → Fulfillment → Customer  
- **Large / low stock:** Inventory → Quoting → reorder or partial fulfill → Customer

### 2.3 Tools and database helpers

All required starter helpers are used in tools:


| Helper                       | Tool(s)                                                                                             |
| ---------------------------- | --------------------------------------------------------------------------------------------------- |
| `get_stock_level`            | `check_item_stock`, `check_reorder_needed`, `calculate_quote`, `check_can_fulfill`, `fulfill_order` |
| `get_all_inventory`          | `list_available_inventory`                                                                          |
| `create_transaction`         | `place_stock_order`, `fulfill_order`                                                                |
| `get_supplier_delivery_date` | `place_stock_order`, `get_delivery_timeline`, `fulfill_order`                                       |
| `get_cash_balance`           | `check_can_fulfill`, `get_cash_on_hand`                                                             |
| `search_quote_history`       | `get_quote_history`                                                                                 |
| `generate_financial_report`  | `get_financial_snapshot`                                                                            |


**Other logic**

- `resolve_item_name()` + `CUSTOMER_ITEM_ALIASES` map customer wording to catalog names.
- `bulk_discount_rate()`: 5% (100+), 10% (500+), 15% (1000+ units per item).
- `fulfill_order` blocks sales when stock is too low and returns shortfall + ETA.

---

## 3. Evaluation Results (`test_results.csv`)

**Run:** `uv run python project_starter.py`  
**Requests processed:** 20 / 20 (full `quote_requests_sample.csv`)  
**Empty responses:** 0  

### 3.1 Financial behavior


| Metric                    | Value      |
| ------------------------- | ---------- |
| Cash after request 1      | $45,116.70 |
| Cash after request 20     | $46,119.06 |
| Requests with cash change | 16 of 20   |
| Starting seed (DB)        | $50,000.00 |


Cash went down from the initial seed because of stock purchases and partial sales over the simulated dates. The rubric threshold (≥3 cash changes) is met.

### 3.2 Fulfillment and quotes


| Pattern                                            | Approx. count (keyword scan) |
| -------------------------------------------------- | ---------------------------- |
| Responses mentioning fulfillment                   | 14                           |
| Responses mentioning stock limits / cannot fulfill | 13                           |
| Responses with pricing / totals                    | 20                           |


**Rubric checks**

- ≥3 cash balance changes: **Yes** (16)  
- ≥3 quote/order activity: **Yes** (sales and quotes across the run)  
- Not all requests fully fulfilled: **Yes**, large orders, unknown SKUs (e.g. balloons, A3 paper, tickets), and stockouts appear in several replies (e.g. requests 6, 7, 14-16)

### 3.3 Strengths

1. **End-to-end pipeline works**: DB init, agent routing, transactions, and CSV output complete without errors.
2. **Clear agent split**: inventory, quoting, and fulfillment stay separate; matches the workflow diagram.
3. **Real tool use**: stock orders and sales update `transactions`; cash and inventory change in the report.
4. **Useful customer detail**: many replies include line items, prices, bulk discounts, and delivery dates.
5. **Item name mapping**: aliases reduce failures when customers say "glossy A4" instead of exact catalog names.
6. **Realistic failures**: the system often explains shortfalls instead of pretending all items exist.

### 3.4 Areas for improvement

1. **Final answer vs tool truth**: the orchestrator LLM sometimes says "fulfilled" while tools reported low stock or missing items (e.g. request 1: partial pricing, request 8: mixed fulfill/pending language).
2. **Invented catalog items**: occasional references to products not in `paper_supplies` (e.g. "A5 paper", balloons).
3. **Cost and latency**: each specialist is a full LLM call; 20 requests took ~14 minutes with heavy token use.
4. **Non-deterministic routing**: the orchestrator decides which specialist to call; there is no hard rule that fulfillment must follow a stock check.
5. **Single file**: all logic lives in `project_starter.py` (~1,330 lines), which is hard to test and maintain.

---

## 4. Suggestions for Further Improvement

This section is my personal take on what I would do next.

### 4.1 Observability - LangSmith

I'd use **LangSmith** to track experiments and agent performance:

- Trace orchestrator → specialist calls, tool inputs/outputs, and latencies per request.
- Compare prompts and models across runs.
- Debug wrong quotes or false "fulfilled" messages with full step history.

### 4.2 Agent evaluation metrics

I'd add automated checks on top of `test_results.csv`. These are the metrics I'd try first:


| Metric                          | What it measures                                                                    |
| ------------------------------- | ----------------------------------------------------------------------------------- |
| **G-Eval**                      | LLM-as-judge scores (correctness, coherence, helpfulness) on customer replies       |
| **pass@k**                      | Task success when the system gets up to *k* attempts (e.g. retry orchestration)     |
| **Faithfulness / groundedness** | Customer text matches tool JSON (no claim of fulfillment if `fulfill_order` failed) |
| **Tool-selection accuracy**     | Correct specialist and tools for the request type (quote vs stock vs order)         |
| **Task success rate**           | End-to-end: expected DB change (sale or stock order) when the customer asked to buy |


I'd also look at RAGAS-style relevancy scores and spot-check with human review on edge cases.

### 4.3 Modular code layout (`src/`)

I'd split the monolith into a `src/` layout, for example:

```
src/
  agents/          # Orchestrator, InventoryAgent, QuotingAgent, FulfillmentAgent
  tools/           # inventory.py, quoting.py, fulfillment.py
  db/              # re-export or thin wrappers around starter helpers
  catalog/         # aliases, resolve_item_name, bulk_discount_rate
  run_eval.py      # run_test_scenarios entry point
```

That way I could unit test `resolve_item_name` and `fulfill_order` without LLM calls, and keep the same behavior with cleaner boundaries.

### 4.4 Product behavior

1. **Response validator**: I'd add a check before `final_answer` so "fulfilled" only appears if `fulfill_order` succeeded for those lines.
2. **Stricter catalog**: if `resolve_item_name` fails, I'd force the orchestrator to list available items instead of inventing SKUs.
3. **Cheaper orchestration**: I'd try exposing specialist tools directly on the orchestrator (one LLM) or use a smaller model for specialists.
4. **Hide internal finance**: I'd keep `get_financial_snapshot` off the customer path and use it only in tests or admin tools.

### 4.5 Optional extensions

If I had more time, I'd explore:

- A **customer agent** to negotiate against quotes.
- A **terminal UI** showing which agent is running per step.
- A **business advisor agent** that reviews transactions and suggests restock or pricing changes.

---

## 5. How to Reproduce

```bash
uv sync
cp .env.example .env   # add UDACITY_OPENAI_API_KEY
uv run python project_starter.py
```

Outputs: console logs, `test_results.csv`, updated `munder_difflin.db`.

---

## 6. Submission Artifacts


| File                                  | Purpose                                               |
| ------------------------------------- | ----------------------------------------------------- |
| `project_starter.py`                  | Implementation                                        |
| `implementation_diagram.mmd` / `.png` | Workflow diagram                                      |
| `test_results.csv`                    | Evaluation output                                     |
| `DESIGN_NOTES.md`                     | This document: architecture, evaluation, improvements |


