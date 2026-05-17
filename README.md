# Munder Difflin Multi-Agent System Project

Welcome to the starter code repository for the **Munder Difflin Paper Company Multi-Agent System Project**! This repository contains the starter code and tools you will need to design, build, and test a multi-agent system that supports core business operations at a fictional paper manufacturing company.

## Project Context

You’ve been hired as an AI consultant by Munder Difflin Paper Company, a fictional enterprise looking to modernize their workflows. They need a smart, modular **multi-agent system** to automate:

- **Inventory checks** and restocking decisions
- **Quote generation** for incoming sales inquiries
- **Order fulfillment** including supplier logistics and transactions

Your solution must use a maximum of **5 agents** and process inputs and outputs entirely via **text-based communication**.

This project challenges your ability to orchestrate agents using modern Python frameworks like `smolagents`, `pydantic-ai`, or `npcsh`, and combine that with real data tools like `sqlite3`, `pandas`, and LLM prompt engineering.

---

## What’s Included

From the `project.zip` starter archive, you will find:

- `project_starter.py`: The main Python script you will modify to implement your agent system
- `quotes.csv`: Historical quote data used for reference by quoting agents
- `quote_requests.csv`: Incoming customer requests used to build quoting logic
- `quote_requests_sample.csv`: A set of simulated test cases to evaluate your system

---

## Workspace Instructions

All the files have been provided in the VS Code workspace on the Udacity platform. Please install the agent orchestration framework of your choice.

## Local setup instructions

1. Install dependencies

This project uses [uv](https://docs.astral.sh/uv/) for Python and package management (Python 3.12+).

Install dependencies from `pyproject.toml`:

```bash
uv sync
```

To add packages later:

```bash
uv add <package-name>
```

2. Create .env File

Copy the example and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and set `UDACITY_OPENAI_API_KEY` to your Vocareum key.

This project uses a custom OpenAI-compatible proxy hosted at https://openai.vocareum.com/v1.

## How to Run the Project

Start by defining your agents in the `"YOUR MULTI AGENT STARTS HERE"` section inside `project_starter.py`. Once your agent team is ready:

```bash
uv run python project_starter.py
```

This runs `run_test_scenarios()`, which simulates customer requests and writes `test_results.csv`. Your system should coordinate inventory checks, generate quotes, and process orders.

For architecture, evaluation summary, and improvement ideas, see **[DESIGN_NOTES.md](./DESIGN_NOTES.md)**.

Output will include:

- Agent responses
- Cash and inventory updates
- Final financial report
- A `test_results.csv` file with all interaction logs

---

## Tips for Success

- Start by sketching a **flow diagram** to visualize agent responsibilities and interactions.
- Test individual agent tools before full orchestration.
- Always include **dates** in customer requests when passing data between agents.
- Ensure every quote includes **bulk discounts** and uses past data when available.
- Use the **exact item names** from the database to avoid transaction failures.

---

## Submission Checklist

Make sure to submit the following files:

1. Your completed `project_starter.py` with all agent logic
2. A **workflow diagram** (`implementation_diagram.mmd` / `.png`)
3. **DESIGN_NOTES.md** — system explanation, evaluation, and improvements
4. Outputs from your test run (`test_results.csv`)

---