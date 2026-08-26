## Why

Log/DB cross-referencing shows job-scout is silently losing a majority of its notification emails: in August 2026, 95 jobs were evaluated as RELEVANT/UNSURE and the log recorded a successful `[notifier] Sent: ...` line for all 95, but a search of the user's Gmail "All Mail" (not just Inbox/Spam) turned up only ~40 of those emails ever having arrived. Batch-size analysis of send timing shows the loss correlates with burst size: runs that sent exactly one notification came through almost intact (42 of 42), while runs that fired multiple near-identical self-addressed emails back-to-back within seconds lost nearly all of them. `Notifier.send()` opens a brand-new SMTP connection per email with no delay between sends, so any run with 2+ matches produces exactly this rapid-fire burst pattern — traffic that Gmail's send-side abuse/reputation heuristics can accept (`250 OK`, no exception raised) and then silently discard, leaving no bounce and no Spam-folder trace. The user is missing real, relevant job postings without any indication anything went wrong.

## What Changes

- Replace per-job immediate SMTP sends with a single digest email per scheduler run, covering all RELEVANT/UNSURE jobs found in that run. **BREAKING**: changes the "immediate email per matched job" notification contract to "one digest email per run."
- A run with zero matches continues to send no email (unchanged).
- A run with one or more matches sends exactly one email listing all of them, each with its role details, verdict, and AI relevance paragraph — eliminating the rapid multi-connection SMTP pattern that triggers silent delivery loss.

## Capabilities

### New Capabilities
(none)

### Modified Capabilities
- `job-notification`: Notification delivery changes from "one email sent immediately per matched job" to "one digest email per scheduler run, containing all matched jobs from that run." Email content requirements (role details, AI paragraph, per-job subject-line format) are preserved but reframed as per-entry content within the digest rather than per-email content.

## Impact

- `notifier.py`: `Notifier.send()` changes from single-job to multi-job digest; single SMTP connection per run instead of one per job.
- `main.py`: `run_once()` collects evaluated jobs and calls the notifier once per run instead of once per job.
- `openspec/specs/job-notification/spec.md`: requirements updated to reflect digest delivery.
- No database schema changes — `seen_jobs`/`processed_emails` tracking is unaffected.
