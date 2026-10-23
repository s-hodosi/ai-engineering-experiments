## 1. Cheaper filter calls

- [x] 1.1 In `filter.py`, pass `reasoning_effort="low"` to `litellm.completion` (design D1). Verify: the 5.1 test asserts the parameter, and the 5.2 spot check reports reasoning-token usage.

## 2. Failure classification in the filter

- [x] 2.1 Add `FilterError(kind, reason, detail)` and a `_classify(exc)` helper in `filter.py` following design D3 (status code first, then message patterns for 402 / "prepayment credits are depleted" / 401 / 403 / API key invalid). Verify: `test_failure_handling.py` (task 5.1) asserts that a litellm `APIConnectionError` carrying today's 402 JSON body → fatal/billing, a 429 with the depleted-credits message → fatal/billing, a 401 → fatal/auth, and 503, timeout, and plain 429 → transient.
- [x] 2.2 Replace the catch-all fallback in `RelevanceFilter.evaluate` with: log the raw error to stdout, then raise `FilterError`. No `"UNSURE"` fallback, and no exception text in the return value. Verify: grep shows no "Filter unavailable" string remains, and the 5.1 test asserts `evaluate` raises when `litellm.completion` is mocked to fail.
- [x] 2.3 Update `test_smoke.py` to catch `FilterError` and print `[DEFERRED <kind>/<reason>]` instead of crashing. Verify: running it with an invalid `GOOGLE_API_KEY` prints a DEFERRED fatal/auth line.

## 3. Persistence

- [x] 3.1 In `db.py`, add the `pending_jobs` and `service_state` tables to `init_db` (design D4/D6, `CREATE TABLE IF NOT EXISTS`). Verify: `init_db` on a copy of the existing `jobs.db` succeeds twice in a row and leaves the `seen_jobs` row count unchanged.
- [x] 3.2 Add `defer_job(job, path, count_attempt)` (returns the new attempt count), `load_pending(path)` (drops and removes URLs already in `seen_jobs`), `remove_pending(url, path)`, and `is_pending(url, path)`. Verify: 5.1 asserts an upsert with no duplicates, that attempts increase only with `count_attempt=True`, that the job dict round-trips with title/company/location/snippet intact, and that a seen URL is purged on load.
- [x] 3.3 Add `get_state(key, path)` and `set_state(key, value, path)` (`value=None` deletes). Verify: 5.1 round-trip assertion.
- [x] 3.4 In `linkedin_email_source.fetch_jobs`, skip a URL when `is_seen(...) or is_pending(...)`, before the JD fetch. Verify: 5.1 (or a manual check) shows a pending URL in a parsed email does not trigger `_fetch_jd`.

## 4. Run orchestration and alerting

- [x] 4.1 Add `Notifier._send(subject, body)` and have `send_digest` use it. Add `send_alert(reason, pending_count)` with the reason→text map from design D7. Verify: 5.1 patches `smtplib.SMTP` and asserts the alert subject is `[Job Scout] Filter down: billing`, and that the body contains the AI Studio hint and the pending count but not the raw error text.
- [x] 4.2 Rewrite the evaluation loop in `main.run_once` per design D5: pending first, then new; blocklist; abort on fatal with no further LLM calls; defer transient with attempt+1; give up at `_MAX_TRANSIENT_ATTEMPTS = 5` → `mark_seen` ERROR plus a digest entry with the fixed note (D8). The early return now checks the combined list. Verify: 5.1 scenarios below.
- [x] 4.3 Add end-of-run alert handling per design D6 (send if there is no current outage or the last alert is more than 24h old; clear state after a run with at least one successful call and no abort; leave state unchanged when no calls were made). Verify: 5.1 scenarios below.

## 5. Verification

- [x] 5.1 Create `test_failure_handling.py` as a plain-assert script in the style of `test_smoke.py`. It uses a temp SQLite file and mocks `litellm.completion`, `fetch_jobs`, and `smtplib.SMTP`. No network. Cover the `llm-failure-handling` scenarios:
  - billing error on job 3 of 6 → jobs 1–2 in digest and seen, jobs 3–6 pending with attempts 0, exactly 3 LLM calls, 1 alert
  - second aborted run within 24h → no alert, attempts still 0
  - recovery run → all pending evaluated, queue empty, state cleared
  - new outage after recovery → immediate alert
  - one transient 503 → only that job deferred, the rest evaluated
  - a job failing transiently 5 runs in a row → seen as ERROR, digest entry shows the fixed note
  - a run with no new jobs but a pending job → still evaluated

  Verify: `python test_failure_handling.py` exits 0.
- [x] 5.2 Quality spot check (design D1): evaluate about 30 recent real JDs at the chosen budget and compare with the verdicts stored in `jobs.db`. Verify: the agreement rate and average output tokens are recorded in design D1.
- [ ] 5.3 Live check: top up Gemini credits, restart the scheduler, and confirm in `scout.log` that the next run evaluates without errors and that the digest contains no "Filter unavailable" text.
