## MODIFIED Requirements

### Requirement: Job listing extraction from alert email HTML
The system SHALL parse the HTML body of each LinkedIn alert email and extract a list of jobs, each containing at minimum: job title, company name, location, and the LinkedIn redirect URL. The extracted `location` SHALL be carried through into the final job record returned by `fetch_jobs()` — it SHALL NOT be dropped between parsing and the record handed to the relevance filter and notifier.

#### Scenario: Alert email contains multiple job listings
- **WHEN** a LinkedIn alert email contains N job cards
- **THEN** the system extracts all N jobs as separate candidate records

#### Scenario: Alert email contains no parseable jobs
- **WHEN** a LinkedIn alert email is found but no job listings can be extracted
- **THEN** the system logs a warning and marks the email as processed to avoid repeated attempts

#### Scenario: Parsed location is present in the returned job record
- **WHEN** a job card's rich-card text yields a non-empty `location` string (e.g. "Hungary (Remote)")
- **THEN** the job record returned by `fetch_jobs()` SHALL include that `location` value under the `location` key, unchanged

#### Scenario: Rich card yields no location
- **WHEN** a job card's rich-card text cannot be split into a location segment
- **THEN** the job record's `location` key SHALL be set to an empty string rather than omitted, so downstream consumers can rely on the key always being present
