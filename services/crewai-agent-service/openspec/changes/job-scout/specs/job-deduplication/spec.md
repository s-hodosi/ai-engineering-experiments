## ADDED Requirements

### Requirement: SQLite-backed job deduplication by URL
The system SHALL maintain a SQLite database of seen job URLs. Any job whose URL is already in the database SHALL be skipped before the LLM filter stage, regardless of verdict.

#### Scenario: New job URL is processed
- **WHEN** a job URL has not been seen before
- **THEN** the job proceeds through the LLM filter and the URL is recorded in the database regardless of verdict

#### Scenario: Previously seen job URL is skipped
- **WHEN** a job URL already exists in the seen-jobs table
- **THEN** the job is immediately discarded without an LLM call or email

#### Scenario: Database persists across restarts
- **WHEN** the service restarts
- **THEN** previously seen job URLs remain in the database and are not re-processed

### Requirement: Seen-jobs table records verdict and timestamp
The system SHALL store the verdict (RELEVANT, UNSURE, SKIP) and the timestamp of first encounter alongside each seen URL.

#### Scenario: Job recorded with metadata
- **WHEN** a job is processed for the first time
- **THEN** the database record includes: url, title, company (if available), verdict, and fetched_at timestamp
