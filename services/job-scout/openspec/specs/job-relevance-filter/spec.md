## Purpose

LLM-based relevance judgment (RELEVANT/UNSURE/SKIP) against a candidate profile, determining which jobs warrant email notification.

## Requirements

### Requirement: LLM relevance judgment against candidate profile
The system SHALL pass each pre-filtered job (title, location, snippet) to a Gemini LLM call along with a candidate profile loaded from `profile.md`. The job's `location` field SHALL be explicitly interpolated into the prompt text sent to the LLM, not merely available on the job object — location-based filtering rules depend on the LLM actually seeing this value. When `location` is empty, the prompt SHALL still be sent, and the LLM falls back to inferring location from the snippet text. The LLM SHALL return a structured verdict: RELEVANT, UNSURE, or SKIP, plus a short explanation paragraph. The target role scope is Senior Engineering Manager and above, capped at VP Engineering (see the senior-leadership-scope requirement) — plain Engineering Manager and Team Leader/Team Lead titles no longer qualify on their own.

#### Scenario: Hard expertise gap detected
- **WHEN** the job snippet hard-requires deep expertise the candidate lacks (e.g. "5+ years TypeScript required", "extensive fintech domain experience required")
- **THEN** the LLM SHALL return verdict SKIP with a reason citing the specific gap

#### Scenario: Strong profile match
- **WHEN** the job description aligns with the candidate's leadership background, meets the senior-leadership-scope bar, and no hard disqualifiers exist
- **THEN** the LLM SHALL return verdict RELEVANT with a paragraph describing the alignment

#### Scenario: Ambiguous location or insufficient scope signal
- **WHEN** the job is listed for a specific country but does not explicitly exclude non-local candidates, or when the JD does not contain enough information to judge whether the role meets the senior-leadership-scope bar
- **THEN** the LLM SHALL return verdict UNSURE with a paragraph describing what is unclear

#### Scenario: Both technical EM and senior leadership profiles accepted
- **WHEN** a role is more technical/architecture-focused EM at or above the senior-leadership-scope bar
- **THEN** the system SHALL NOT skip it solely due to technical depth — the candidate's IC background is relevant

#### Scenario: Structured location field is used when present
- **WHEN** the job record has a non-empty `location` field (e.g. "Hungary (Remote)") sourced from the alert email
- **THEN** that value SHALL appear in the prompt sent to the LLM, so location-filtering rules are evaluated against it rather than solely against JD snippet text

### Requirement: Senior-leadership-scope target range, judged by organizational scope not title
The system SHALL target only Senior Engineering Manager, Director of Engineering, Head of Engineering, and VP Engineering roles (or equivalent), capped at VP Engineering — CTO and other Chief-level titles are excluded as out of scope. Plain "Engineering Manager" and "Team Leader"/"Team Lead" titles SHALL be treated as SKIP by default. Whether a role meets this bar SHALL be judged primarily by the organizational scope described in the job description — not by title string alone — since titles are known to both overstate and understate actual seniority.

Scope signals indicating the role meets the bar include: managing other managers, owning multiple teams or a department, reporting to a VP/CTO/C-level position, or an explicit Director/Head/VP/Principal-equivalent title. This bar SHALL be interpreted against the candidate's own demonstrated scope (managing managers, 55-95 person department) as a practical anchor.

#### Scenario: Plain-titled role with senior scope is not skipped on title alone
- **WHEN** a job is titled plainly "Engineering Manager" but the JD describes managing other managers, owning a department, or reporting to a VP/C-level position
- **THEN** the role SHALL NOT be skipped solely for lacking a "Senior"/"Director"/"Head"/"VP" title

#### Scenario: Senior-sounding title without senior scope is skipped
- **WHEN** a job is titled "Senior Engineering Manager" or similar but the JD describes a single-team, first-line management scope with no evidence of managing managers or department-level ownership
- **THEN** the role SHALL be treated as below the target bar and skipped

#### Scenario: Plain Engineering Manager or Team Lead with no senior scope signal is skipped
- **WHEN** a job is titled "Engineering Manager" or "Team Leader"/"Team Lead" and the JD contains no scope signal indicating it exceeds standard first-line management
- **THEN** the LLM SHALL return verdict SKIP

#### Scenario: CTO and Chief-level titles are skipped
- **WHEN** a job title is "Chief Technology Officer," "Chief Engineering Officer," or an equivalent Chief-level title
- **THEN** the LLM SHALL return verdict SKIP regardless of otherwise-matching organizational scope

#### Scenario: Insufficient scope signal defaults to UNSURE, not SKIP
- **WHEN** the JD snippet is thin, truncated, or fetch-failed (e.g. "[limited info — JD not accessible]") such that organizational scope cannot be determined either way
- **THEN** the LLM SHALL return verdict UNSURE rather than defaulting to SKIP

### Requirement: Pure individual-contributor roles are disqualified regardless of technical fit
The system SHALL return SKIP for roles that are purely individual-contributor in nature — with no people-management scope — even when the role is a strong technical match to the candidate's background.

#### Scenario: Staff/Principal engineer title with no management scope
- **WHEN** a job is titled "Staff Software Engineer," "Principal Software Engineer," "Architect," or similar, and the JD does not describe any people-management responsibility
- **THEN** the LLM SHALL return verdict SKIP, even if the technical domain (e.g. C++, systems programming) matches the candidate's background

#### Scenario: Founding/early engineer hire framed as hands-on IC
- **WHEN** a job is titled "Founding Engineer" or similar and the JD describes a hands-on individual-contributor hire rather than a management role
- **THEN** the LLM SHALL return verdict SKIP

### Requirement: Leadership roles outside the software engineering organization are disqualified
The system SHALL return SKIP for leadership roles (regardless of "Head of," "Director," or "Manager" in the title) that lead a function other than the software engineering/development organization, unless the job description explicitly describes leading a software engineering or development team.

Out-of-scope functions include: Quality Assurance/Testing-only leadership, Security-only leadership, Data/Analytics-only leadership, Program/PMO management, Governance/Risk/Compliance leadership, general business Consulting leadership, Talent/Learning & Development leadership, and general "General Manager"/Operations leadership without explicit engineering scope.

#### Scenario: QA, Security, Data, or PMO leadership title
- **WHEN** a job is titled "Head of Quality Assurance," "Senior Manager – Application Security," "IT PMO Leader," "Group Data Director," or similar, and the JD does not describe leading a software engineering/development team
- **THEN** the LLM SHALL return verdict SKIP

#### Scenario: Engineering-adjacent title that is actually core engineering is not skipped
- **WHEN** a job is titled "Head of Platform Engineering," "Director of SRE," or similar, and the JD describes leading a software engineering/development team
- **THEN** this requirement SHALL NOT be a basis for SKIP — the role is evaluated on its other merits

#### Scenario: Consulting, Governance/Risk, or Talent leadership title
- **WHEN** a job is titled around consulting leadership, governance/risk/compliance leadership, or talent/L&D leadership, and the JD does not describe leading a software engineering/development team
- **THEN** the LLM SHALL return verdict SKIP

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
