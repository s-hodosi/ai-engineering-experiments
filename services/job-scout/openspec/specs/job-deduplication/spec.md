## Purpose

SQLite-backed seen-job tracking to prevent re-notification of already-processed job URLs across service restarts.

## Requirements

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

### Requirement: Email-level deduplication via processed_emails table
The system SHALL maintain a `processed_emails` table in the SQLite database, storing the `Message-ID` of each processed LinkedIn alert email. On each poll, emails whose `Message-ID` is already in this table SHALL be skipped. This deduplication is independent of the IMAP read/unread flag, so the user may read the email in Gmail without affecting the bot's processing state.

#### Scenario: First time an alert email is processed
- **WHEN** a LinkedIn alert email is processed for the first time
- **THEN** its Message-ID is inserted into processed_emails after all its jobs have been evaluated

#### Scenario: Same alert email encountered on subsequent poll
- **WHEN** a LinkedIn alert email's Message-ID is already in processed_emails
- **THEN** the email and all its jobs are skipped without any HTTP or LLM calls

#### Scenario: Database persists across restarts
- **WHEN** the service restarts
- **THEN** previously processed email Message-IDs remain in the database and those emails are not re-processed
