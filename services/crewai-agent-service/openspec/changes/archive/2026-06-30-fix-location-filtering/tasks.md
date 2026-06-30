## 1. Update candidate profile location rules

- [x] 1.1 In `services/job-scout/profile.md`, replace the existing "Remote, UK" UNSURE line with two explicit rules: UK-only remote → SKIP, multi-region EU/EMEA remote → RELEVANT
- [x] 1.2 Add a line stating candidate is in Hungary, EU, and not open to relocation

## 2. Update filter prompt rules

- [x] 2.1 In `services/job-scout/filter.py`, add an explicit location rule to `_PROMPT_TEMPLATE` Rules section: UK-only restricted roles (e.g. "for those based in the UK", "must be UK resident", "right to work in UK") → SKIP
- [x] 2.2 Add complementary rule: multi-region remote including EU (UK/EU, EMEA, Europe, global) → location is not a basis for SKIP

## 3. Verify

- [x] 3.1 Manually trace the failing JD ("for those based in the UK") through the updated prompt and confirm verdict would be SKIP
