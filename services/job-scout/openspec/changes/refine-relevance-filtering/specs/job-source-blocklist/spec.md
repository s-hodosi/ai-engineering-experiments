## ADDED Requirements

### Requirement: Jobs from known low-quality posting sources are excluded before the LLM relevance call
The system SHALL maintain a list of known low-quality/repost-spam poster or company names. Any job whose `company` field matches an entry in this list (case-insensitively) SHALL be excluded before reaching the LLM relevance filter stage — no LLM call SHALL be made for these jobs.

#### Scenario: Job from a blocklisted company is excluded pre-LLM
- **WHEN** a job's `company` field matches an entry in the blocklist
- **THEN** the job is excluded without any call to the relevance filter LLM

#### Scenario: Job from a non-blocklisted company proceeds normally
- **WHEN** a job's `company` field does not match any blocklist entry
- **THEN** the job proceeds to the relevance filter stage as usual

#### Scenario: Blocklist match is case-insensitive
- **WHEN** a job's `company` field matches a blocklist entry differing only in letter case
- **THEN** the job SHALL still be excluded

### Requirement: Blocklisted jobs are still recorded for observability
The system SHALL record blocklisted jobs in the seen-jobs database with verdict SKIP, consistent with how LLM-judged SKIP jobs are recorded, so that blocklist activity remains auditable via the same data used for other job-scout diagnostics.

#### Scenario: Blocklisted job is recorded with SKIP verdict
- **WHEN** a job is excluded by the source blocklist
- **THEN** it is recorded in the seen-jobs table with verdict SKIP, url, title, and company populated, the same as any other SKIP

### Requirement: Blocklist is a maintainable, manually-edited list
The system SHALL store the blocklist in a location that can be extended without modifying application logic (e.g. a config value or a simple list read at startup), so new offending sources can be added as they are identified.

#### Scenario: New offending source added to blocklist
- **WHEN** a new low-quality poster/company name is added to the blocklist
- **THEN** jobs from that source are excluded on the next run, without any code change beyond the list itself
