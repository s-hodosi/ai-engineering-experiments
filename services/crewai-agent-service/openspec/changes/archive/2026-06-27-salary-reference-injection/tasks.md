## 1. Data loading

- [x] 1.1 Add CSV loader in `agents.py`: read `salary_db.csv` from the service root using stdlib `csv`, format all rows as a markdown table string, store as module-level `SALARY_REFERENCE_TABLE`
- [x] 1.2 Handle missing file: raise `FileNotFoundError` with a clear message if `salary_db.csv` is not found at startup

## 2. Model update

- [x] 2.1 Add `reasoning: str` field to `SalaryEstimation` in `models.py`
- [x] 2.2 Add `unit: str` field to `SalaryEstimation` in `models.py`

## 3. Agent and prompt update

- [x] 3.1 Create a separate `llm_salary` instance in `agents.py` with `temperature=0.1`; assign it to `salary_agent`
- [x] 3.2 Rewrite task3 prompt to inject `SALARY_REFERENCE_TABLE`, instruct the agent to anchor on reference data first, use web search only for adjustments, output `salary_low`/`salary_high` as full integers in HUF, populate `reasoning` and set `unit` to `"monthly gross HUF"`, and flag `confidence: "low"` with explanation when no close match exists

## 4. Frontend update

- [x] 4.1 Update the salary card in `static/index.html` to display the `reasoning` field below the existing salary range and sources
- [x] 4.2 Display `unit` label next to the salary range (e.g. "2,300,000 – 2,900,000 monthly gross HUF")
