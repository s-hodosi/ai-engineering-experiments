## Purpose

Adzuna API-based job search across 7 EU countries, providing 1–3 hour freshness as a parallel source alongside Tavily.

## Requirements

### Requirement: Adzuna API job search
The system SHALL query the Adzuna Jobs API for each configured role-title variant across a fixed set of EU countries (GB, AT, DE, FR, IT, NL, PL), using `sort_by=date` and `max_days_old=FRESHNESS_MAX_AGE_DAYS`. Results from all country/role combinations SHALL be merged and deduplicated by URL before passing to the pre-filter.

#### Scenario: All role-title and country combinations are queried each run
- **WHEN** the scheduler triggers a search run
- **THEN** the system executes all configured Adzuna queries across all role variants and supported EU countries, collecting results from each

#### Scenario: EU-wide location coverage without EMEA keywords
- **WHEN** a job is posted in any Adzuna-supported EU country or UK
- **THEN** it is included in results regardless of whether EMEA, Europe, or regional keywords appear in the job description

#### Scenario: Results include required fields
- **WHEN** Adzuna returns a job result
- **THEN** each result SHALL include at minimum: the job page redirect URL, job title, company name, created date, and description snippet

#### Scenario: Duplicate URLs across queries are deduplicated
- **WHEN** the same job URL appears in results from multiple role/country queries
- **THEN** only one instance is passed to the pre-filter

#### Scenario: Missing credentials skips Adzuna gracefully
- **WHEN** `ADZUNA_APP_ID` or `ADZUNA_APP_KEY` is not set
- **THEN** the Adzuna source is skipped with a warning and Tavily results are used alone

### Requirement: created-date-based freshness filter
The system SHALL use the Adzuna `created` field to discard jobs older than `FRESHNESS_MAX_AGE_DAYS` (default 3). The `created` field from the Adzuna API reliably reflects the actual posting date.

#### Scenario: Job within freshness threshold passes
- **WHEN** the `created` date of an Adzuna result is within the last `FRESHNESS_MAX_AGE_DAYS` days
- **THEN** the result passes the freshness filter

#### Scenario: Job beyond freshness threshold is discarded
- **WHEN** the `created` date of an Adzuna result is older than `FRESHNESS_MAX_AGE_DAYS` days
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Missing created date passes through
- **WHEN** an Adzuna result has no parseable `created` field
- **THEN** the result passes the freshness check and proceeds to the title pre-filter
