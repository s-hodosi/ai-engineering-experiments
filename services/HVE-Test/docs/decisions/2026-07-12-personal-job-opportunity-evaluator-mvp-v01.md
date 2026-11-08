# ADR: Personal Job Opportunity Evaluator MVP

- Date: 2026-07-12
- Status: Accepted
- Deciders: You

## Context
A personal web application is needed to help evaluate job opportunities before applying. The initial goal is to make the process faster and more consistent without building a large or overly complex system.

## Decision
We will build a lightweight MVP that allows a user to:
- paste a job description URL,
- review a basic imported summary,
- enter or adjust key details,
- score the opportunity on a simple 100-point rubric,
- and save the evaluation for later review.

The app will use a simple scoring model based on personal preferences rather than salary benchmarking. Python will be the preferred implementation language when possible, especially for any parsing, scoring, or backend logic.

## Rationale
This approach keeps the first version practical and useful while minimizing implementation effort. It focuses on the core value: helping decide whether a role is worth pursuing.

## Consequences
### Positive
- Fast to build and test.
- Easy to understand and use.
- Provides a repeatable way to compare opportunities.

### Negative
- Importing data from URLs will be basic rather than fully automated.
- The scoring model will be simple and may need refinement later.

## Alternatives Considered
- A fully automated job scraping and evaluation tool.
- A spreadsheet-only workflow.
- A more complex multi-feature application with recruiter and networking workflows.

## Notes
This ADR covers the MVP direction only. Future improvements can add richer import capabilities, more advanced scoring, or additional workflow features.
