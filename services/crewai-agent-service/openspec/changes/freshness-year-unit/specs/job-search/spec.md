## MODIFIED Requirements

### Requirement: Snippet-based posting age filter
The system SHALL parse age text from Tavily snippets (e.g. "5 months ago", "Posted 2 weeks ago", "4 years ago") and discard results whose parsed age exceeds `FRESHNESS_MAX_AGE_DAYS` (default 3). Supported time units are: `hour`, `day`, `week`, `month`, `year`. Results whose snippet contains "no longer accepting applications" SHALL also be discarded.

#### Scenario: Job posted within threshold
- **WHEN** the snippet contains "2 days ago" and `FRESHNESS_MAX_AGE_DAYS` is 3
- **THEN** the result passes the freshness filter

#### Scenario: Job posted beyond threshold
- **WHEN** the snippet contains "2 weeks ago" or "1 month ago"
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Job posted years ago is discarded
- **WHEN** the snippet contains "4 years ago" or any N years ago
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: Job no longer accepting applications
- **WHEN** the snippet contains "no longer accepting applications"
- **THEN** the result SHALL be discarded without an LLM call

#### Scenario: No posting age text in snippet
- **WHEN** the snippet contains no age pattern and no "no longer accepting" text
- **THEN** the result passes the snippet age check and proceeds to the next freshness layer
