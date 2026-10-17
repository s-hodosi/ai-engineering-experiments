## 1. Fetch outcome classification

- [x] 1.1 Refactor the single-request part of `_fetch_jd` into a helper returning `(outcome, text, response)` with outcomes `ok`/`short`/`gone`/`http_<code>`/`no_jd`/`error` per design.md; verify by calling it on a live job ID (expect `ok`) and on a mocked 404, 429, and 200-without-description response (expect `gone`, `http_429`, `no_jd`)

## 2. Retry with backoff

- [x] 2.1 Wrap the helper in a retry loop: max 3 attempts, waits 3s then 10s, retry only `http_*`/`no_jd`/`error`; verify with a mocked sequence `no_jd → ok` that the second attempt's text is returned and that `gone`/`short` return after one attempt
- [x] 2.2 Honour `Retry-After` (integer seconds, capped at 30s) for the next wait; verify with a mocked response carrying `Retry-After: 45` that the wait used is 30s (patch `time.sleep` to record calls)
- [x] 2.3 Keep the existing placeholder strings (`[limited info — JD not accessible]` / `[limited info — fetch failed]`) mapped per the spec; verify the final returned snippet for an all-`no_jd` and an all-`error` sequence

## 3. Diagnostics

- [x] 3.1 Log each failed attempt (ISO timestamp, job ID, attempt n/3, status or `-`, outcome, response length), one recovery line on success-after-retry, and one final-failure line; verify by running the mocked sequences from 2.1 and inspecting stdout
- [x] 3.2 On final failure with a response body, write `debug/jd_failures/<job_id>_<YYYYmmddTHHMMSS>.html` with status and response headers in a leading HTML comment, wrapped in try/except so a write error only logs; verify the file appears for a mocked all-`no_jd` sequence and that a read-only target does not raise
- [x] 3.3 Prune `debug/jd_failures/` to the 50 most recent files after each write; verify by pre-creating 55 dummy files and checking 50 remain after one capture
- [x] 3.4 Add `debug/` to `.gitignore`; verify `git status` does not list captured files
- [x] 3.5 Prefix the `[main] Scout run starting...` line in `main.py` with an ISO timestamp; verify with `python main.py --once` output

## 4. Verification

- [x] 4.1 Run `python test_smoke.py` (after deleting `test_jobs.db`) and confirm the run completes, real JDs are still extracted, and any failures produce the new log lines (2026-10-17: 238 fetches; 5 × HTTP 429 all recovered on attempt 2 after a 3–4s wait; 5 × 404 `gone`, not retried; no other failures — 429 rate limiting is the observed cause)
- [x] 4.2 Update `openspec/specs/linkedin-email-source/spec.md` via archive/sync once implemented
- [ ] 4.3 After ~1 week of real runs, review `scout.log` recovery/final-failure lines and `debug/jd_failures/` captures; decide whether deferred cross-run retry (design.md Non-Goals) is warranted
