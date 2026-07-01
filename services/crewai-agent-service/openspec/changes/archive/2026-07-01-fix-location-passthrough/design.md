## Context

`linkedin_email_source.py::_parse_jobs_from_email` already parses a structured `location` string (e.g. "Hungary (Remote)") from each LinkedIn alert email's rich card text. `fetch_jobs()` builds the final job record from the parsed data but omits `location` from the dict it returns. Downstream, `filter.py::RelevanceFilter.evaluate()` formats a prompt from `title`, `url`, and `snippet` only — it has no `{location}` placeholder even though `job-relevance-filter`'s existing spec already says location should be passed to the LLM. `notifier.py` already does `job.get("location") or _extract_location(job)`, so it needs no code change — it will pick up the real value automatically once populated.

This is a two-file, single-service bug fix restoring behavior the specs already describe. No new dependencies, no data model changes, no cross-service impact.

## Goals / Non-Goals

**Goals:**
- Make the email-parsed `location` value survive into the job dict returned by `fetch_jobs()`.
- Make `RelevanceFilter` use that value in its prompt so location rules (UK-only SKIP, EU/EMEA RELEVANT) are evaluated against reliable data instead of guessing from JD snippet text.

**Non-Goals:**
- Persisting `location` in `jobs.db` (not required for filtering or notification; can be a future change if location is ever needed for later analysis/dedup).
- Removing `notifier.py::_extract_location`'s keyword-scan fallback — it stays as a last-resort for the rare case where the email itself has no parseable location (e.g. malformed rich-card text).
- Changing the location-filtering *rules* themselves (`profile.md`, the SKIP/RELEVANT logic) — this change only fixes what data those rules see, not the rules.

## Decisions

- **Add `location` as a plain top-level key in the job dict** (`services/job-scout/linkedin_email_source.py` `fetch_jobs()`), mirroring how `title`, `company`, and `snippet` are already handled. Alternative considered: wrapping location extraction into `_fetch_jd` so it comes from the JD page instead of the email — rejected, since the email's rich-card location is more reliable and already parsed; re-deriving it from JD text would reintroduce the exact failure mode this change fixes (many JD fetches return `[limited info — ...]`).
- **Add `{location}` to `filter.py::_PROMPT_TEMPLATE`** and pass `job.get("location", "")` when formatting. When empty (e.g. some future non-email source, or an email whose card didn't parse), the field renders as an empty value and the LLM falls back to inferring location from the snippet, same as today — no behavior regression for that edge case.
- **No change to `notifier.py`** — its existing `job.get("location") or _extract_location(job)` precedence already does the right thing; fixing the upstream data source is sufficient.

## Risks / Trade-offs

- [Some already-`seen_jobs` URLs were evaluated/notified under the old blind-filtering behavior before this fix] → No backfill; this only affects jobs processed after deployment. Acceptable since these are live alert notifications, not a batch dataset needing correction.
- [`location` string format varies ("Hungary (Remote)" vs "Budapest, Hungary" vs just "Remote")] → The LLM prompt already treats location as free text for interpretation (existing location-filtering rules are pattern-based, not exact-match), so format variance doesn't need normalization here.

## Migration Plan

Straightforward code change, no data migration. Deploy and verify with a manual `--once` run against a recent alert email known to include a location string (e.g. re-process or synthetically test with the EPAM Systems / Hungary (Remote) case from the bug report).
