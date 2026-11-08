<!-- markdownlint-disable-file -->
# Planning Log: Personal Job Opportunity Evaluator

## Discrepancy Log

### Unaddressed Research Items
* DR-01: Full automated scraping and extraction from arbitrary job sites is not planned for the MVP.
  * Source: .copilot-tracking/research/2026-07-12/personal-job-opportunity-evaluator-research.md
  * Reason: The MVP scope prioritizes a basic import flow and a lightweight experience.
  * Impact: medium

### Plan Deviations from Research
* DD-01: The research recommends FastAPI + Jinja2 + SQLite; the plan uses the same approach.
  * Research recommends: FastAPI + Jinja2 + SQLite
  * Plan implements: FastAPI + Jinja2 + SQLite
  * Rationale: This is the selected approach and matches the stated constraints.

## Implementation Paths Considered

### Selected: Lightweight Python web app
* Approach: Build a small FastAPI application with server-rendered templates and SQLite.
* Rationale: It is simple, Python-friendly, and appropriate for a personal MVP.
* Evidence: .copilot-tracking/research/2026-07-12/personal-job-opportunity-evaluator-research.md

### IP-01: Streamlit app
* Approach: Build the MVP as a Streamlit app.
* Trade-offs: Fastest prototype, but less suited to a polished personal web app and harder to evolve later.
* Rejection rationale: The selected approach offers more structure and better future flexibility.

## Suggested Follow-On Work

* WI-01: Add richer import parsing for common job boards — medium
  * Source: PRD and research note
  * Dependency: Basic URL import flow must work first
* WI-02: Add user preferences for custom criteria weights — medium
  * Source: PRD functional requirement FR-005
  * Dependency: Core scoring flow must be proven
