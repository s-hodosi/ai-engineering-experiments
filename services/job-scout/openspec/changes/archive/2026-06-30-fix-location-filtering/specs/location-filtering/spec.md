## ADDED Requirements

### Requirement: UK-only remote roles are skipped
The filter SHALL return SKIP for any role whose job description explicitly restricts the position to candidates based in the UK, regardless of whether the role is otherwise remote.

Explicit restriction patterns include (but are not limited to):
- "for those based in the UK"
- "must be based in the UK"
- "must be a UK resident"
- "right to work in the UK required" (without EU/international sponsorship mention)

#### Scenario: JD opens with UK-only restriction phrase
- **WHEN** the job description contains "for those based in the UK" or equivalent
- **THEN** the filter SHALL return SKIP

#### Scenario: JD says "Remote, UK" with no further restriction language
- **WHEN** the job description lists location as "Remote, UK" but contains no explicit residency or right-to-work restriction
- **THEN** the filter SHALL return UNSURE (company may hire internationally; not confirmed UK-only)

### Requirement: Multi-region remote roles including EU are treated as relevant on location
The filter SHALL treat a role as location-eligible (not skipped on geographic grounds) when the job description indicates a multi-region remote scope that includes the EU or EMEA.

Eligible patterns include:
- "Remote UK/EU"
- "Remote EMEA"
- "Remote Europe"
- "Remote globally"

#### Scenario: JD lists UK/EU remote scope
- **WHEN** the job description specifies "Remote UK/EU" or "Remote EMEA" or similar multi-region scope including Europe
- **THEN** location SHALL NOT be a basis for SKIP; verdict is determined by role fit

#### Scenario: JD lists global remote
- **WHEN** the job description specifies "Remote (global)" or "Fully remote" without geographic restriction
- **THEN** location SHALL NOT be a basis for SKIP

### Requirement: Candidate location and relocation preference are encoded in filtering rules
The filter SHALL treat the candidate as located in Hungary, EU, and not open to relocation. Any role requiring physical presence or residency outside Hungary/EU SHALL be returned as SKIP.

#### Scenario: Role requires on-site or hybrid in non-EMEA city
- **WHEN** the job description requires physical presence in a location outside Hungary or EU (e.g. "on-site in London required", "hybrid in San Francisco")
- **THEN** the filter SHALL return SKIP
