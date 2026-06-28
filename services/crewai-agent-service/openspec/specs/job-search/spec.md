## Purpose

Periodic Tavily-based LinkedIn job search with title and location pre-filtering, feeding the relevance filter pipeline.

## Requirements

### Requirement: Periodic LinkedIn job search via Tavily
The system SHALL query Tavily search with a fixed set of query templates targeting LinkedIn job listings, on a configurable recurring schedule (default every 4-6 hours). Queries SHALL cover all target role title variants and location variants. Each query SHALL include an `after:<date>` operator computed as today minus `FRESHNESS_MAX_AGE_DAYS` (default 3) to restrict Google's index to recently crawled pages.

#### Scenario: All query variants are executed each run
- **WHEN** the scheduler triggers a search run
- **THEN** the system executes all configured query templates against Tavily and collects results

#### Scenario: Results include URL, title, and snippet
- **WHEN** Tavily returns results for a query
- **THEN** each result SHALL include at minimum: the job page URL, job title, and a text snippet

#### Scenario: Freshness filter applied
- **WHEN** constructing Tavily queries
- **THEN** the system SHALL append `after:<YYYY-MM-DD>` to each query, where the date is today minus `FRESHNESS_MAX_AGE_DAYS`

### Requirement: Title and location pre-filter
The system SHALL apply a metadata-only pre-filter to Tavily results before any LLM calls, discarding results that clearly do not match target titles or locations.

#### Scenario: Title does not match target roles
- **WHEN** a result title contains no variant of Engineering Manager, Senior Engineering Manager, Director of Engineering, Head of Engineering, Team Lead, or Team Leader
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Location does not match
- **WHEN** a result metadata indicates an on-site-only location outside Budapest, or a non-EMEA geography
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Ambiguous location passes pre-filter
- **WHEN** location metadata is absent or ambiguous (e.g. "Remote" with no region)
- **THEN** the result SHALL pass to the LLM filter stage for further evaluation

### Requirement: Snippet-based posting age filter
The system SHALL parse age text from Tavily snippets (e.g. "5 months ago", "Posted 2 weeks ago") and discard results whose parsed age exceeds `FRESHNESS_MAX_AGE_DAYS` (default 3). Results whose snippet contains "no longer accepting applications" SHALL also be discarded.

#### Scenario: Job posted within threshold
- **WHEN** the snippet contains "2 days ago" and `FRESHNESS_MAX_AGE_DAYS` is 3
- **THEN** the result passes the freshness filter

#### Scenario: Job posted beyond threshold
- **WHEN** the snippet contains "2 weeks ago" or "1 month ago"
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Job no longer accepting applications
- **WHEN** the snippet contains "no longer accepting applications"
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: No posting age text in snippet
- **WHEN** the snippet contains no age pattern and no "no longer accepting" text
- **THEN** the result passes the snippet age check and proceeds to the next freshness layer

### Requirement: published_date metadata filter
The system SHALL check the Tavily `published_date` field when present. Results with a `published_date` older than `FRESHNESS_MAX_PUBLISHED_DAYS` (default 7) SHALL be discarded.

#### Scenario: published_date within threshold
- **WHEN** `published_date` is within the last `FRESHNESS_MAX_PUBLISHED_DAYS` days
- **THEN** the result passes this filter

#### Scenario: published_date exceeds threshold
- **WHEN** `published_date` is present and older than `FRESHNESS_MAX_PUBLISHED_DAYS`
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: published_date absent
- **WHEN** the Tavily result has no `published_date` field
- **THEN** this filter is skipped and the result proceeds normally
