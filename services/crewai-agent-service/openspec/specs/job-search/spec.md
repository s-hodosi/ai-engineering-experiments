## Purpose

Multi-source job search (Tavily + Adzuna) with title pre-filtering, feeding the relevance filter pipeline.

## Requirements

### Requirement: Periodic job search via multiple sources
The system SHALL query both Tavily (LinkedIn-specific, via Google index) and Adzuna API on a configurable recurring schedule (default every 30 minutes). Results from all sources are merged and passed through deduplication before pre-filtering. Tavily serves as a complementary fallback for LinkedIn-only posts not indexed by Adzuna. Each Tavily query SHALL include an `after:<date>` operator computed as today minus `FRESHNESS_MAX_AGE_DAYS` (default 3).

#### Scenario: All sources are queried each run
- **WHEN** the scheduler triggers a search run
- **THEN** the system executes all Tavily query templates and all Adzuna API queries, collecting results from both

#### Scenario: Results from all sources are merged before deduplication
- **WHEN** both sources return results
- **THEN** the system merges all results and deduplicates by URL before applying the pre-filter

#### Scenario: Schedule interval is configurable in minutes
- **WHEN** `SCHEDULE_INTERVAL_MINUTES` is set in config
- **THEN** the scheduler runs at that interval (default 30 minutes)

#### Scenario: Freshness filter applied to Tavily queries
- **WHEN** constructing Tavily queries
- **THEN** the system SHALL append `after:<YYYY-MM-DD>` to each query, where the date is today minus `FRESHNESS_MAX_AGE_DAYS`

### Requirement: Title pre-filter
The system SHALL apply a title-only metadata pre-filter to all job results before any LLM calls, discarding results whose title contains no variant of the target role titles. Location judgment is delegated entirely to the LLM filter.

#### Scenario: Title does not match target roles
- **WHEN** a result title contains no variant of Engineering Manager, Senior Engineering Manager, Director of Engineering, Head of Engineering, Team Lead, or Team Leader
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Title matches — result proceeds regardless of location keywords
- **WHEN** a result title matches a target role variant
- **THEN** the result proceeds to the LLM filter regardless of whether location keywords (EMEA, Europe, etc.) appear in the metadata

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
