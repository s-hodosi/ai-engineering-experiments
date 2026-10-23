## Why

The Gemini API moved to prepaid billing. On 2026-10-23 the project's credits ran out, and every filter call began failing with HTTP 402. The pipeline treats a failed LLM call as an `UNSURE` verdict. That has three effects:

- The job is marked seen, so it is never evaluated again.
- The digest shows the raw litellm exception as the job's scope summary.
- Nothing announces the outage. It looks like a normal digest full of junk.

Billing is now a hard limit, so two things matter: keep per-call cost as low as possible, and make an LLM outage loud and lossless instead of silent and lossy.

## What Changes

- **Cap Gemini 2.5 Flash "thinking"** on relevance-filter calls at a low budget (1024 tokens). Thinking tokens are billed as output, the most expensive side. By default Flash spends about 1,300 of them per call. Turning thinking off entirely was tested and rejected: verdicts matched the service's prior decisions on only 19/30 jobs, because the scope rules for plain-titled EM roles were no longer applied. A capped budget keeps the reasoning while bounding its cost.
- **An LLM failure is no longer a verdict.** When the filter call fails, the job is not marked seen, not added to the digest, and no exception text reaches any email.
- **Persist deferred jobs in a pending queue.** Each alert email is marked processed during fetch, before evaluation, so a job that fails evaluation would never come back from Gmail. Deferred jobs are stored with their already-fetched details (title, company, location, JD snippet) and re-evaluated on later runs before new jobs.
- **Classify failures:**
  - *Fatal* (billing depleted, invalid or denied API key): stop LLM calls for the rest of the run after the first occurrence, and send every remaining job to the pending queue.
  - *Transient* (rate limit, 5xx, timeout, connection error): defer only the affected job and continue the run.
- **Cap retries per job.** A job that keeps failing with transient errors is given up after a fixed number of attempts, so it cannot loop forever. Fatal-error runs do not count against a job's attempts. A billing outage of any length loses nothing.
- **Alert email on filter outage.** When the filter is down, send one short `[Job Scout] Filter down: <reason>` email with a plain-language reason and the pending-job count. Alerts are throttled so a multi-day outage does not produce one email per 2-hour run.
- Not in scope: recovering jobs already lost to today's outage, switching model or provider, and pre-LLM title filtering.

## Capabilities

### New Capabilities
- `llm-failure-handling`: how relevance-filter failures are classified (fatal vs transient), the pending-job queue and retry cap, run abort on fatal errors, and the throttled outage alert email.

### Modified Capabilities
- `job-relevance-filter`: the LLM call runs with a capped (low) reasoning/thinking budget. A failed call yields "no verdict" instead of a fallback `UNSURE` verdict.
- `job-deduplication`: a job is recorded as seen only once it has a real verdict (or has been given up after the retry cap), not "regardless of outcome" on first encounter.
- `job-notification`: a run may send an outage alert email in addition to the digest. Digest entries never contain raw error text.

## Impact

- **Code:** `filter.py` (capped thinking budget, error classification, no fallback verdict), `main.py` (pending-queue drain, run abort, alert send), `db.py` (new `pending_jobs` table and a small service-state record for alert throttling), `notifier.py` (alert email).
- **Data:** two new SQLite tables, created idempotently by `init_db`. Existing `seen_jobs` and `processed_emails` are unchanged.
- **Dependencies:** none new. The `reasoning_effort` → `thinkingBudget` mapping was confirmed in the installed litellm (1.83.7).
- **Cost:** lower per-call cost. Retrying deferred jobs adds at most a few extra calls per transient failure, bounded by the retry cap.
