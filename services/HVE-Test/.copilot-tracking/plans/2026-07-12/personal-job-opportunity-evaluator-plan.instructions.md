<!-- markdownlint-disable-file -->
# Implementation Plan: Personal Job Opportunity Evaluator

## Overview
Create a lightweight Python-based web app that lets a single user paste a job description URL, review a basic imported summary, score the opportunity on a simple 100-point rubric, and save the evaluation locally.

## Objectives

### User Requirements
* Support pasting a job description URL and importing basic opportunity details — Source: PRD and ADR in docs/prds/personal-job-opportunity-evaluator.md and docs/decisions/2026-07-12-personal-job-opportunity-evaluator-mvp-v01.md
* Score a job opportunity using a simple 100-point rubric with clear recommendations — Source: PRD section on scoring rubric
* Save and review past evaluations locally — Source: PRD functional requirements

### Derived Objectives
* Deliver the MVP as a small Python web app with minimal complexity and fast iteration — Derived from: lightweight MVP and Python-first constraint
* Keep the experience simple and manual-edit friendly when URL parsing is incomplete — Derived from: basic import requirement and MVP scope

## Context Summary
### Project Files
* docs/prds/personal-job-opportunity-evaluator.md - Product requirements and MVP scope
* docs/decisions/2026-07-12-personal-job-opportunity-evaluator-mvp-v01.md - Architectural decision for a lightweight Python-based MVP
* .copilot-tracking/research/2026-07-12/personal-job-opportunity-evaluator-research.md - Recommended implementation approach

### References
* None beyond workspace documents

### Standards References
* c:\Users\gumiz\.vscode\extensions\ise-hve-essentials.hve-core-all-3.2.2\.github\instructions\coding-standards\python-script.instructions.md — Python implementation standards
* c:\Users\gumiz\.vscode\extensions\ise-hve-essentials.hve-core-all-3.2.2\.github\instructions\hve-core\writing-style.instructions.md — Markdown writing standards

## Implementation Checklist

### [x] Implementation Phase 1: Scaffold the app

<!-- parallelizable: true -->

* [x] Step 1.1: Create the project structure for a Python web app
  * Details: .copilot-tracking/details/2026-07-12/personal-job-opportunity-evaluator-details.md (Lines 1-20)
* [x] Step 1.2: Add dependencies for FastAPI, Jinja2, SQLite support, and HTML parsing
  * Details: .copilot-tracking/details/2026-07-12/personal-job-opportunity-evaluator-details.md (Lines 21-40)
* [x] Step 1.3: Validate scaffolded project files
  * Run Python dependency install and import check
  * Skip if validation conflicts with parallel phases

### [x] Implementation Phase 2: Implement core evaluation flow

<!-- parallelizable: false -->

* [x] Step 2.1: Define the data model for opportunities, scores, and saved evaluations
  * Details: .copilot-tracking/details/2026-07-12/personal-job-opportunity-evaluator-details.md (Lines 41-80)
* [x] Step 2.2: Implement the scoring engine and recommendation logic
  * Details: .copilot-tracking/details/2026-07-12/personal-job-opportunity-evaluator-details.md (Lines 81-110)
* [x] Step 2.3: Build the form and results page flow
  * Details: .copilot-tracking/details/2026-07-12/personal-job-opportunity-evaluator-details.md (Lines 111-140)

### [x] Implementation Phase 3: Add URL import and persistence

<!-- parallelizable: false -->

* [x] Step 3.1: Implement URL parsing and prefill logic for a basic imported summary
  * Details: .copilot-tracking/details/2026-07-12/personal-job-opportunity-evaluator-details.md (Lines 141-170)
* [x] Step 3.2: Persist evaluations and show a history view
  * Details: .copilot-tracking/details/2026-07-12/personal-job-opportunity-evaluator-details.md (Lines 171-200)

### [x] Implementation Phase 4: Validation

<!-- parallelizable: false -->

* [x] Step 4.1: Run full project validation
  * Execute Python import and app startup checks
  * Exercise the main evaluation flow manually
* [x] Step 4.2: Fix minor validation issues
  * Iterate on errors and usability issues
* [x] Step 4.3: Report blocking issues
  * Document anything that needs additional planning

## Planning Log

See .copilot-tracking/plans/logs/2026-07-12/personal-job-opportunity-evaluator-log.md for discrepancy tracking, implementation paths, and suggested follow-on work.

## Dependencies

* Python 3.11+
* FastAPI
* Jinja2
* SQLite
* BeautifulSoup or trafilatura for basic URL parsing

## Success Criteria

* A user can paste a job URL and load a basic form prefill — Traces to: FR-002
* A user can score an opportunity and see a 100-point result and recommendation — Traces to: FR-003
* A user can save and revisit previous evaluations — Traces to: FR-004
