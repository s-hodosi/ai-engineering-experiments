## Context

`RelevanceFilter.evaluate()` (`filter.py`) sends one Gemini call per job: a fixed `_PROMPT_TEMPLATE` with the candidate profile (`profile.md`, loaded verbatim) interpolated in, plus job title/URL/location/snippet. Reviewing August 2026 output (96 RELEVANT/UNSURE rows) surfaced four precision problems:

1. **Repost spam**: 36 of 96 (37.5%) notifications were 5 repeating (title, company) pairs from recruiter-aggregator accounts (Jobs Ai, Hire Feed, Quik Hire Staffing), reposted under a new LinkedIn job ID each time. `job-deduplication` is strictly URL-keyed, so this is invisible to it by design.
2. **Pure IC roles leaking through**: "Staff Software Engineer," "Principal Software Engineer," "AI Platform Architect," "Founding engineer" — all zero people-management scope — got RELEVANT/UNSURE anyway.
3. **Adjacent-domain leadership leaking through**: QA, Security, Data, PMO, Governance/Risk, Consulting, Talent/L&D "Head of X"/"Director" roles matched despite not being software-engineering-org leadership.
4. **Bar has moved**: the candidate now wants only Senior EM and above (capped at VP Engineering); plain "Engineering Manager" and "Team Lead" are no longer targets.

Notably, problems 2 and 3 happened *despite* `profile.md`'s existing Target Roles list already not including IC titles or adjacent-domain titles — the LLM is already prone to being more permissive than the profile text alone specifies. This project has hit this exact failure mode once before: `location-filtering` was split out from `job-relevance-filter` into its own capability specifically because leaving location rules solely in the editable profile text wasn't reliable enough, and the rules ended up hardcoded directly into `filter.py`'s prompt template (in addition to living in `profile.md`) for enforcement strength. That precedent directly informs the approach here.

## Goals / Non-Goals

**Goals:**
- Eliminate recruiter-aggregator repost spam via a deterministic, pre-LLM blocklist (no LLM cost spent on known-bad sources).
- Make the "pure IC role" and "adjacent-domain leadership" disqualifiers stick, learning from the location-rules precedent that profile-text-only guidance has already proven insufficient for this LLM.
- Re-scope the target range to Senior EM+ (capped at VP Engineering, excluding CTO/Chief-level), judged by JD-described organizational scope rather than title string.
- Keep `profile.md` as the single human-editable source of truth for *what* the candidate wants; use hardcoded prompt reinforcement only for rules that have already proven to leak.

**Non-Goals:**
- Fuzzy/near-duplicate detection for unnamed future spam sources — explicitly deferred; blocklist is a static, manually maintained list per the user's choice.
- Changing anything about location filtering, dedup, or notification delivery — untouched by this change.
- Perfect precision on scope-based seniority judgment — the JD snippet is sometimes thin/truncated (`_MIN_JD_LENGTH = 200`, capped at 3000 chars, and JD fetch failures return `"[limited info — JD not accessible]"`), so some misses are expected and acceptable.

## Decisions

**Decision: New `job-source-blocklist` capability, applied as a pre-LLM filter stage, not folded into `job-relevance-filter` or `job-deduplication`.**

Mirrors the `location-filtering` precedent of splitting out a distinct, independently-reasoned-about rule into its own capability. It's conceptually different from both existing capabilities: `job-deduplication` is about *identity* (same URL/message seen before), while this is about *source quality* (a company/poster known to produce low-value reposts) — no identity check involved. Keeping it a separate stage also means it can run before the LLM call, saving cost, whereas relevance judgment necessarily requires the LLM.

**Decision: Blocklist is a simple, manually maintained list of company/poster names, checked case-insensitively against the job's `company` field, applied in `main.py`'s evaluation loop before `relevance_filter.evaluate()` is called.**

Chosen (per user's explicit choice) over fuzzy title-based dedup. Simple to reason about and extend; the cost is manual upkeep as new spammy posters appear, accepted as a fair trade for determinism.

**Decision: Blocklisted jobs are still recorded in `seen_jobs` with verdict `SKIP` (not a new distinct verdict value), and skip the LLM call.**

Keeps `seen_jobs.verdict` a stable 3-value enum (`RELEVANT`/`UNSURE`/`SKIP`) that existing tooling and the notification-loss diagnostic already rely on, rather than introducing a fourth value that every downstream query would need to special-case. If future debugging needs to distinguish "blocklisted" from "LLM SKIP," that's recoverable by cross-referencing `company` against the blocklist retroactively — company is already stored — so no information is lost by reusing `SKIP`.

**Decision: New disqualifiers (pure-IC, adjacent-domain-leadership, CTO exclusion, senior-scope requirement) are hardcoded into `filter.py`'s `_PROMPT_TEMPLATE`, in addition to being documented in `profile.md`'s Target Roles / Hard Disqualifiers sections.**

Rationale is the location-rules precedent described in Context: profile-text-only guidance already demonstrably under-enforces role-type matching (IC and adjacent-domain roles leaked through despite not being in the Target Roles list at all). Duplicating the critical rules into the code-level prompt template — the same treatment location rules got — is the most direct way to close that same class of leak for these new rules. `profile.md` remains the source of truth for target-role *content* (titles, what counts as "the candidate's domain"); the hardcoded template reinforces *enforcement* of the disqualifiers that have proven leaky.

**Decision: Seniority cutoff is scope-based (manages other managers / owns multiple teams or a department / reports to VP or C-level / explicit Director-or-above-equivalent title), not title-string matching.**

Per the user's explicit choice — titles demonstrably lie both ways ("Principal Engineering Manager" has no "Senior" but is clearly senior scope; many "Senior Engineering Manager" titles are just inflated first-line-manager titles). The rule anchors to the candidate's own background (Head of Department, 55-95 people, managing managers, per `profile.md`) as the practical bar.

**Decision: When the JD snippet doesn't contain enough scope information to judge seniority (thin snippet, fetch failure), the filter returns UNSURE rather than guessing either way.**

Consistent with the existing "when in doubt, use UNSURE — missed opportunities are worse than extra emails" principle already in `filter.py`. A scope-based rule is only as good as the signal available; defaulting to UNSURE on missing signal avoids systematically SKIPping good roles just because the snippet was thin (which would silently defeat the whole point of switching away from a title-only rule).

## Risks / Trade-offs

- **[Risk]** The blocklist requires manual maintenance — new spammy aggregator accounts will appear and won't be caught until noticed and added. → **Mitigation**: low-cost to extend (a list edit, no code change to add an entry); the same DB-vs-notification review method used to find the original 5 offenders can be re-run periodically to catch new ones.
- **[Risk]** Scope-based seniority judgment depends on JD snippet quality, which is often thin or fetch-failed. → **Mitigation**: default to UNSURE on insufficient signal (see Decision above) rather than silently over-SKIPping.
- **[Risk]** Hardcoding new rules into `filter.py`'s prompt template alongside `profile.md` creates two places that describe target-role logic, similar to the existing location-rule duplication. This is already an accepted pattern in the codebase, but it does mean future adjustments to these specific disqualifiers require a code change, not just a `profile.md` edit. → **Mitigation**: only the disqualifiers that have already proven to leak (IC roles, adjacent-domain, CTO exclusion) get hardcoded; the general target-role list and softer preferences stay in `profile.md` only.
- **[Trade-off]** Narrowing to Senior EM+ will reduce notification volume significantly (plain "Engineering Manager" was a large share of past RELEVANT verdicts). This is the explicit intent of the change, not a side effect to mitigate.

## Migration Plan

- No data migration — `seen_jobs` schema unchanged (blocklisted jobs reuse the existing `SKIP` verdict).
- Deploy is a code + config update: `profile.md`, `filter.py`, and the new blocklist list/module, plus `main.py` wiring the blocklist check before the LLM call.
- Rollback: revert the files; no persistent state depends on the new behavior.
- Post-deploy validation: after a couple weeks of real usage, review new RELEVANT/UNSURE output the same way the August data was reviewed here, to confirm the four leak patterns are gone and the volume drop matches expectations.

## Open Questions

- Exact initial blocklist contents beyond the three confirmed offenders (Jobs Ai, Hire Feed, Quik Hire Staffing) — worth a quick look at whether "wherewework Jobs" (which posts a mix of legitimate-looking Hungarian titles and generic ones) should also be added, or left alone since it didn't show the same repost-spam pattern as the other three.
