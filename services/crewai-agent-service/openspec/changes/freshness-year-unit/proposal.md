## Why

The Tavily snippet freshness filter handles `hour`, `day`, `week`, and `month` time units but not `year`. When LinkedIn embeds `"4 years ago"` in a job snippet, the regex finds no match, age is treated as unknown, and the stale job passes through to Gemini and email. The "no longer accepting applications" check is also unreliable because that text is JavaScript-rendered and rarely appears in Tavily's static excerpt.

## What Changes

- Add `year` to the `_POSTED_RE` regex alternation in `searcher.py`
- Add `"year": 365` to `_DAYS_PER_UNIT` in `searcher.py`

## Capabilities

### New Capabilities
- none

### Modified Capabilities
- `job-search`: Snippet-based posting age filter now covers `year` as a time unit

## Impact

- `services/job-scout/searcher.py` — two-line change, no other files affected
