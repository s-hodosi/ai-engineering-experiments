## 1. Fix freshness regex in searcher.py

- [x] 1.1 Add `year` to the `_POSTED_RE` regex alternation (alongside `hour|day|week|month`)
- [x] 1.2 Add `"year": 365` to `_DAYS_PER_UNIT` in `searcher.py`

## 2. Verify

- [x] 2.1 Run `python test_smoke.py` and confirm no jobs with year-scale age appear in output
