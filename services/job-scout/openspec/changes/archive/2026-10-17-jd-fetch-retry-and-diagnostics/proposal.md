## Why

Job descriptions frequently fail to load from the LinkedIn guest API, so the digest shows only "Scope not described beyond the title…" for those roles. The failures are transient — job 4480388816 failed on 2026-10-17 in a run that made only 3 requests, yet the same URL returned its full 4,723-char description on 5 of 5 attempts a few hours later — but the current code gives up after one attempt, logs nothing (no status code, no reason, no timestamp), and marks the job seen, so the failure is permanent and undiagnosable.

## What Changes

- Classify every JD fetch outcome (success, HTTP error status, missing description element, too-short description, network exception) instead of collapsing non-success cases into a silent placeholder. This also makes the code honour the existing spec scenario for non-200 responses, which the implementation currently ignores.
- Retry transient failures immediately within the same run, with a short backoff (2 retries), honouring LinkedIn's `Retry-After` header when present. Permanent outcomes (404/410, description present but short) are not retried.
- Log each failed fetch attempt with timestamp, job ID, attempt number, HTTP status, and failure reason; log a final line when a job's retries are exhausted.
- Save the raw response body of a final failed fetch to a local, git-ignored debug folder (bounded in size) so the next failure reveals what LinkedIn actually returned.
- Prefix the per-run start log line with a timestamp so failures can be correlated with runs and time of day.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `linkedin-email-source`: the "LinkedIn JD page fetching" requirement gains retry-with-backoff for transient failures, explicit HTTP status handling, and diagnostic logging/response capture for failed fetches.

## Impact

- `linkedin_email_source.py`: `_fetch_jd` gains outcome classification, a retry loop, logging, and failed-response capture.
- `main.py`: timestamped run-start log line.
- `.gitignore`: new debug folder for captured failure responses.
- Run duration: each finally-failing job adds up to ~13s (more if `Retry-After` is honoured, capped); successful fetches are unaffected.
- No database schema change, no notification or filter change. Deferred retry across runs is explicitly out of scope (see design.md Non-Goals).
