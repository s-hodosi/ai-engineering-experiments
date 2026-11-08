<!-- markdownlint-disable-file -->
# Implementation Details: Personal Job Opportunity Evaluator

## Context Reference
Sources: docs/prds/personal-job-opportunity-evaluator.md, docs/decisions/2026-07-12-personal-job-opportunity-evaluator-mvp-v01.md, .copilot-tracking/research/2026-07-12/personal-job-opportunity-evaluator-research.md

## Implementation Phase 1: Scaffold the app

<!-- parallelizable: true -->

### Step 1.1: Create the project structure for a Python web app
Create a small FastAPI project structure with separate folders for app logic, templates, static assets, and data persistence.

Files:
* app/main.py - application entry point
* app/models.py - data models for evaluations and settings
* app/schemas.py - request/response schemas if needed
* templates/ - HTML templates for the main flow
* data/ - local SQLite database location

Success criteria:
* The project can be started locally with a simple command
* The app serves a basic home page

### Step 1.2: Add dependencies for FastAPI, Jinja2, SQLite support, and HTML parsing
Add a requirements file or pyproject dependency list for the Python runtime.

Files:
* requirements.txt - Python package list

Success criteria:
* Dependencies install successfully in a Python environment
* Imports for FastAPI, Jinja2, and a parser library work

### Step 1.3: Validate scaffolded project files
Run a basic import and startup check for the app.

Validation commands:
* python -m pip install -r requirements.txt - install dependencies
* python -m compileall app - compile the app package

## Implementation Phase 2: Implement core evaluation flow

<!-- parallelizable: false -->

### Step 2.1: Define the data model for opportunities, scores, and saved evaluations
Create the storage model for a saved opportunity and its evaluation result.

Files:
* app/models.py - database model definitions
* app/db.py - SQLite setup and helpers

Success criteria:
* A new evaluation record can be created and stored locally
* The app can load a saved evaluation for review

### Step 2.2: Implement the scoring engine and recommendation logic
Implement the weighted scoring rubric from the PRD and convert the five-point criterion ratings into a 100-point total.

Files:
* app/services/scoring.py - scoring engine

Success criteria:
* A sample score produces the expected total and recommendation band
* The logic is easy to adjust for future weights changes

### Step 2.3: Build the form and results page flow
Create the pages that capture job details, collect criterion scores, and show the summary.

Files:
* templates/new_evaluation.html - form for entering details and scores
* templates/result.html - summary page for the completed evaluation

Success criteria:
* A user can complete the full scoring workflow from form submission to result view

## Implementation Phase 3: Add URL import and persistence

<!-- parallelizable: false -->

### Step 3.1: Implement URL parsing and prefill logic for a basic imported summary
Add a simple URL import flow that fetches the page, extracts title/company/location/summary text, and pre-fills the form.

Files:
* app/services/importer.py - URL parsing helper
* app/main.py - route wiring for import submission

Success criteria:
* A pasted URL produces a basic populated form for review
* If parsing fails, the user can still complete the form manually

### Step 3.2: Persist evaluations and show a history view
Save evaluations to SQLite and expose a page listing prior items.

Files:
* templates/history.html - saved evaluations list
* app/main.py - history routes

Success criteria:
* A completed evaluation is saved locally
* The history page lists previous evaluations and allows viewing details

## Implementation Phase 4: Validation

<!-- parallelizable: false -->

### Step 4.1: Run full project validation
Exercise the main flow end to end and confirm it works locally.

Validation commands:
* python -m compileall app
* uvicorn app.main:app --reload

### Step 4.2: Fix minor validation issues
Resolve small issues found during manual testing.

### Step 4.3: Report blocking issues
Document any issues that require additional planning or scope reduction.

## Dependencies

* Python 3.11+
* FastAPI
* Jinja2
* SQLite
* BeautifulSoup or trafilatura

## Success Criteria

* The app can start locally and render the main page
* The evaluation flow works end to end
* URL import provides basic prefill data for manual review
