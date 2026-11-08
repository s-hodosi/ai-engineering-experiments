# Personal Job Opportunity Evaluator - Implementation Research

Date: 2026-07-12
Status: Complete

## Scope

This research is focused on the MVP implementation approach for a personal web app that evaluates job opportunities using the existing product requirements and architecture decision records in this workspace.

Evidence from the current workspace:
- The PRD in [docs/prds/personal-job-opportunity-evaluator.md](docs/prds/personal-job-opportunity-evaluator.md) defines the MVP as a single-user, lightweight app with URL-based import, a 100-point weighted score, and local persistence.
- The ADR in [docs/decisions/2026-07-12-personal-job-opportunity-evaluator-mvp-v01.md](docs/decisions/2026-07-12-personal-job-opportunity-evaluator-mvp-v01.md) explicitly favors a lightweight Python-based implementation for the first version.
- The workspace currently contains documentation and tracking folders, but no application implementation scaffold yet, so the approach should be a new small web app rather than an extension of existing code.

## Assumptions

The following assumptions are used to shape the implementation plan:
- The app is for one user and does not require authentication, accounts, or multi-user hosting.
- Data should remain private and local by default, with SQLite as the simplest durable option.
- URL import is a basic convenience feature, not a fully automated scraping pipeline.
- The scoring model is transparent and editable, with the MVP using the six weighted criteria from the PRD.
- The primary goal is to validate the evaluation workflow quickly, not to build a full recruiting platform.

## Implementation Alternatives

### Option 1: Streamlit app

Pros:
- Fastest path to a working Python prototype.
- Built-in forms, tables, and simple UI components.
- Minimal boilerplate for a single-user internal tool.

Cons:
- Less suited to a polished personal web app experience.
- Harder to evolve into a more structured app later.
- Less control over HTML structure and deployment style.

### Option 2: Flask + Jinja2 + SQLite

Pros:
- Very lightweight and easy to understand.
- Fits a small single-user web app well.
- Straightforward for form handling, templates, and local persistence.

Cons:
- Slightly more manual template and routing setup than newer Python web stacks.
- Less modern than FastAPI for API-first development.

### Option 3: FastAPI + Jinja2/HTMX + SQLite

Pros:
- Strong fit for a Python-preferred MVP with a simple web interface.
- Clean separation between routes, business logic, and persistence.
- Easy to add a small API layer later without rewriting the app.
- Good balance of simplicity and maintainability for a personal tool.

Cons:
- Slightly more setup than Flask or Streamlit.
- Requires a bit more structure than a one-file prototype.

## Selected Approach

The recommended MVP is a small Python web application built with FastAPI, Jinja2 templates, and SQLite.

Why this fits the stated constraints:
- It aligns with the PRD’s requirement for a simple personal web app.
- It satisfies the ADR’s preference for Python and a lightweight implementation.
- It supports the core user flow: paste a job URL, review a parsed summary, enter or adjust details, score the role out of 100, and save the record locally.
- It keeps the first version maintainable without over-engineering the architecture.

### Proposed architecture
- Backend: FastAPI for routes and evaluation logic.
- UI: server-rendered HTML templates with minimal JavaScript or HTMX for lightweight interactivity.
- Persistence: SQLite for local storage of evaluations, criteria settings, and history.
- URL import: use Python HTTP requests plus an HTML parser such as BeautifulSoup or trafilutra to extract basic page text and prefill the form.
- Scoring: implement the PRD rubric as a weighted model with six criteria scored 1–5 and converted to a total out of 100.

### MVP feature set
- Dashboard with a form for new opportunities.
- URL input field that attempts to extract title, company, location, and summary.
- Manual review/edit step before scoring.
- Score summary showing both raw criterion ratings and final weighted result.
- Saved history view for previously evaluated opportunities.
- Simple settings page for adjusting weights or disabling criteria later.

## Recommended Implementation Plan

1. Create a new Python web app skeleton with FastAPI, Jinja2, and SQLite.
2. Define the initial data model for opportunities, evaluations, and scoring settings.
3. Implement the evaluation form and scoring engine for the six PRD criteria.
4. Add URL import parsing with graceful fallback to manual entry when parsing is incomplete.
5. Implement local persistence and a simple history page.
6. Validate the flow manually with a few sample job postings.

## Next Steps

- Scaffold the project structure and dependency list.
- Implement the minimum viable evaluation flow first, then add URL import.
- Keep the UI intentionally simple and prioritize clarity over advanced automation.
- Treat any parsing limitations as acceptable for the MVP and preserve a manual edit path.
