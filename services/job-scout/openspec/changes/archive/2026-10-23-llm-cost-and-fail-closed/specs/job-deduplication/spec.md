## MODIFIED Requirements

### Requirement: SQLite-backed job deduplication by URL
The system SHALL maintain a SQLite database of seen job URLs. Any job whose URL is already in the database SHALL be skipped before the LLM filter stage, regardless of verdict. A job SHALL be recorded as seen only once its processing is final: it received an LLM verdict, it was blocklisted, or it was given up after the transient-retry cap. A job whose LLM evaluation failed SHALL NOT be recorded as seen. It is held in the pending queue instead (see `llm-failure-handling`). A URL present in the pending queue SHALL also be skipped when encountered again in a newly fetched alert email, so it is not evaluated twice.

#### Scenario: New job URL is processed
- **WHEN** a job URL has not been seen before and its LLM evaluation succeeds
- **THEN** the job proceeds through the LLM filter and the URL is recorded in the database with its verdict

#### Scenario: Failed evaluation is not recorded as seen
- **WHEN** a job's LLM evaluation fails
- **THEN** the URL SHALL NOT be recorded in the seen-jobs table, and the job SHALL be held in the pending queue

#### Scenario: Pending job reappears in a new alert email
- **WHEN** a newly fetched alert email lists a job whose URL is already in the pending queue
- **THEN** the job SHALL NOT be added again, and its JD SHALL NOT be refetched

#### Scenario: Previously seen job URL is skipped
- **WHEN** a job URL already exists in the seen-jobs table
- **THEN** the job is immediately discarded without an LLM call or email

#### Scenario: Database persists across restarts
- **WHEN** the service restarts
- **THEN** previously seen job URLs remain in the database and are not re-processed

### Requirement: Seen-jobs table records verdict and timestamp
The system SHALL store the verdict (RELEVANT, UNSURE, SKIP, or ERROR for jobs given up after the retry cap) and the timestamp of recording alongside each seen URL.

#### Scenario: Job recorded with metadata
- **WHEN** a job's processing becomes final
- **THEN** the database record includes: url, title, company (if available), verdict, and fetched_at timestamp
