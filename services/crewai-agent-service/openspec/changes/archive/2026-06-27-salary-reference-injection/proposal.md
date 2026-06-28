## Why

The salary estimation agent produces inconsistent and often inaccurate results because it relies solely on web search against US-centric sources (Glassdoor, Levels.fyi) to estimate Budapest leadership salaries. The user has a curated dataset of 28 real 2025–2026 Budapest market offers that provides a far more reliable anchor than any web search result.

## What Changes

- Add `salary_db.csv` to the service as a persistent salary reference file (already placed in the service directory)
- Load the CSV at server startup and format it as a markdown table
- Inject the full reference table into the salary agent's task prompt as the primary calibration source
- Update the salary agent prompt to instruct it to anchor on the reference data first, use web search only for adjustments, and output in monthly gross HUF
- Lower `salary_agent` temperature from `0.7` to `0.1` to reduce run-to-run variance
- Update `SalaryEstimation` model to add a `reasoning` field explaining how the estimate was derived and which reference rows were used
- Add a `unit` field to `SalaryEstimation` to make the currency and period explicit (`"monthly gross HUF"`)

## Capabilities

### New Capabilities

- `salary-reference-data`: Loading and injecting the Budapest salary reference CSV into the salary estimation prompt

### Modified Capabilities

- `sse-progress`: No requirement changes — unaffected
- `dark-theme`: No requirement changes — unaffected

## Impact

- `salary_db.csv`: New reference data file in the service root (already present)
- `agents.py`: CSV loading at module init; updated task3 prompt; salary_agent temperature change
- `models.py`: `SalaryEstimation` gains `reasoning: str` and `unit: str` fields
- `static/index.html`: Salary card updated to display `reasoning` and `unit`
- No new dependencies required (`csv` module is stdlib)
