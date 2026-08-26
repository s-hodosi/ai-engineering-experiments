## Why

After ~2 months of real usage, a review of August 2026 notification data (96 RELEVANT/UNSURE jobs) surfaced four distinct precision problems in what job-scout considers "relevant": over a third of notifications are recruiter-aggregator repost spam that URL-based dedup can't catch, pure individual-contributor roles and adjacent-domain leadership roles (QA, Security, Data, PMO, Governance, Consulting) are leaking through as matches, and — now that the candidate has a clearer sense of what they're actually targeting — standard Engineering Manager and Team Lead roles are no longer the bar; only senior engineering leadership (Senior EM and above, capped at VP Engineering) should qualify.

## What Changes

- **BREAKING**: Standard "Engineering Manager" and "Team Leader/Team Lead" roles, previously valid targets, are now SKIP by default. Only Senior Engineering Manager, Director of Engineering, Head of Engineering, and VP Engineering (new) qualify — determined by the organizational scope described in the JD (manages other managers, owns multiple teams/a department, reports to VP/C-level, or an explicit senior-equivalent title), not by title string alone, since titles are shown to lie about seniority in both directions.
- CTO and other Chief-level titles are explicitly excluded (too broad/exec-generalist in scope) — VP Engineering is the top of the target range.
- Add a hard disqualifier: pure individual-contributor roles (e.g. Staff/Principal Software Engineer, Architect without management scope, "Founding Engineer" hired as a hands-on IC) are SKIP regardless of technical domain fit — closes a loophole in the existing "don't skip for being too technical" guidance.
- Add a hard disqualifier: leadership roles outside the software engineering/development organization (QA-only, Security-only, Data/Analytics-only, PMO/Program Management, Governance/Risk/Compliance, general business Consulting, Talent/L&D, general GM/Operations) are SKIP unless the JD explicitly describes leading a software engineering or development team.
- New deterministic blocklist stage: jobs from known recruiter-aggregator poster accounts (e.g. Jobs Ai, Hire Feed, Quik Hire Staffing) are excluded before the LLM relevance call — these accounts repost the same generic listing under a new job ID repeatedly, evading URL-based dedup entirely.

## Capabilities

### New Capabilities
- `job-source-blocklist`: Deterministic, pre-LLM exclusion of jobs whose posting company matches a maintained list of known low-quality/repost-spam sources, applied before the relevance filter stage to avoid both notification noise and wasted LLM calls.

### Modified Capabilities
- `job-relevance-filter`: Target role scope narrows from "EM and above" to "Senior EM and above, capped at VP Engineering," determined by JD-described organizational scope rather than title string; adds hard disqualifiers for pure IC roles and for leadership roles outside the software engineering organization.

## Impact

- `profile.md`: Target Roles section rewritten (drop plain EM/Team Lead as valid, add VP Engineering, describe the scope-based senior bar); Hard Disqualifiers section gains the IC-role and adjacent-domain-leadership entries plus the CTO exclusion.
- `filter.py`: prompt template likely needs the new disqualifiers reinforced directly in code (not just via the editable profile), following the existing precedent where location rules are hardcoded in the prompt template in addition to living in `profile.md` — because profile.md alone has already proven insufficient to stop the LLM from being too lenient on role-type matches (e.g. pure IC titles slipping through despite not appearing in the Target Roles list at all).
- New blocklist mechanism: likely a small config list plus a check in `main.py` or `linkedin_email_source.py` before jobs reach `RelevanceFilter.evaluate()`.
- `openspec/specs/job-relevance-filter/spec.md`: requirements updated per above.
- `openspec/specs/job-source-blocklist/spec.md`: new spec file.
- No changes to `job-deduplication`, `job-notification`, or `location-filtering` capabilities.
