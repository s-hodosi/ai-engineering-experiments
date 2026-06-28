## Why

Job Scout sends notifications for job postings that are weeks or months old and already closed ("No longer accepting applications"). Tavily's search index retains stale LinkedIn job pages long after they close, and the current pipeline has no age filtering.

## What Changes

- Add a three-layer freshness filter to `searcher.py` that discards results older than a configurable threshold (default 3 days)
- Layer 1: Parse "Posted X ago" text from Tavily snippet — drop if weeks or months
- Layer 2: Check Tavily `published_date` field — drop if older than `FRESHNESS_MAX_PUBLISHED_DAYS` (default 7 days)
- Layer 3: Append `after:<date>` operator to all Tavily queries — filters Google's index at source
- Add `FRESHNESS_MAX_AGE_DAYS` and `FRESHNESS_MAX_PUBLISHED_DAYS` to `config.env`
- No changes to LLM filter, notifier, or database

## Capabilities

### New Capabilities
<!-- None — this is an enhancement to an existing capability -->

### Modified Capabilities
- `job-search`: Adding freshness filter requirement — results older than threshold are discarded before the LLM call

## Impact

- `services/job-scout/searcher.py` — sole file changed
- `services/job-scout/config.env` — two new optional keys with defaults
- No dependency changes
