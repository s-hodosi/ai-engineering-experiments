## ADDED Requirements

### Requirement: LLM relevance judgment against candidate profile
The system SHALL pass each pre-filtered job (title, location, snippet) to a Gemini LLM call along with a candidate profile loaded from `profile.md`. The LLM SHALL return a structured verdict: RELEVANT, UNSURE, or SKIP, plus a short explanation paragraph.

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

### Requirement: Candidate profile loaded from editable file
The system SHALL load the candidate profile from `profile.md` at startup. The file SHALL be plain text and editable without code changes.

#### Scenario: Profile file is read at startup
- **WHEN** the service starts
- **THEN** the content of `profile.md` is loaded into memory and used for all LLM filter calls in that run

#### Scenario: Profile file is missing
- **WHEN** `profile.md` does not exist at startup
- **THEN** the service SHALL fail with a clear error message indicating the missing file

### Requirement: UNSURE and RELEVANT verdicts both trigger notification
The system SHALL treat both RELEVANT and UNSURE as notification-worthy. SKIP verdicts SHALL be silently discarded.

#### Scenario: RELEVANT job triggers email
- **WHEN** the LLM returns RELEVANT
- **THEN** the job is passed to the notification stage

#### Scenario: UNSURE job triggers email
- **WHEN** the LLM returns UNSURE
- **THEN** the job is passed to the notification stage with the UNSURE verdict visible in the email

#### Scenario: SKIP job is discarded
- **WHEN** the LLM returns SKIP
- **THEN** the job is marked as seen in the database and no email is sent
