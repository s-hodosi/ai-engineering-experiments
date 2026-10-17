## Context

`_fetch_jd` (in `linkedin_email_source.py`) makes one `requests.get` to `jobs-guest/jobs/api/jobPosting/{job_id}`, never inspects the status code, and looks for a description `div`. Anything other than a found div with ≥200 chars becomes `[limited info — JD not accessible]`; only raised exceptions are logged, and `scout.log` contains zero of those. The job is then evaluated and marked seen in the same run, so it is never fetched again.

Evidence gathered during exploration (2026-10-17):
- 20 sequential probes at 1 req/s across 9 job IDs: all 200 with description present.
- The same job ID returns materially different response bodies across requests (e.g. 52.7 KB vs 19.0 KB; 31 KB vs 42 KB), i.e. LinkedIn serves multiple page variants.
- The reported failure (4480388816) occurred in a 3-job run, ruling out within-run burst rate limiting for that case; the URL fetched cleanly hours later.

Working hypothesis: intermittent per-request variance (an auth-wall/challenge variant, or IP-level throttling influenced by other traffic from the same IP). Both are transient, which favours an immediate retry. The exact response LinkedIn sends on failure is unknown — hence the capture step.

## Goals / Non-Goals

**Goals:**
- Recover the majority of transient JD fetch failures within the same run.
- Make every residual failure diagnosable from the log plus a saved response.

**Non-Goals:**
- **Deferred retry across runs** (a "pending" state in `seen_jobs`, re-fetching on the next scheduled run). Revisit only if the new logs show failures persisting through in-run retries. It needs a schema change and changes notification timing, so it should be driven by data.
- Changing how a finally-failed job is evaluated or shown in the digest (it still goes to the LLM with the `[limited info …]` snippet, as today).
- Changing the ≥200-char threshold or passing short descriptions through.
- Using authenticated LinkedIn access or a headless browser.

## Decisions

### Outcome classification

Each attempt produces one of:

| Outcome | Condition | Retry? |
|---|---|---|
| `ok` | description element found, ≥200 chars | — |
| `short` | element found, <200 chars | no (content is genuinely short) |
| `gone` | HTTP 404 / 410 | no (posting removed) |
| `http_<code>` | any other non-200 (429, 999, 5xx, 403…) | yes |
| `no_jd` | 200 but no description element | yes (variant / auth wall) |
| `error` | request raised (timeout, connection) | yes |

Retrying `no_jd` is the important one: it is the silent case today and the most consistent with the observed failure. *Alternative considered:* retrying only on non-200 — rejected because the reported failure produced no exception and most likely a 200 response.

The returned snippet placeholders stay as they are today (`[limited info — JD not accessible]` for `short`/`no_jd`/`gone`, `[limited info — fetch failed]` for `error`/`http_*`), so the filter prompt's existing handling of `[limited info …]` is unaffected.

### Retry schedule

Up to 3 attempts total: initial, then after 3s, then after 10s. If a response carries `Retry-After` (seconds), use it instead for that wait, capped at 30s. *Alternatives:* exponential with jitter — unnecessary at this scale; longer waits (minutes) — would block a run that is otherwise ~1 req/s and starts edging toward the deferred-retry design we're explicitly not doing yet.

Worst case per failing job ≈ 13s (≤ ~60s with Retry-After); successful jobs pay nothing extra. The existing 1s inter-job sleep is kept.

### Logging

One line per failed attempt and one summary line on exhaustion, all with an ISO timestamp, job ID, attempt number, status code (or `-`), outcome, and response length. Successful first attempts log nothing (keeps the log quiet); a success after retry logs one recovery line, which is what tells us the retry is earning its keep. Logging stays as `print` to stdout, consistent with the rest of the service (stdout is already redirected to `scout.log` when headless).

### Failed-response capture

On final failure for retryable outcomes and `gone`, write the last response body to `debug/jd_failures/<job_id>_<YYYYmmddTHHMMSS>.html` (with status code and response headers as an HTML comment at the top). Keep only the 50 most recent files to bound disk use. Folder is git-ignored. `error` outcomes have no body; the exception text is already in the log. Capture is best-effort — a write failure must never break the run.

## Risks / Trade-offs

- [Retrying a throttled IP may extend the throttle] → only 2 retries, honour `Retry-After`, and failures are logged so a worsening pattern is visible.
- [Retry doesn't help if the cause is a persistent IP block lasting hours] → the logs will show retries exhausting consistently; that is the trigger to build deferred retry.
- [Captured HTML could contain cookies/tokens in headers] → only response headers are recorded (no request cookies are sent); folder is local and git-ignored.
- [Long runs after a large backlog] → bounded at ~13s per failing job; acceptable for a 30-minute schedule.

## Migration Plan

Drop-in: no schema or config change. Rollback is reverting the commit. After deploy, review `scout.log` and `debug/jd_failures/` after ~1 week to decide whether deferred retry is needed.
