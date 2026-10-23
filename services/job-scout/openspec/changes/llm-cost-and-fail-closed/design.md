## Context

See proposal.md (Why) for the motivation. The parts of the current code that shape this design:

- `linkedin_email_source.fetch_jobs` calls `mark_email_processed` for each alert email **during fetch**, before any job in it is evaluated. It also fetches each job's JD (≤3000 chars) during fetch. As a result, a job whose evaluation fails cannot be recovered from Gmail on a later run. Deferral needs its own persisted store, which is why the specs require a pending queue and not just "skip `mark_seen`".
- `filter.RelevanceFilter.evaluate` catches every exception and returns `("UNSURE", "Filter unavailable (<exc>) …")`. `main.run_once` then calls `mark_seen` for that job and adds it to the digest.
- litellm 1.83.7 surfaced today's billing error as `litellm.APIConnectionError` whose message contains the JSON body `{"code": 402, ..., "status": "RESOURCE_EXHAUSTED"}`. The exception class alone does not identify the error as billing.
- litellm's Gemini adapter maps `reasoning_effort` presets to Gemini `thinkingBudget` values (`"none"` → 0, `"low"` → 1024) (in `vertex_and_google_ai_studio_gemini.py`).
- Runs are every 2h (APScheduler, in-process). Volume is ~700 evaluations per month.

## Goals / Non-Goals

**Goals:**
- Fail closed on infrastructure errors while keeping fail-open on uncertain verdicts. "When in doubt, UNSURE" still applies to the model's judgment, not to outages.
- Make no extra LLM calls during a known fatal outage.
- Keep the change small and in the existing style: module-level functions in `db.py`, plain-text email in `notifier.py`, no new dependencies.

**Non-Goals:**
- Fallback to a second model or provider.
- Backoff or retry inside a single run. A deferred job waits for the next scheduled run, which already gives a 2h backoff.
- Re-evaluating jobs already lost to the 2026-10-23 outage.
- A recovery ("filter back up") email. Recovery shows up as deferred jobs appearing in the next digest.

## Decisions

### D1. Cap thinking with `reasoning_effort="low"`
Pass `reasoning_effort="low"` to `litellm.completion`. In 1.83.7 this maps to `thinkingBudget: 1024` (`DEFAULT_REASONING_EFFORT_LOW_THINKING_BUDGET`).
- *Rejected:* `"none"` (budget 0). In a 30-job comparison against default thinking, verdicts agreed on only 18/30 and matched stored verdicts on 19/30. Every flip was SKIP→UNSURE/RELEVANT on plain-titled EM roles, so the digest would get noisier.
- *Rejected:* default thinking (unbounded). It matched stored verdicts on 29/30 but averaged about 1,310 output tokens per call, roughly $2.90/month.
- *Chosen:* `"low"` matched stored verdicts on 27/30 jobs. All 3 misses were lenient (SKIP→UNSURE on plain-titled EM roles), with no RELEVANT→SKIP. It averaged about 890 output tokens per call (max 1,073), roughly $2.20/month, versus about 1,310 tokens and $2.90/month at default.
- *Alternative:* `"minimal"` (128). Not tested. It would land somewhere between `"low"` and `"none"` on both cost and accuracy.

### D2. `evaluate` returns a result or raises a classified error; `main` decides
`RelevanceFilter.evaluate` keeps its `(verdict, scope)` return on success. On failure it raises `FilterError(kind, reason, detail)`, where `kind` is `"fatal"` or `"transient"` and `reason` is `"billing"`, `"auth"`, or `"transient"`. `main.run_once` owns the policy: abort or continue, pending queue, retry cap.
- *Alternative:* return a sentinel verdict like `"ERROR"`. Rejected. It is the same shape as today's bug, a failure that looks like a verdict, and is easy to mis-handle at a call site.
- The raw exception text goes only to `scout.log`, never into email.

### D3. Classify by status code first, then message text
Read `getattr(e, "status_code", None)` and `str(e)`:
- **fatal/billing:** status 402, or the message contains `"code": 402` or `prepayment credits are depleted` (case-insensitive). This also catches the older 429 form of the billing message.
- **fatal/auth:** status 401 or 403, or the message contains `API_KEY_INVALID`, `API key not valid`, or `PERMISSION_DENIED`.
- **transient:** everything else.

Order matters: billing is checked before treating a 429 as transient. Matching on text is brittle, but it is the only reliable signal given that litellm wraps the error. The patterns live in one place so they can be extended.

### D4. `pending_jobs` table holds the full job record
```
pending_jobs(url TEXT PRIMARY KEY, title, company, location, snippet,
             attempts INTEGER DEFAULT 0, first_deferred_at TEXT, last_error TEXT)
```
- `defer_job(job, path, count_attempt: bool)`: insert, or update with `attempts = attempts + 1` only when `count_attempt` is true (the transient case). `INSERT … ON CONFLICT(url) DO UPDATE`.
- `load_pending(path) -> list[dict]` returns job dicts in the same shape `fetch_jobs` produces.
- `remove_pending(url, path)`.
- `is_pending(url, path)`: `fetch_jobs` skips a URL if `is_seen(...) or is_pending(...)`. This avoids a duplicate JD fetch and a double evaluation.
- *Alternative:* store only the URL and refetch the JD on retry. Rejected because it means extra LinkedIn requests, which are already rate-limited, and the JD may have been taken down.

### D5. Run order: pending first, then new; abort on fatal
```
jobs = load_pending() + fetch_jobs()        # pending first; fetch skips pending URLs
for job in jobs:
    blocklisted? → mark_seen SKIP, remove_pending, continue
    if aborted:  defer_job(job, count_attempt=False); continue
    try:  verdict, scope = evaluate(job)
          mark_seen(verdict); remove_pending; collect if RELEVANT/UNSURE
    except FilterError as e:
          fatal     → aborted = e; defer_job(job, count_attempt=False)
          transient → defer_job(job, count_attempt=True)
                      if attempts ≥ 5 → mark_seen ERROR; remove_pending;
                                         collect with GAVE_UP_NOTE
send digest if entries
handle alert state (D6)
```
- `fetch_jobs` still runs during an outage. It is cheap (IMAP plus JD fetches), and it moves new jobs into the pending queue so they are not lost when old emails fall outside the `_LOOKBACK_DAYS` window.
- The current early return on `if not jobs` stays, but it now checks the combined list, so a run with only pending jobs still evaluates them.
- The retry cap is a module constant `_MAX_TRANSIENT_ATTEMPTS = 5`. At a 2h cadence that is about 10h of retries.

### D6. Alert throttling with a tiny key/value table
```
service_state(key TEXT PRIMARY KEY, value TEXT)
  keys: outage_reason, last_alert_at
```
At the end of a run:
- **Fatal abort:** if `outage_reason` is unset, or `last_alert_at` is more than 24h ago, send the alert and set both keys. Set `outage_reason` either way.
- **No abort and at least one LLM call succeeded:** clear both keys (outage over).
- **No LLM calls made** (nothing to evaluate): leave the state unchanged. A quiet run says nothing about recovery.
- *Alternative:* alert every aborted run. Rejected because a weekend outage would produce about 24 emails.
- *Alternative:* store state in a file. Rejected because SQLite is already the persistence layer.

### D7. Alert email via `Notifier.send_alert(reason, pending_count)`
The subject is `[Job Scout] Filter down: <reason>`. The body is plain text and comes from a small map from reason to text:
- `billing` → "Gemini prepay credits are depleted. Top up (or enable auto-reload) at https://aistudio.google.com/ — pending jobs will be evaluated automatically on the next run after that."
- `auth` → "The Gemini API key was rejected. Check GOOGLE_API_KEY in config.env."

Both bodies append "`N` job(s) pending." The method shares SMTP setup with `send_digest`, factored into a private `_send(subject, body)`.

### D8. Given-up jobs in the digest
`_render_entry` is unchanged. `main` passes a fixed note as `scope`: "Could not be evaluated by the filter after repeated errors — review manually." The verdict slot carries `"ERROR"`, which the digest already ignores.

## Risks / Trade-offs

- [Thinking off lowers verdict quality on subtle seniority or scope rules] → Mitigation: `seen_jobs` does not store JDs, so there is no offline eval set. Tasks include a one-off manual spot check instead: evaluate one live batch (or the backlog that builds up during the outage) with thinking on and off, and compare verdicts. The bias stays toward UNSURE per the prompt. If quality drops noticeably, use a small budget (`"low"`) instead of re-enabling full thinking.
- [Provider changes the error text and billing errors get classified as transient] → Effect: jobs burn through 5 attempts and end up as ERROR entries in the digest, so they are still visible and still not silent. Mitigation: classification lives in one function, and the raw error is logged.
- [Pending queue grows without bound during a long outage] → Bounded by real job volume, about 25/day. SQLite handles that trivially. When billing returns, the first run evaluates the whole backlog in one go, which is the desired behavior.
- [A large backlog run hits rate limits] → Those jobs are deferred as transient (attempt +1) and picked up on later runs. Five attempts is enough headroom.
- [A crash between `mark_seen` and `remove_pending`] → The next run finds the job in pending but also seen. Mitigation: `load_pending` drops, and removes, any URL already in `seen_jobs`.

## Migration Plan

- `init_db` creates `pending_jobs` and `service_state` with `CREATE TABLE IF NOT EXISTS`. No change to existing tables and no backfill.
- Deploy: stop the scheduler process, pull, restart. Top up Gemini credits before or after; the order does not matter now.
- Rollback: revert the commit. The two new tables are ignored by old code. Any jobs left in `pending_jobs` at rollback are not evaluated by the old code. That is acceptable, and the table can be dropped.
