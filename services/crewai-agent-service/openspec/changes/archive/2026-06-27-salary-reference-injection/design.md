## Context

The salary agent currently guesses Budapest leadership salaries from web search results against US-centric sources. The user has a `salary_db.csv` file (28 rows, 2025–2026 Budapest market offers) covering leadership roles: Engineering Manager, Head of Engineering, Director, Program Manager, Release Train Engineer, Team Lead. The file is already in the service root.

The agent currently uses `temperature=0.7` and produces high variance across runs. The `SalaryEstimation` model has no field explaining how the estimate was derived.

## Goals / Non-Goals

**Goals:**
- Load `salary_db.csv` at server startup and inject the full table into task3's prompt
- Anchor salary estimation on the reference data; use web search only for adjustments
- Reduce run-to-run variance by lowering salary agent temperature to `0.1`
- Surface the agent's matching reasoning in the output via a new `reasoning` field
- Make the output unit explicit (`monthly gross HUF`)

**Non-Goals:**
- Filtering or ranking reference rows before injection — full table is injected every time
- Supporting multiple reference files or dynamic upload
- Covering IC (individual contributor) roles — the reference data is leadership-only; the agent should flag when no close match exists
- Hot-reloading the CSV without server restart

## Decisions

### D1: Load CSV at module init, format as markdown table string

**Decision**: Read `salary_db.csv` once at `agents.py` module load time using Python's stdlib `csv` module. Format all rows as a plain markdown table string stored in a module-level constant `SALARY_REFERENCE_TABLE`. Inject this string into task3's prompt template.

**Why not load per-request**: The file doesn't change between requests. Loading once at startup is simpler and faster.

**Why markdown table**: The LLM reads tabular data more reliably from markdown tables than from raw CSV. Keeps the prompt human-readable too.

**Why full table injection**: 28 rows ≈ 500 tokens. Negligible cost. Filtering logic could silently exclude relevant comps; the LLM can do its own relevance ranking.

### D2: Temperature 0.1 for salary_agent only

**Decision**: Instantiate a separate `LLM` for `salary_agent` with `temperature=0.1`. All other agents keep `temperature=0.7`.

**Why not 0.0**: Fully deterministic output can cause repetitive failures if the model gets stuck on a bad reasoning path. `0.1` gives minimal creativity while still being near-deterministic.

**Why only salary_agent**: The other agents (recruiter, market analyst, career advisor) benefit from more expressive reasoning. The salary agent is doing a lookup-and-adjust task where variance is harmful.

### D3: Add `reasoning` and `unit` fields to `SalaryEstimation`

**Decision**: Add `reasoning: str` (which reference rows were used, what adjustments were made) and `unit: str` (always `"monthly gross HUF"`).

**Why reasoning**: Makes the agent's matching logic visible and debuggable. If the estimate looks wrong, the user can see whether it found a close match or extrapolated from a distant one.

**Why unit**: Eliminates ambiguity — previously `currency` was just a string that could be "HUF", "USD", or inconsistent.

### D4: Prompt instructs agent to output in million HUF, matching the reference data

**Decision**: The task prompt explicitly states: "Return `salary_low` and `salary_high` as integers in HUF (not millions — multiply by 1,000,000)." This avoids the agent returning 2.5 instead of 2,500,000.

**Why**: The reference data uses millions (e.g. `2.3-2.9`) but the model fields are `int`. The agent needs explicit instruction on the unit conversion.

## Risks / Trade-offs

- **No close match in reference data** → Agent may extrapolate poorly for niche roles. Mitigation: prompt explicitly instructs the agent to flag `confidence: "low"` and explain the gap in `reasoning`.
- **CSV format changes break loading** → If `salary_db.csv` columns are renamed, the markdown formatter silently produces wrong output. Mitigation: column names are read from the header row dynamically, so minor reordering is fine; only renaming breaks things.
- **Reference data becomes stale** → 2025/2026 data will drift. Mitigation: replacing `salary_db.csv` triggers a server restart, which reloads the table. No code change needed.
- **`salary_low`/`salary_high` as integers** → If the agent returns a decimal (e.g. `2500000.5`), Pydantic will coerce it. Acceptable.
