## ADDED Requirements

### Requirement: Relevance-filter calls run with a capped reasoning budget
The system SHALL make relevance-filter LLM calls with the model's internal reasoning ("thinking") capped at a low budget of at most 1024 tokens, not the model's unbounded default. Thinking tokens are billed as output, so this keeps per-call cost low on a prepaid billing plan. Reasoning SHALL NOT be disabled entirely: a 30-job comparison showed that with zero thinking the model failed to apply the senior-leadership-scope rules. It matched the service's prior verdicts on only 19/30 jobs, wrongly passing plain-titled Engineering Manager roles.

#### Scenario: Filter call requests a capped thinking budget
- **WHEN** a job is sent to the LLM for relevance evaluation
- **THEN** the request SHALL specify a thinking budget of at most 1024 tokens

#### Scenario: Output format is unchanged with capped thinking
- **WHEN** the LLM responds to a filter call with capped reasoning
- **THEN** the response SHALL still be parsed into a RELEVANT/UNSURE/SKIP verdict and a scope summary, exactly as before

### Requirement: A failed LLM call yields no verdict
When the relevance-filter LLM call fails, the system SHALL NOT substitute a fallback verdict (such as UNSURE) for the job. The failure SHALL be reported as "no verdict", together with its classification (see the `llm-failure-handling` capability). Exception text SHALL NOT be used as the job's scope summary.

#### Scenario: Provider error does not become UNSURE
- **WHEN** the LLM call for a job fails with any error
- **THEN** the job SHALL receive no verdict, SHALL NOT be passed to the notification stage as UNSURE, and its scope summary SHALL NOT contain the error message

## MODIFIED Requirements

### Requirement: UNSURE and RELEVANT verdicts both trigger notification
The system SHALL treat both RELEVANT and UNSURE as notification-worthy. SKIP verdicts SHALL be silently discarded. Jobs that received no verdict because the LLM call failed are neither notified nor discarded. They are deferred per the `llm-failure-handling` capability.

#### Scenario: RELEVANT job triggers email
- **WHEN** the LLM returns RELEVANT
- **THEN** the job is passed to the notification stage

#### Scenario: UNSURE job triggers email
- **WHEN** the LLM returns UNSURE
- **THEN** the job is passed to the notification stage with the UNSURE verdict visible in the email

#### Scenario: SKIP job is discarded
- **WHEN** the LLM returns SKIP
- **THEN** the job is marked as seen in the database and no email is sent

#### Scenario: Failed evaluation is deferred, not notified
- **WHEN** the LLM call for a job fails
- **THEN** the job SHALL NOT be passed to the notification stage and SHALL be deferred for re-evaluation
