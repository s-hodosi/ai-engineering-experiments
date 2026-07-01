## ADDED Requirements

### Requirement: Gmail IMAP reading of LinkedIn job alert emails
The system SHALL connect to Gmail via IMAP (port 993) using the configured `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD`, search for LinkedIn job alert emails received within the last 7 days, and skip any whose `Message-ID` is already recorded in the `processed_emails` table. After processing, each email's `Message-ID` SHALL be inserted into `processed_emails`.

#### Scenario: Unread and unprocessed alert email is found
- **WHEN** a LinkedIn job alert email is present in Gmail and its Message-ID is not in processed_emails
- **THEN** the system parses it, processes its jobs, and records the Message-ID

#### Scenario: Already-processed alert email is skipped
- **WHEN** a LinkedIn job alert email's Message-ID is already in the processed_emails table
- **THEN** the email is skipped entirely without re-parsing or re-processing

#### Scenario: User has read the email before the bot runs
- **WHEN** the user has opened and read the LinkedIn alert email in Gmail (marking it as read)
- **THEN** the bot still processes it on the next poll, because processing state is tracked in DB, not by IMAP read/unread flag

#### Scenario: No new alert emails since last poll
- **WHEN** IMAP search returns no unprocessed LinkedIn alert emails
- **THEN** the system exits immediately with no further action

### Requirement: Job listing extraction from alert email HTML
The system SHALL parse the HTML body of each LinkedIn alert email and extract a list of jobs, each containing at minimum: job title, company name, location, and the LinkedIn redirect URL.

#### Scenario: Alert email contains multiple job listings
- **WHEN** a LinkedIn alert email contains N job cards
- **THEN** the system extracts all N jobs as separate candidate records

#### Scenario: Alert email contains no parseable jobs
- **WHEN** a LinkedIn alert email is found but no job listings can be extracted
- **THEN** the system logs a warning and marks the email as processed to avoid repeated attempts

### Requirement: LinkedIn JD page fetching
For each unseen job URL, the system SHALL fetch the LinkedIn job page using HTTP with browser-realistic headers, extract the job description body text, and attach it to the job record as `snippet`. The fetch SHALL follow redirects from the email's tracking URL to the canonical `linkedin.com/jobs/view/` URL.

#### Scenario: JD page returns accessible content
- **WHEN** the LinkedIn job page returns ≥ 200 characters of description text
- **THEN** the extracted text is used as the job snippet for the Gemini filter

#### Scenario: JD page is gated or returns insufficient content
- **WHEN** the LinkedIn job page returns < 200 characters (login wall or empty)
- **THEN** the snippet is set to `[limited info — JD not accessible]` and the job proceeds to the Gemini filter with title, company, and location only

#### Scenario: JD fetch fails with network or HTTP error
- **WHEN** the HTTP request raises an exception or returns a non-200 status
- **THEN** the snippet is set to `[limited info — fetch failed]` and the job proceeds to the Gemini filter

### Requirement: JD fetch deferred until after URL deduplication
The system SHALL check whether a job URL is already in `seen_jobs` BEFORE fetching its JD page. HTTP requests SHALL only be made for URLs not yet in the database.

#### Scenario: Job URL already seen
- **WHEN** a job URL extracted from the email is already in seen_jobs
- **THEN** no HTTP fetch is attempted and the job is discarded

#### Scenario: Job URL not yet seen
- **WHEN** a job URL is not in seen_jobs
- **THEN** the JD fetch is performed and the job proceeds to the Gemini filter
