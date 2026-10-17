## MODIFIED Requirements

### Requirement: LinkedIn JD page fetching
For each unseen job URL, the system SHALL fetch the LinkedIn job page via the public `jobs-guest/jobs/api/jobPosting/{job_id}` endpoint (no authentication required), extract the job description body text, and attach it to the job record as `snippet`.

The system SHALL inspect the HTTP status code of every response. A fetch attempt that raises a network exception, returns a non-200 status other than 404/410, or returns 200 without a recognisable description element SHALL be treated as a transient failure and retried, up to 3 attempts in total, waiting approximately 3 seconds before the second attempt and 10 seconds before the third. When a response carries a `Retry-After` header expressed in seconds, the system SHALL wait that long instead, capped at 30 seconds. A 404/410 response, or a description element containing fewer than 200 characters, SHALL NOT be retried.

Every failed attempt SHALL be logged with a timestamp, the job ID, the attempt number, the HTTP status (if any), and the failure reason. A job that succeeds only after a retry SHALL produce one recovery log line. When all attempts fail, the system SHALL log a final failure line and save the last response body (when one exists), together with its status code and response headers, to a local debug folder excluded from version control; the folder SHALL retain at most the 50 most recent captures. Failure to write a capture SHALL NOT interrupt the run.

#### Scenario: JD page returns accessible content
- **WHEN** the LinkedIn job page returns ≥ 200 characters of description text
- **THEN** the extracted text is used as the job snippet for the Gemini filter, and no log line is written for that fetch

#### Scenario: Description missing on first attempt but present on retry
- **WHEN** the first attempt returns HTTP 200 without a description element and a subsequent attempt returns ≥ 200 characters of description text
- **THEN** the description from the successful attempt is used as the snippet, and a recovery log line records the job ID and the number of attempts taken

#### Scenario: Transient HTTP error status
- **WHEN** an attempt returns a non-200 status other than 404/410 (e.g. 429, 999, 503)
- **THEN** the attempt is logged with its status code and retried according to the backoff schedule

#### Scenario: Retry-After header present
- **WHEN** a failed response includes `Retry-After: 20`
- **THEN** the system waits 20 seconds before the next attempt; a value above 30 is capped at 30 seconds

#### Scenario: All attempts fail with no description
- **WHEN** all 3 attempts return no description element or a transient error status
- **THEN** the snippet is set to `[limited info — JD not accessible]` (no description element) or `[limited info — fetch failed]` (error status or exception), a final failure line is logged, the last response body is saved to the debug folder, and the job proceeds to the Gemini filter with title, company, and location only

#### Scenario: JD fetch fails with network or HTTP error
- **WHEN** every attempt raises a network exception (e.g. timeout) or returns a transient non-200 status
- **THEN** each failed attempt is logged, the snippet is set to `[limited info — fetch failed]`, the last response body is saved if one was received, and the job proceeds to the Gemini filter

#### Scenario: Posting removed
- **WHEN** the endpoint returns HTTP 404 or 410
- **THEN** the system does not retry, logs the outcome, saves the response body, sets the snippet to `[limited info — JD not accessible]`, and the job proceeds to the Gemini filter

#### Scenario: JD page is gated or returns insufficient content
- **WHEN** the description element is found but contains fewer than 200 characters
- **THEN** the system does not retry, sets the snippet to `[limited info — JD not accessible]`, and the job proceeds to the Gemini filter

#### Scenario: Debug folder retention
- **WHEN** a new failure capture would bring the debug folder above 50 captures
- **THEN** the oldest captures are removed so that at most 50 remain
