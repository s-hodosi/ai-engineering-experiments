## Context

`location-filtering` is enforced entirely through natural-language rules fed to Gemini in `filter.py`'s `_PROMPT_TEMPLATE` and mirrored in `profile.md`'s "Location Preferences" section — there is no regex or country-list code. The current rules (added in commit `520ba6d`) only spell out UK-specific phrasing, because UK-based remote EM roles were the immediate noise source at the time. The gap: any other single country (Germany, US, Ireland, etc.) named as the required location isn't caught, so the candidate gets notified about roles they're not eligible for.

## Goals / Non-Goals

**Goals:**
- Generalize the country-restriction rule so it applies to any country other than Hungary, not just the UK.
- Collapse the current UK-only "hard restriction → SKIP" / "bare label → UNSURE" split into one SKIP outcome, since the candidate has decided the ambiguity isn't worth an email.
- Keep the multi-region exception (Remote UK/EU, EMEA, Europe, global) and the "Hungary mentioned anywhere" exception unchanged.

**Non-Goals:**
- No country-name enumeration, regex, or lookup table — this stays a semantic LLM rule. Gemini already recognizes country names and demonyms; the prompt just needs to stop special-casing the UK.
- No change to how location text is extracted or passed through (`linkedin_email_source.py`, `db.py`, `notifier.py` are untouched).
- No change to non-location filtering behavior (role fit, language, domain disqualifiers).

## Decisions

**Collapse UNSURE into SKIP for bare single-country remote labels.** Today "Remote, UK" with no explicit restriction returns UNSURE, reasoning the company might hire internationally. The candidate explicitly chose to skip these outright rather than take that chance across every possible country — false negatives (missing an internationally-friendly role) are an accepted cost of not receiving noise. Alternative considered: keep UNSURE for bare labels and only SKIP on explicit restriction language. Rejected per user's explicit instruction — "if it is Remote, UK or Remote, Germany or similar, just skip."

**Keep examples illustrative, not exhaustive.** The rule will list a handful of countries (UK, US, Germany, Ireland) as examples of the pattern, the same way the current rule lists UK-only phrasings as examples. This relies on Gemini's semantic understanding of "specific country" rather than an enumerated list, so no maintenance burden when new countries show up in job postings.

**Tighten on-site/hybrid scope from "outside Hungary/EU" to "outside Hungary".** Previously a hybrid role in, say, Berlin was allowed through as "EU, therefore fine" under the old Requirement 3. Under the new unified rule, naming any specific non-Hungary country — EU or not — as the required physical location is a SKIP. This makes the on-site/hybrid rule consistent with the remote-label rule instead of carving out a special EU exception.

**Multi-region and Hungary-inclusion exceptions are untouched.** These already work correctly and weren't part of the reported gap; changing them wasn't in scope of this ask (confirmed with user during exploration).

## Risks / Trade-offs

- **[Risk]** Broader SKIP criteria may cause a genuinely viable role to be silently skipped (e.g., a company that would sponsor relocation or hire remote-anywhere but phrased the listing as "Remote, Germany" for payroll reasons) → **Mitigation**: none needed — this is the explicitly accepted trade-off (fewer notifications, zero non-Hungary noise). If it proves too aggressive in practice, the candidate can revisit via a future change.
- **[Risk]** LLM inconsistency: Gemini may not reliably treat "Remote, Germany" identically to "Remote, UK" since only a few example countries are spelled out in the prompt → **Mitigation**: phrase the rule as a general principle first ("any specific country other than Hungary"), with examples clearly marked as illustrative ("e.g., ...") rather than the sole trigger list — this is the same pattern already validated by the existing UK-only rule.

## Migration Plan

Prompt/spec wording change only; no data migration. Deploy by editing `filter.py`, `profile.md`, and the spec in one commit. No rollback complexity — revert the wording if it over-skips in practice.

## Open Questions

None outstanding — scope was clarified with the user during exploration (multi-region exception unchanged; bare single-country labels now SKIP instead of UNSURE; on-site/hybrid scope narrowed to Hungary-only).
