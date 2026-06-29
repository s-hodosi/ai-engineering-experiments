## Context

`searcher.py` parses age text from Tavily snippets (e.g. "4 days ago", "2 months ago") to discard stale jobs. The regex alternation and conversion table only cover `hour`, `day`, `week`, and `month`. A job snippet containing `"4 years ago"` produces no match, is treated as unknown age, and passes through.

## Goals / Non-Goals

**Goals:**
- Extend the regex and conversion table to handle `year` time unit

**Non-Goals:**
- Fixing the "no longer accepting" detection (that text is JS-rendered and unreliable in Tavily snippets — a structural limitation, not a bug to fix here)
- Any changes to Adzuna freshness (uses `created` date field directly, unaffected)

## Decisions

### Add `year` to existing regex and table
`_POSTED_RE` already handles bare age text without a "Posted" prefix (fixed in the previous freshness-filter change). Adding `year` to the alternation follows the same pattern. `365` days per year is a sufficient approximation — any job with a year-scale age is well beyond the 3-day threshold.

## Risks / Trade-offs

- None. The change is additive and touches two lines in one file.
