## 1. Dependencies

- [x] 1.1 Add `feedparser` to `requirements.txt` (or install and verify with `pip install feedparser`)

## 2. Indeed RSS searcher

- [x] 2.1 Create `services/job-scout/indeed_searcher.py` with Indeed RSS query templates (role-title variants, `l=Europe` and `l=Budapest`, `fromage=1`, `sort=date`)
- [x] 2.2 Implement RSS fetch and parse using `feedparser`, returning list of dicts with `url`, `title`, `company`, `snippet`, `published_date`
- [x] 2.3 Implement `pubDate`-based freshness filter using `FRESHNESS_MAX_AGE_DAYS`
- [x] 2.4 Implement individual job URL filter for Indeed (discard search result pages)
- [x] 2.5 Implement title pre-filter using the same `_TITLE_RE` regex as `searcher.py` (no location filter)

## 3. Update searcher.py

- [x] 3.1 Remove the location pre-filter (`_LOCATION_RE` and location check in `_passes_prefilter`) from `searcher.py`
- [x] 3.2 Verify that `_passes_prefilter` in `searcher.py` retains only title match and freshness checks

## 4. Update main.py

- [x] 4.1 Import `indeed_searcher` and merge its results with Tavily results before deduplication
- [x] 4.2 Replace `SCHEDULE_INTERVAL_HOURS` with `SCHEDULE_INTERVAL_MINUTES` (default 30); update `BlockingScheduler` job to use `minutes=` parameter

## 5. Config

- [x] 5.1 Update `config.env`: replace `SCHEDULE_INTERVAL_HOURS=2` with `SCHEDULE_INTERVAL_MINUTES=30`

## 6. Smoke test

- [x] 6.1 Run `python test_smoke.py` and confirm Adzuna results appear alongside Tavily results in output
- [x] 6.2 Verify freshness filter works for Adzuna results (no stale jobs pass through)
