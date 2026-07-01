## MODIFIED Requirements

### Requirement: LLM relevance judgment against candidate profile
The system SHALL pass each pre-filtered job (title, location, snippet) to a Gemini LLM call along with a candidate profile loaded from `profile.md`. The job's `location` field SHALL be explicitly interpolated into the prompt text sent to the LLM, not merely available on the job object — location-based filtering rules depend on the LLM actually seeing this value. When `location` is empty, the prompt SHALL still be sent, and the LLM falls back to inferring location from the snippet text. The LLM SHALL return a structured verdict: RELEVANT, UNSURE, or SKIP, plus a short explanation paragraph.

#### Scenario: Hard expertise gap detected
- **WHEN** the job snippet hard-requires deep expertise the candidate lacks (e.g. "5+ years TypeScript required", "extensive fintech domain experience required")
- **THEN** the LLM SHALL return verdict SKIP with a reason citing the specific gap

#### Scenario: Strong profile match
- **WHEN** the job description aligns with the candidate's leadership background and no hard disqualifiers exist
- **THEN** the LLM SHALL return verdict RELEVANT with a paragraph describing the alignment

#### Scenario: Ambiguous location or borderline role
- **WHEN** the job is listed for a specific country (e.g. UK) but does not explicitly exclude non-local candidates, or when a Team Lead title may or may not be genuine people management
- **THEN** the LLM SHALL return verdict UNSURE with a paragraph describing what is unclear

#### Scenario: Both technical EM and senior leadership profiles accepted
- **WHEN** a role is more technical/architecture-focused EM
- **THEN** the system SHALL NOT skip it solely due to technical depth — the candidate's IC background is relevant

#### Scenario: Structured location field is used when present
- **WHEN** the job record has a non-empty `location` field (e.g. "Hungary (Remote)") sourced from the alert email
- **THEN** that value SHALL appear in the prompt sent to the LLM, so location-filtering rules are evaluated against it rather than solely against JD snippet text
