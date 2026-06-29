## ADDED Requirements

### Requirement: Indeed RSS job search
The system SHALL query Indeed RSS feeds for each configured role-title variant, combining `l=Europe` and `l=Budapest` location parameters with `fromage=1` (last 24 hours) and `sort=date`. Results from all queries SHALL be merged and deduplicated by URL before passing to the pre-filter.

#### Scenario: All role-title queries are executed each run
- **WHEN** the scheduler triggers a search run
- **THEN** the system executes all configured Indeed RSS queries and collects results across all role variants

#### Scenario: Europe-wide location coverage
- **WHEN** a job is posted in any EU country, UK, or listed as globally remote
- **THEN** the `l=Europe` location parameter ensures it is included in results without requiring EMEA keywords in the job description

#### Scenario: Results include required fields
- **WHEN** Indeed returns an RSS item
- **THEN** each result SHALL include at minimum: the job page URL, job title, company name, pubDate, and description snippet

#### Scenario: Duplicate URLs across queries are deduplicated
- **WHEN** the same job URL appears in results from multiple role-title queries
- **THEN** only one instance is passed to the pre-filter

### Requirement: pubDate-based freshness filter
The system SHALL use the RSS `pubDate` field to discard jobs older than `FRESHNESS_MAX_AGE_DAYS` (default 3). The `pubDate` field from Indeed RSS reliably reflects the actual posting date, unlike Tavily's `published_date` which is often absent for LinkedIn results.

#### Scenario: Job within freshness threshold passes
- **WHEN** the `pubDate` of an Indeed result is within the last `FRESHNESS_MAX_AGE_DAYS` days
- **THEN** the result passes the freshness filter

#### Scenario: Job beyond freshness threshold is discarded
- **WHEN** the `pubDate` of an Indeed result is older than `FRESHNESS_MAX_AGE_DAYS` days
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Missing pubDate passes through
- **WHEN** an Indeed RSS item has no parseable `pubDate`
- **THEN** the result passes the freshness check and proceeds to the title pre-filter

### Requirement: Individual job URL filter for Indeed
The system SHALL discard Indeed results whose URL is a search results page rather than an individual job listing.

#### Scenario: Individual job listing passes
- **WHEN** the Indeed result URL points to a single job page
- **THEN** the result passes the URL filter

#### Scenario: Search results page is discarded
- **WHEN** the Indeed result URL is a search results page (e.g. contains `/jobs?q=`)
- **THEN** the result SHALL be discarded without an LLM call
