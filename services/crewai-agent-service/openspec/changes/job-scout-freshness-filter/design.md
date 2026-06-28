## Context

Job Scout currently returns stale LinkedIn job postings that are weeks or months old. Tavily's search index retains LinkedIn job page entries long after positions close. The `days=2` Tavily parameter has no effect on general web search (only on `topic="news"`), so no freshness filtering is happening today.

## Goals / Non-Goals

**Goals:**
- Discard results older than ~3 days before they reach the LLM filter
- Three-layer approach: query-level, snippet-parsed age, and published_date metadata
- Configurable thresholds via `config.env`
- Zero new dependencies

**Non-Goals:**
- Fetching the actual LinkedIn page to verify "No longer accepting" status (higher cost, LinkedIn auth wall risk)
- Filtering based on LinkedIn job ID heuristics (unreliable)
- Changes outside `searcher.py` and `config.env`

## Decisions

### D1: Three layers rather than one
No single signal is fully reliable. `after:` filters at the query level but uses Google's crawl date. `published_date` is absent on many results. Snippet text is present when available and is the most direct signal. Combining all three maximises coverage.

### D2: Snippet age parsed via regex, not LLM
Extracting "Posted X weeks ago" from text is deterministic regex work. Adding it to the LLM prompt would increase cost and introduce inconsistency. Regex is zero-cost and runs before the LLM call.

### D3: Asymmetric thresholds (3 days snippet, 7 days published_date)
`published_date` reflects Google's crawl date, not LinkedIn's posting date. A job posted 5 days ago might have been crawled by Google today — so a stricter threshold on `published_date` would cause false drops. The snippet "Posted X ago" text is LinkedIn's own display of the actual posting age, so a tighter threshold (3 days) is reliable there.

### D4: Pass-through when age is unknown
If neither snippet age nor `published_date` is available, the result passes. The `after:` query operator already reduces the pool at source. It is better to occasionally notify on a borderline result than to silently drop a fresh job.

### D5: Separate config keys with defaults
`FRESHNESS_MAX_AGE_DAYS=3` and `FRESHNESS_MAX_PUBLISHED_DAYS=7`. Both optional — service works without them using defaults. User can tighten or loosen without code changes.

## Risks / Trade-offs

- **[Index lag]** A job posted today may not be indexed by Google for 1-2 days. With a 3-day `after:` window, it still appears. Acceptable.
- **[LinkedIn snippet variability]** LinkedIn sometimes shows "Reposted X ago" instead of "Posted X ago". The regex must handle both.
- **[published_date unreliability]** Tavily may not include `published_date` for all results. Mitigated by the other two layers.
- **[Tight threshold drops fresh jobs]** A 3-day threshold means a job posted 4 days ago won't appear. Acceptable trade-off given the user's explicit preference.

## Open Questions

- None. Thresholds (3 days / 7 days) confirmed by user.
