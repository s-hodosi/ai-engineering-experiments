## Context

`Notifier.send()` (`notifier.py:37-65`) opens a new `smtplib.SMTP` connection, authenticates, and sends exactly one email, once per RELEVANT/UNSURE job, called from a loop in `main.py:run_once()`. There is no delay between calls and no connection reuse. Diagnostic cross-referencing of `jobs.db` (`seen_jobs` table) against `scout.log` for August 2026 found:

- 95 jobs marked RELEVANT/UNSURE, 95 corresponding `[notifier] Sent: ...` log lines (no exceptions anywhere in the send path)
- Only ~40 of those emails found in the account's Gmail "All Mail" (confirmed not a labeling/tab issue)
- Runs producing exactly 1 notification (42 emails, no burst) landed almost completely; runs producing 2+ notifications in the same run (53 emails across various bursts) were almost entirely missing, including a confirmed case (a 6-email burst on 2026-08-16) where a specific known job never arrived

This is consistent with Gmail's send-side abuse/reputation heuristics accepting (`250 OK`) and then silently discarding rapid, near-identical, self-to-self automated emails sent over a personal account's SMTP app-password auth. The SMTP transaction succeeding gives the sending code no signal that anything went wrong, so the current implementation cannot detect or recover from this — the loss is invisible short of the kind of manual DB/log/mailbox reconciliation done during diagnosis.

## Goals / Non-Goals

**Goals:**
- Eliminate the rapid multi-connection SMTP burst pattern that correlates with silent delivery loss.
- Preserve all existing per-job content (title, company, location, URL, verdict, AI explanation paragraph) — just reorganized into one email per run instead of one email per job.
- Keep the fix scoped to `notifier.py` and its caller in `main.py`; no scheduler, filter, or DB changes.

**Non-Goals:**
- Proving Gmail's exact server-side drop mechanism — the evidence (burst-correlated loss, no bounce, no spam trace) is strong but the fix targets the send *pattern*, not a confirmed Gmail internals root cause.
- Delivery confirmation / read receipts — out of scope for this change; if digest batching doesn't fully resolve loss, that's a follow-up.
- Migrating off SMTP+app-password to the Gmail API — noted as a possible future hardening step, not part of this change.
- Any change to how jobs are parsed, filtered, or deduplicated.

## Decisions

**Decision: Batch all of a run's notifications into a single digest email, sent once at the end of `run_once()`.**

This was chosen over the alternatives considered:
- *Add inter-send delay between individual emails*: reduces burst signature but still sends N emails per run for N matches; a run with many matches (the exact scenario that triggers loss) would still be the worst case, just slower. Doesn't fully eliminate the risk.
- *Reuse a single SMTP connection across sends within a run*: fewer auth handshakes, but still N distinct outbound messages sent in quick succession from the same connection — Gmail's heuristics plausibly key on message similarity/frequency more than connection count, so this doesn't clearly remove the pattern either.
- *Digest batching (chosen)*: caps outbound notification email volume at exactly one per scheduler run, regardless of how many jobs matched. Since runs are already spaced hours apart (current interval: 2 hours), this reduces the account's outbound automated-mail frequency to a pattern indistinguishable from a normal periodic personal email — the strongest available mitigation given the evidence, and the only one of the three that structurally removes bursts rather than just shrinking them.

Digest batching is also a reasonable UX improvement independent of the bug: one email summarizing "N new matches this run" is easier to scan than N separate emails arriving within the same minute.

**Decision: Digest is built and sent from `main.py:run_once()`, collecting `(job, verdict, explanation)` tuples during the evaluation loop, with `Notifier.send_digest()` replacing `Notifier.send()`.**

Keeps `notifier.py` responsible only for formatting/sending, and `main.py` responsible for orchestration, matching the existing separation of concerns.

**Decision: A run with zero matches still sends no email (unchanged from current behavior).**

No reason to notify about nothing; avoids adding notification noise.

## Risks / Trade-offs

- **[Risk]** Digest batching reduces frequency but does not empirically prove the burst theory — if some other mechanism is causing the loss, one email per run could still occasionally go missing. → **Mitigation**: the same DB-vs-received-count diagnostic method used to find this bug is cheap to repeat; validate over the following weeks by comparing `seen_jobs` RELEVANT/UNSURE counts to actual received digest emails.
- **[Risk]** If a run somehow produces an unusually large number of matches (e.g., after extended downtime + backlog), the single digest email could become very large. → **Mitigation**: not a new problem (the current code already sends unbounded-count emails per run); a single large email is strictly safer than many small ones from a delivery-pattern perspective, so no additional handling needed now.
- **[Trade-off]** Notifications are delayed until the end of the run's evaluation loop rather than fired immediately per job. Given the scheduler interval is hours, this is a negligible latency cost for a meaningful reliability gain.

## Migration Plan

- No data migration needed — `seen_jobs`/`processed_emails` schema and semantics are unchanged.
- Deploy is a straightforward code replace: update `notifier.py` and `main.py`, restart the service.
- Rollback: revert the two files; no persistent state depends on the new behavior.
- Post-deploy validation: after ~1-2 weeks, re-run the DB-vs-Gmail reconciliation (`seen_jobs` RELEVANT/UNSURE count vs. actual digest emails found in Gmail) to confirm the loss is resolved.

## Open Questions

- If digest batching does not fully eliminate loss (validated per Migration Plan), the next step would be adding delivery observability (e.g., logging digest send outcomes distinctly) or reconsidering SMTP vs. Gmail API — deferred until there's evidence digest batching alone is insufficient.
