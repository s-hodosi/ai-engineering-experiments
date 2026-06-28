## 1. Config

- [x] 1.1 Add `FRESHNESS_MAX_AGE_DAYS=3` and `FRESHNESS_MAX_PUBLISHED_DAYS=7` to `config.env` with comments

## 2. Freshness Filter in searcher.py

- [x] 2.1 Add `_parse_snippet_age_days(snippet)` — regex-extracts "Posted/Reposted X hours/days/weeks/months ago", returns age in days or `None` if not found
- [x] 2.2 Add `_is_fresh(result, max_age_days, max_published_days)` — applies all three layers: snippet age, `published_date`, and passes through if neither is present
- [x] 2.3 Extract `published_date` from Tavily result in the search loop (currently not captured)
- [x] 2.4 Append `after:<YYYY-MM-DD>` operator to each query string, computed as today minus `max_age_days`
- [x] 2.5 Call `_is_fresh()` inside `_passes_prefilter()` — discard result if it fails freshness check
- [x] 2.6 Accept `max_age_days` and `max_published_days` as parameters to `search()`, read from config in `main.py` and pass through

## 3. Wiring in main.py

- [x] 3.1 Read `FRESHNESS_MAX_AGE_DAYS` and `FRESHNESS_MAX_PUBLISHED_DAYS` from env in `run_once()` and pass to `search()`

## 4. Verification

- [x] 4.1 Run `test_smoke.py` and confirm logged output shows freshness filter discarding at least some results; verify no "Posted X weeks/months ago" jobs appear in the kept set
