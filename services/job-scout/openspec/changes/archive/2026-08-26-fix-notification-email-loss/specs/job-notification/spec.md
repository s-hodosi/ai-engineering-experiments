## MODIFIED Requirements

### Requirement: Digest email per scheduler run
The system SHALL collect all RELEVANT and UNSURE jobs evaluated during a single scheduler run and send at most one digest email for that run, containing all of them, using Gmail SMTP with app password authentication. Sending and receiving address SHALL be the same (self-email). The system SHALL NOT send more than one notification email per scheduler run, regardless of how many jobs matched.

#### Scenario: Multiple matches in a run produce one digest email
- **WHEN** a scheduler run evaluates jobs and one or more receive verdict RELEVANT or UNSURE
- **THEN** exactly one email is sent at the end of that run, listing every matched job from the run

#### Scenario: No matches in a run
- **WHEN** a scheduler run finds no RELEVANT or UNSURE jobs
- **THEN** no email is sent

### Requirement: Digest email contains role details and AI relevance paragraph per entry
Each entry in the digest email SHALL include: role title, company name (if available), location, job URL, verdict label, and the AI-generated explanation paragraph from the LLM filter.

#### Scenario: Digest subject summarizes the run
- **WHEN** a digest email is sent
- **THEN** the subject SHALL indicate this is a job-scout digest and the number of matched jobs, e.g. `[Job Scout] N new matches`

#### Scenario: Each entry in the digest identifies its role
- **WHEN** a digest email is rendered
- **THEN** each entry SHALL be clearly delimited and include its own title, company, location, verdict, job URL, and the LLM explanation paragraph
