## ADDED Requirements

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
