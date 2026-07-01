## MODIFIED Requirements

### Requirement: Periodic job search via multiple sources
The system SHALL query both Tavily (LinkedIn-specific, via Google index) and Indeed RSS on a configurable recurring schedule (default every 30 minutes). Results from all sources are merged and passed through deduplication before pre-filtering. Tavily serves as a complementary fallback for LinkedIn-only posts not indexed by Indeed. Each Tavily query SHALL include an `after:<date>` operator computed as today minus `FRESHNESS_MAX_AGE_DAYS` (default 3).

#### Scenario: All sources are queried each run
- **WHEN** the scheduler triggers a search run
- **THEN** the system executes all Tavily query templates and all Indeed RSS queries, collecting results from both

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
