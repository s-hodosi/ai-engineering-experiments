## 1. Update the LLM prompt

- [x] 1.1 In `filter.py`'s `_PROMPT_TEMPLATE`, replace the UK-only location rules block with the generalized rule: any specific single country other than Hungary (restriction, bare remote label, or on-site/hybrid presence) → SKIP; multi-region scope and Hungary-inclusion remain not-a-SKIP-basis.
- [x] 1.2 Use illustrative examples covering more than just the UK (e.g. UK, US, Germany, Ireland) so the pattern reads as general rather than UK-specific.

## 2. Update the candidate profile

- [x] 2.1 In `profile.md`'s "Location Preferences" section, replace the UK-specific bullets with the generalized non-Hungary-country rule, keeping the multi-region and Hungary-inclusion exceptions.

## 3. Update the spec

- [x] 3.1 Sync the delta spec in this change into `openspec/specs/location-filtering/spec.md` (via `/opsx:sync` or archive), replacing the UK-only and outside-Hungary/EU requirements with the unified "Non-Hungary country-specific roles are skipped" requirement.

## 4. Verify

- [x] 4.1 Ran `RelevanceFilter.evaluate()` against representative synthetic listings (live Gemini calls, same EM job snippet, location varied): "Remote, Germany" → SKIP, "Remote, UK" → SKIP, "Remote EMEA" → RELEVANT, "Remote UK/EU" → RELEVANT, "Remote, Hungary" → RELEVANT, eligible-country list omitting Hungary → SKIP. All matched expectations.
- [x] 4.2 "Hybrid, Berlin, Germany" → SKIP, confirmed against live Gemini call.
