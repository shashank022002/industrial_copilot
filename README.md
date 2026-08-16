# Industrial Copilot - AI4I 2020 Predictive Maintenance Prototype

A conversational assistant over the [AI4I 2020 Predictive Maintenance Dataset](https://archive.ics.uci.edu/dataset/601/ai4i+2020+predictive+maintenance+dataset). You ask it plain-English questions about machine conditions and failures, and it answers by actually querying the data through tool calls rather than just guessing from what the model already "knows."

Built natively in a WSL 2 Ubuntu Python environment, no Docker, no extra layers, just a venv and the dataset sitting on disk.

## Why it's built this way

- **No Docker.** Running everything natively through a Python virtual environment avoids the I/O overhead you get bouncing between Windows and WSL.
- **DuckDB does the heavy lifting.** It's embedded and file-backed, and it runs the SQL, aggregation, and JSON serialization directly. Pandas isn't in the loop for computation.
- **Function calling handled by the SDK.** The `google-genai` Chat implementation deals with tool routing and sequencing on its own, no manual `while` loop needed.
- **No RAG, no embeddings.** The data's tabular. SQL and tool-calling cover what's needed; vector search would be overkill here.

## Repo layout

```text
ai4i2020.csv                  # the dataset
.env                          # GEMINI_API_KEY=..., not committed
requirements.txt              # duckdb, google-genai, python-dotenv, sqlglot
src/
  data_store.py               # singleton DuckDB connection, loads the CSV automatically
  sql_guard.py                # AST-level validation for raw SQL (SELECT-only, row capped)
  tools.py                    # the callables the agent has access to
  agent.py                    # the Gemini chat loop tying model and tools together
evals/
  questions.json              # Structured benchmark questions and test cases
  run_evals.py                # Evaluation runner scoring agent answers against tolerances
```

## Setup

Needs Python 3.10+ in WSL.

**1. Set up the environment**

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**2. Configure `.env`**

```env
GEMINI_API_KEY=your_actual_api_key_here
GEMINI_MODEL=gemini-3.5-flash
SQL_ROW_CAP=500
```

**3. Run it**

```bash
python3 -m src.agent
```

## What each piece does

### `data_store.py`

Builds a persistent `local_data.duckdb` file the first time it runs, inferring the schema from `ai4i2020.csv` straight off the CSV. DuckDB handles the aggregations, filtering, and JSON serialization from there.

### `tools.py`

Five hardcoded tools, kept narrow on purpose so they run fast:

- `get_machine_record` pulls one machine's snapshot by Product ID
- `summarize_column` min/max/avg for a given operating condition
- `compare_groups` aggregates a metric across a categorical grouping
- `failure_breakdown` totals machines against all five failure modes
- `correlation_analysis` checks correlation between numeric columns

Plus one fallback:

- `run_sql_query` - lets the model write raw SQL, gated by `sql_guard.py`

### `sql_guard.py`

Parses whatever SQL the model writes into an AST using `sqlglot` and checks it against four rules before it's allowed to run: single statement only, `SELECT` only (no `DROP`/`UPDATE`/`INSERT`), only touches the `ai4i2020` table, and stays under the row cap (500 by default) so it doesn't flood the context window.

### `agent.py`

Sets up the `google-genai` client and hands the tools to the chat session directly `client.chats.create(config={'tools': [...]})`. Because the functions are passed in as-is, the SDK handles parallel calls (independent lookups firing at once) and compositional calls (one tool's output feeding the next) without you writing that logic yourself.

### `evals`

Provides an isolated, automated benchmark suite using `questions.json` to evaluate the agent's multi-turn conversational memory, numerical tolerance accuracy, and factual text grounding.