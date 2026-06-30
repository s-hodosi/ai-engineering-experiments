## Why

The job relevance filter incorrectly marks UK-only remote roles as RELEVANT. A JD opening with "for those based in the UK" was passed through because the location rule in `profile.md` used a double-negative ("include as UNSURE if not explicitly restricted"), and the filter prompt gave no explicit SKIP guidance for geographic restrictions.

## What Changes

- Replace the ambiguous double-negative location rule in `profile.md` with two clear, positive rules: UK-only remote → SKIP; multi-region remote including EU → RELEVANT
- Add an explicit geographic restriction rule to the filter prompt in `filter.py` so the LLM has an unambiguous instruction at decision time

## Capabilities

### New Capabilities

- `location-filtering`: Explicit logic to classify job postings by geographic scope — single-country UK-only remote as SKIP, multi-region EU/EMEA remote as RELEVANT

### Modified Capabilities

(none — no existing spec files)

## Impact

- `services/job-scout/profile.md`: Location Preferences section rewritten
- `services/job-scout/filter.py`: Rules section in `_PROMPT_TEMPLATE` extended with location rule
