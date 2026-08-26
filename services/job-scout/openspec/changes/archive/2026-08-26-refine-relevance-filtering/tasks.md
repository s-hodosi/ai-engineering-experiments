## 1. Source blocklist (Thread A)

- [x] 1.1 Add a blocklist list (e.g. `_BLOCKLISTED_COMPANIES` in a small module or a `config.env`/`profile.md`-adjacent list) seeded with confirmed offenders: Jobs Ai, Hire Feed, Quik Hire Staffing
- [x] 1.2 Decide on "wherewework Jobs" per design.md's Open Question — check whether it shows the same repost-spam pattern before including it (checked jobs.db: 16 rows, 15 distinct real Hungarian-market titles across many functions, not one generic template repeated — NOT the same repost-spam pattern; excluded from blocklist)
- [x] 1.3 In `main.py`'s evaluation loop, check each job's `company` field (case-insensitive) against the blocklist before calling `relevance_filter.evaluate()`
- [x] 1.4 Blocklisted jobs SHALL still call `mark_seen(..., verdict="SKIP", ...)` and SHALL NOT call the LLM
- [x] 1.5 Log blocklist exclusions distinctly (e.g. `[main] Blocklisted: <title> @ <company>`) so they're visible in scout.log without needing a DB query

## 2. Pure IC role disqualifier (Thread B)

- [x] 2.1 Update `filter.py`'s `_PROMPT_TEMPLATE` rules section with an explicit disqualifier: pure individual-contributor roles (Staff/Principal Engineer, Architect without management scope, "Founding Engineer" as hands-on IC) are SKIP regardless of technical fit
- [x] 2.2 Update `profile.md` Hard Disqualifiers section with the same rule for documentation/editability

## 3. Adjacent-domain leadership disqualifier (Thread C)

- [x] 3.1 Update `filter.py`'s `_PROMPT_TEMPLATE` rules section with the out-of-scope-function disqualifier (QA-only, Security-only, Data/Analytics-only, PMO, Governance/Risk/Compliance, Consulting, Talent/L&D, general GM/Operations), phrased so engineering-adjacent-but-actually-core roles (Platform Engineering, SRE) still pass
- [x] 3.2 Update `profile.md` Hard Disqualifiers section with the same rule

## 4. Senior-leadership-scope target range (Thread D)

- [x] 4.1 Rewrite `profile.md`'s Target Roles section: drop plain "Engineering Manager" and "Team Leader/Team Lead" as standalone valid targets, add "VP Engineering," describe the scope-based bar (manages managers / owns multiple teams or a department / reports to VP-or-above / explicit Director-or-above-equivalent title)
- [x] 4.2 Add the CTO/Chief-level exclusion to `profile.md`'s Hard Disqualifiers
- [x] 4.3 Update `filter.py`'s `_PROMPT_TEMPLATE` rules section with the same scope-based senior-bar logic and CTO exclusion, hardcoded per design.md's rationale (mirrors the existing location-rules precedent)
- [x] 4.4 Update `filter.py`'s rules section with the "insufficient scope signal → UNSURE, not SKIP" guidance, consistent with the existing "when in doubt, UNSURE" principle
- [x] 4.5 Update `filter.py`'s existing "Both technical EM roles and senior managing-managers roles are valid targets" line if needed so it doesn't contradict the new senior-only floor

## 5. Verification

- [x] 5.1 Run `--once` locally and confirm blocklisted companies (Jobs Ai, Hire Feed, Quik Hire Staffing) are excluded without an LLM call, visible in the new log line (live run found 0 new jobs this cycle, so no blocklisted posting happened to appear to exercise the skip-log-line end-to-end; instead unit-verified `_is_blocklisted()` directly — correctly matches all 3 blocklisted names case/whitespace-insensitively with no false positives on Wizz Air / wherewework Jobs. Full end-to-end log-line exercise will happen naturally next time a blocklisted poster's job appears — historically several times a week)
- [x] 5.2 Manually construct or find a few test cases per thread (plain "Engineering Manager" with no scope signal → SKIP; "Principal Engineering Manager" or department-scope EM → not auto-skipped; "Staff Software Engineer" → SKIP; "Head of Quality Assurance" → SKIP; "Head of Platform Engineering" with engineering-team JD → not skipped for this reason; CTO title → SKIP) and confirm verdicts match expectations (ran 7 synthetic cases directly through `RelevanceFilter.evaluate()` — all matched expectations)
- [x] 5.3 Confirm a thin/fetch-failed JD snippet with an otherwise plausible senior title returns UNSURE, not SKIP (verified in the same test run — "[limited info — JD not accessible]" + "Senior Engineering Manager" title returned UNSURE)

## 6. Post-deploy validation

- [ ] 6.1 After 1-2 weeks of real usage, review new RELEVANT/UNSURE output the same way August data was reviewed (title/company breakdown, repeat-pair counts) to confirm the four leak patterns are gone and volume dropped as expected
- [ ] 6.2 Extend the blocklist if new repost-spam sources are found during that review
