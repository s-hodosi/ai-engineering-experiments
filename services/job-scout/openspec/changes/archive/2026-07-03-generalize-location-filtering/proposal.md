## Why

The location-filtering rules only recognize the UK as a country-specific disqualifier. A remote role that names any other single country (e.g. "Remote, Germany", "must be based in Ireland", "hybrid, Berlin office") isn't caught, so the candidate (Hungary-based, not open to relocation) is currently notified about roles they can't take. The UK-only scope was a reasonable first cut, but the underlying rule was never actually about the UK — it's about any specific country other than Hungary.

## What Changes

- Replace the UK-only residency-restriction rule with a general rule: any job that names a specific single country other than Hungary as the required location — whether as a hard restriction ("must be based in Germany"), a bare remote location label with no further restriction language ("Remote, Germany"), or a requirement of physical on-site/hybrid presence in that country — returns SKIP.
- **BREAKING** (behavior change, not API): retires the previous "bare single-country remote label → UNSURE" carve-out. Today "Remote, UK" with no explicit restriction language returns UNSURE ("company may hire internationally"); this will now return SKIP, for the UK and every other non-Hungary country.
- Tighten the existing on-site/hybrid rule from "outside Hungary/EU" to "outside Hungary" — a non-Hungary EU country named specifically (e.g. "hybrid, Berlin office") now also returns SKIP, not just non-EU ones.
- A job listing several eligible countries that omits Hungary (e.g. "open to candidates based in Germany, Poland, or the Netherlands") returns SKIP.
- Keep unchanged: multi-region remote scopes that include EU/EMEA/Europe/global ("Remote UK/EU", "Remote EMEA", "Remote Europe", "Remote (global)") remain location-eligible, evaluated on role fit only. Keep unchanged: Hungary mentioned anywhere (alone or in a list) remains location-eligible.
- This is a prompt/spec wording change only — no new parsing, regex, or country-list logic. The filter is LLM-driven (Gemini via `filter.py`) and already recognizes countries semantically; the fix generalizes the rule text so UK is one example among several rather than the only covered case.

## Capabilities

### New Capabilities

(none)

### Modified Capabilities

- `location-filtering`: Requirement "UK-only remote roles are skipped" becomes a country-generic requirement (any non-Hungary country, not just UK), and drops the UNSURE carve-out for bare single-country remote labels. Requirement "Candidate location and relocation preference are encoded in filtering rules" narrows its on-site/hybrid scope from "outside Hungary/EU" to "outside Hungary". Requirement "Multi-region remote roles including EU are treated as relevant on location" is unchanged.

## Impact

- `filter.py`: `_PROMPT_TEMPLATE` location rules section (currently UK-specific examples) rewritten to be country-generic.
- `profile.md`: "Location Preferences" section rewritten to match the generalized rule.
- `openspec/specs/location-filtering/spec.md`: requirements rewritten per the delta spec in this change.
- No changes to `linkedin_email_source.py`, `db.py`, `notifier.py`, or `main.py` — location text already flows into the filter prompt unchanged; only the evaluation rule changes.
