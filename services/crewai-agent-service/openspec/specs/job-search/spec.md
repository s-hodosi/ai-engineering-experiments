## Purpose

Periodic Tavily-based LinkedIn job search with title and location pre-filtering, feeding the relevance filter pipeline.

## Requirements

### Requirement: Periodic LinkedIn job search via Tavily
The system SHALL query Tavily search with a fixed set of query templates targeting LinkedIn job listings, on a configurable recurring schedule (default every 4-6 hours). Queries SHALL cover all target role title variants and location variants.

#### Scenario: All query variants are executed each run
- **WHEN** the scheduler triggers a search run
- **THEN** the system executes all configured query templates against Tavily and collects results

#### Scenario: Results include URL, title, and snippet
- **WHEN** Tavily returns results for a query
- **THEN** each result SHALL include at minimum: the job page URL, job title, and a text snippet

#### Scenario: Freshness filter applied
- **WHEN** constructing Tavily queries
- **THEN** the system SHALL apply a recency filter (e.g. days=2) to limit results to recently indexed listings

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
