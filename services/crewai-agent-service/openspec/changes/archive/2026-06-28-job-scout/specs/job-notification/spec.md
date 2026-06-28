## ADDED Requirements

### Requirement: Immediate Gmail email per matched job
The system SHALL send one email per RELEVANT or UNSURE job immediately upon filtering, using Gmail SMTP with app password authentication. Sending and receiving address SHALL be the same (self-email).

#### Scenario: RELEVANT job email sent immediately
- **WHEN** a job receives verdict RELEVANT
- **THEN** an email is sent within the same scheduler run, without waiting for batch collection

#### Scenario: UNSURE job email sent immediately
- **WHEN** a job receives verdict UNSURE
- **THEN** an email is sent within the same scheduler run with UNSURE verdict visible in subject or body

#### Scenario: No matches in a run
- **WHEN** a scheduler run finds no RELEVANT or UNSURE jobs
- **THEN** no email is sent

### Requirement: Email contains role details and AI relevance paragraph
Each notification email SHALL include: role title, company name (if available), location, job URL, verdict label, and the AI-generated explanation paragraph from the LLM filter.

#### Scenario: Email subject identifies the role
- **WHEN** an email is sent for a matched job
- **THEN** the subject SHALL follow the format: `[Job Scout] <Title> – <Company> (<Location>)`

#### Scenario: Email body contains link and AI paragraph
- **WHEN** an email is rendered
- **THEN** the body SHALL include the full job URL and the LLM explanation paragraph

### Requirement: Email credentials loaded from config
The system SHALL load Gmail address and app password from `config.env`. The app password SHALL never be hardcoded.

#### Scenario: Missing credentials fail with clear error
- **WHEN** GMAIL_ADDRESS or GMAIL_APP_PASSWORD is not set in config.env
- **THEN** the service SHALL fail at startup with a descriptive error message
