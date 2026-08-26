## 1. Notifier: digest sending

- [x] 1.1 Replace `Notifier.send(job, verdict, explanation)` with `Notifier.send_digest(entries)`, where `entries` is a list of `(job, verdict, explanation)` tuples
- [x] 1.2 Build a single email whose subject follows `[Job Scout] N new matches` (N = `len(entries)`)
- [x] 1.3 Render each entry in the body with its own title, company, location, verdict, job URL, and AI explanation paragraph, clearly delimited between entries
- [x] 1.4 Keep a single SMTP connect/login/send/quit for the whole digest (one connection per run, not per entry)

## 2. Orchestration: main.py

- [x] 2.1 In `run_once()`, collect `(job, verdict, explanation)` for every job evaluated as RELEVANT or UNSURE during the loop instead of calling the notifier inline
- [x] 2.2 After the evaluation loop, call `notifier.send_digest(entries)` once if `entries` is non-empty; send nothing if empty
- [x] 2.3 Update the run summary log line to reflect "1 digest email sent covering N jobs" (or equivalent) instead of "N emails sent out of M evaluated"

## 3. Verification

- [x] 3.1 Run `--once` locally against real/test data and confirm exactly one email is sent per run regardless of match count
- [x] 3.2 Confirm a zero-match run still sends no email (verified by code review of the `if entries:`/`else` branch — this run's `jobs.db` shows recent all-SKIP runs would hit the untested `else` branch; not yet observed live with the new code)
- [x] 3.3 Manually inspect a multi-match digest email for correct per-entry content and subject format (verified via a 3-entry test digest sent directly through `Notifier.send_digest()` with fabricated entries — subject read `[Job Scout] 3 new matches`, each entry rendered with its own title/company/location/verdict/URL/explanation, separated by delimiters)
- [x] 3.4 Update `test_smoke.py` if it references the old `Notifier.send()` signature

## 4. Post-deploy validation

- [ ] 4.1 After 1-2 weeks of real usage, re-run the DB-vs-Gmail reconciliation (compare `seen_jobs` RELEVANT/UNSURE count to actual digest emails found via Gmail "All Mail" search) to confirm the loss is resolved
- [ ] 4.2 If loss persists, revisit Open Questions in design.md (delivery observability, SMTP vs. Gmail API)
