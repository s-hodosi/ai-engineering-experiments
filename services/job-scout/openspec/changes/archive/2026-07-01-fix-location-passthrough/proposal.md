## Why

LinkedIn alert emails often include a reliable, structured location string (e.g. "Hungary (Remote)") that `_parse_jobs_from_email` already extracts, but `fetch_jobs()` drops it before returning the job record. As a result, notification emails show "Location unclear" whenever the JD snippet fetch fails or omits location text (common, since LinkedIn's guest API frequently blocks scraping) — and more importantly, the LLM relevance filter's location rules (UK-only → SKIP, EU/EMEA → RELEVANT) are evaluated blind, guessing location from JD text alone instead of using the value already parsed from the email. This silently degrades the location filtering added in the prior `fix-location-filtering` change.

## What Changes

- Thread the `location` field extracted by `_parse_jobs_from_email` through `fetch_jobs()` into the job record returned to callers (`services/job-scout/linkedin_email_source.py`).
- Interpolate the job's `location` field into the `RelevanceFilter` prompt (`services/job-scout/filter.py`) so the existing location rules operate on the structured email-derived value, falling back to JD snippet text only when location is empty.
- No changes needed to `services/job-scout/notifier.py` — it already prefers `job.get("location")` over its keyword-scan fallback, so the fix cascades automatically once the field is populated.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `linkedin-email-source`: the job record returned by `fetch_jobs()` SHALL include the `location` field extracted from the alert email, not just title/company/snippet.
- `job-relevance-filter`: the LLM prompt SHALL explicitly include the job's `location` field (previously the requirement said location was passed but the prompt template never interpolated it).

## Impact

- `services/job-scout/linkedin_email_source.py` — add `location` to the dict appended in `fetch_jobs()`.
- `services/job-scout/filter.py` — add a `{location}` placeholder to `_PROMPT_TEMPLATE` and pass `job.get("location", "")` when formatting.
- No database schema changes; `location` is not currently persisted in `jobs.db` and this change does not add persistence.
