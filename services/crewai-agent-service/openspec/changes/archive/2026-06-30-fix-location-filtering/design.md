## Context

The job-scout pipeline filters job postings through an LLM (`gemini-2.5-flash`) using a prompt built from two sources: a candidate `profile.md` (who the candidate is and what they want) and a rules section in `filter.py` (how to map observations to RELEVANT/UNSURE/SKIP verdicts).

The current location rule in `profile.md` reads:
> "Roles listed as 'Remote, UK' or similar single-country remote: include as UNSURE if the job description does not explicitly restrict to local residents"

This is a double-negative. The intended contrapositive (explicitly restricts → SKIP) is never stated, and the LLM failed to derive it — returning RELEVANT for a JD that opened with "for those based in the UK."

## Goals / Non-Goals

**Goals:**
- UK-only remote roles (explicit "based in UK", "must be UK resident", "right to work in UK") → SKIP
- Multi-region remote including EU (UK/EU, EMEA, Europe) → RELEVANT on location
- Candidate is in Hungary, EU; not open to relocation — encoded as positive rules in both files

**Non-Goals:**
- Handling visa sponsorship nuances (separate concern)
- Changing any other filtering logic (role type, seniority, domain)

## Decisions

**Decision: Fix both `profile.md` and `filter.py`, not just one**

Both files contribute to the LLM's decision. `profile.md` establishes candidate intent; `filter.py`'s Rules section is the direct decision rubric the LLM follows. Fixing only the profile risks the LLM still leaning toward UNSURE under the "when in doubt" bias. Fixing both provides redundant, unambiguous signal.

Alternatives considered:
- Fix only `profile.md`: insufficient — the Rules section in `filter.py` still lists "location restriction" as an UNSURE example, which anchors the LLM toward UNSURE rather than SKIP.
- Fix only `filter.py`: leaves the profile document internally inconsistent, and a future prompt rewrite could re-introduce the bug.

**Decision: Use positive, concrete language ("for those based in", "must be UK resident") rather than abstract ("geographic restriction")**

LLMs respond more reliably to pattern-matched phrasing that mirrors actual JD language. The failing JD used "for those based in the UK" — including that exact phrase reduces ambiguity.

## Risks / Trade-offs

- [False negatives] A JD could use subtle UK-restriction language not covered by the listed phrases → Mitigation: the listed phrases cover the most common patterns; UNSURE remains available for ambiguous cases.
- [Over-eager SKIP] "Remote UK/EU" with a later sentence saying "preference for UK candidates" → Mitigation: the rule keys on explicit restriction language, not soft preferences; soft preferences should surface as UNSURE, not SKIP.
