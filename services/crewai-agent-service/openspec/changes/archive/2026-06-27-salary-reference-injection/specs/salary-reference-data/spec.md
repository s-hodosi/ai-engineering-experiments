## ADDED Requirements

### Requirement: Salary reference CSV loaded at startup
The service SHALL load `salary_db.csv` from the service root directory at module initialisation time and format its contents as a markdown table. The formatted table SHALL be available as a module-level constant for injection into the salary estimation prompt.

#### Scenario: CSV loaded successfully on startup
- **WHEN** the service starts and `salary_db.csv` exists in the service root
- **THEN** the full contents are available as a formatted markdown table with no rows omitted

#### Scenario: Missing CSV raises a clear error
- **WHEN** the service starts and `salary_db.csv` does not exist
- **THEN** a `FileNotFoundError` is raised with a message indicating the expected file path

### Requirement: Full reference table injected into salary agent prompt
The salary agent's task description SHALL include the complete reference table on every invocation. The prompt SHALL instruct the agent to use the reference data as its primary calibration anchor and use web search only for adjustments.

#### Scenario: Reference table present in every salary estimation task
- **WHEN** the salary agent task is constructed
- **THEN** the task description contains the full markdown reference table and explicit anchoring instructions

#### Scenario: Agent flags low confidence when no close match exists
- **WHEN** the role being evaluated has no close match in the reference table (different seniority level, highly niche domain)
- **THEN** the agent returns `confidence: "low"` and explains the gap in the `reasoning` field

### Requirement: Salary output in monthly gross HUF with reasoning
The `SalaryEstimation` model SHALL include a `reasoning` field describing which reference rows were used and what adjustments were applied, and a `unit` field explicitly stating the output unit. `salary_low` and `salary_high` SHALL be integers in HUF (not millions).

#### Scenario: Reasoning field populated on every response
- **WHEN** a salary estimation completes
- **THEN** the `reasoning` field is a non-empty string describing the closest reference match(es) and any adjustments made

#### Scenario: Unit field always set to monthly gross HUF
- **WHEN** a salary estimation completes
- **THEN** `unit` equals `"monthly gross HUF"` and `salary_low` / `salary_high` are full integers (e.g. `2300000`, not `2.3`)

### Requirement: Salary agent temperature set to 0.1
The salary agent SHALL use a near-deterministic LLM configuration (`temperature=0.1`) to minimise run-to-run variance in estimates.

#### Scenario: Repeated runs for same input produce consistent estimates
- **WHEN** the same CV and job description are submitted multiple times
- **THEN** `salary_low` and `salary_high` vary by no more than 10% across runs
