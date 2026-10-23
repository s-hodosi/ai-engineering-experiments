# llm-failure-handling Specification

## Purpose
Defines how the service behaves when the relevance-filter LLM call fails. Failures never produce a verdict and never lose a job. Fatal outages stop further spend and are announced with a throttled alert.

## Requirements

### Requirement: LLM failures are classified as fatal or transient
The system SHALL classify every failed relevance-filter call as either fatal or transient.

Fatal failures cannot succeed on retry without user action:
- billing exhausted, e.g. "prepayment credits are depleted" with HTTP 402, or the same message with HTTP 429
- invalid API key
- permission or authentication denied (HTTP 401/403)

All other failures SHALL be classified as transient. This includes rate limits not related to billing, HTTP 5xx, timeouts, connection errors, and unparseable provider responses. Classification SHALL use the provider's status code and error message, not the client library's exception class alone, because the client may wrap a billing error in a generic connection-error type.

#### Scenario: Depleted prepay credits are fatal
- **WHEN** the LLM provider responds with HTTP 402, or with an error message stating prepayment credits are depleted
- **THEN** the failure SHALL be classified as fatal with reason "billing"

#### Scenario: Billing error wrapped as a connection error is still fatal
- **WHEN** the client library raises a connection-error type whose message contains a 402 status or a "prepayment credits are depleted" message
- **THEN** the failure SHALL be classified as fatal with reason "billing"

#### Scenario: Invalid or denied API key is fatal
- **WHEN** the provider responds with HTTP 401 or 403, or an error stating the API key is invalid
- **THEN** the failure SHALL be classified as fatal with reason "auth"

#### Scenario: Ordinary rate limit or server error is transient
- **WHEN** the provider responds with HTTP 429 not related to billing, HTTP 5xx, or the call times out
- **THEN** the failure SHALL be classified as transient

### Requirement: Fatal failure stops LLM calls for the rest of the run
On the first fatal failure in a run, the system SHALL make no further LLM calls in that run. The failed job and every job not yet evaluated SHALL be placed in the pending queue. Jobs that already received a verdict earlier in the run SHALL still be delivered in that run's digest.

#### Scenario: Billing outage mid-run
- **WHEN** a run has 6 jobs to evaluate, jobs 1–2 receive verdicts, and job 3 fails with a fatal error
- **THEN** jobs 3–6 SHALL be placed in the pending queue without further LLM calls, and jobs 1–2 SHALL be handled normally (recorded as seen, and included in the digest if RELEVANT or UNSURE)

### Requirement: Transient failure defers only the affected job
On a transient failure, the system SHALL place the affected job in the pending queue and continue evaluating the remaining jobs in the run.

#### Scenario: One job hits a server error
- **WHEN** one job's LLM call fails with HTTP 503 and other jobs remain in the run
- **THEN** that job SHALL be placed in the pending queue and the remaining jobs SHALL still be evaluated

### Requirement: Pending queue persists deferred jobs across runs
The system SHALL persist each deferred job in a pending queue that survives restarts. Each entry SHALL hold enough data to re-evaluate the job without refetching it from email or LinkedIn: URL, title, company, location, and JD snippet. Each entry SHALL also hold a count of transient-failure attempts. At the start of each run's evaluation stage, the system SHALL evaluate pending jobs before newly fetched jobs. A pending job that receives a verdict SHALL be removed from the queue and handled like any newly evaluated job. A job already in the queue SHALL NOT be duplicated.

#### Scenario: Deferred job is evaluated after the outage ends
- **WHEN** a job was deferred during a billing outage, and on a later run the LLM call succeeds
- **THEN** the job SHALL be evaluated, removed from the pending queue, recorded as seen with its verdict, and included in that run's digest if RELEVANT or UNSURE

#### Scenario: Pending jobs are retried even when there are no new emails
- **WHEN** a run fetches no new jobs but the pending queue is not empty
- **THEN** the run SHALL still evaluate the pending jobs

#### Scenario: Pending queue survives restart
- **WHEN** the service restarts while jobs are pending
- **THEN** those jobs SHALL still be pending after the restart and SHALL be evaluated on the next run

### Requirement: Transient retries are capped per job; fatal outages do not consume attempts
A job's attempt count SHALL increase only when its own LLM call fails transiently. Being deferred because of a fatal failure, whether its own or an earlier job's in the same run, SHALL NOT increase its attempt count. When a job reaches 5 transient attempts, the system SHALL stop retrying it, remove it from the pending queue, and record it as seen with verdict `ERROR`. It SHALL then be included in that run's digest with a fixed, human-readable note in place of the scope summary, stating that it could not be evaluated and should be reviewed manually.

#### Scenario: Persistently failing job is given up
- **WHEN** a job's LLM call has failed transiently on 5 separate attempts
- **THEN** it SHALL be removed from the pending queue, recorded as seen with verdict ERROR, and listed in the digest with the "could not be evaluated — review manually" note

#### Scenario: Multi-day billing outage loses nothing
- **WHEN** the filter fails fatally on every run for several days
- **THEN** no pending job's attempt count SHALL increase, and every pending job SHALL be evaluated once billing is restored

### Requirement: Throttled outage alert email
When a run ends with a fatal failure, the system SHALL send a separate alert email to the notification address. The subject SHALL be `[Job Scout] Filter down: <reason>`. The body SHALL contain a plain-language explanation (e.g. "Gemini prepay credits are depleted — top up in AI Studio"), the number of jobs currently pending, and no raw exception dump. While the outage continues, the system SHALL send at most one alert per 24 hours. After a run that follows a fatal outage completes with no fatal failure, the system SHALL treat the outage as ended. A later fatal failure SHALL then alert immediately.

#### Scenario: First fatal failure sends an alert
- **WHEN** a run hits a fatal billing failure and no alert has been sent for the current outage
- **THEN** one email with subject `[Job Scout] Filter down: billing` SHALL be sent, stating the cause and the pending-job count

#### Scenario: Ongoing outage is not re-alerted every run
- **WHEN** an alert was sent less than 24 hours ago and the outage is still ongoing
- **THEN** no further alert email SHALL be sent in this run

#### Scenario: New outage after recovery alerts immediately
- **WHEN** a previous outage ended (a run completed with no fatal failure) and a new fatal failure occurs
- **THEN** an alert SHALL be sent in that run regardless of when the previous alert was sent
