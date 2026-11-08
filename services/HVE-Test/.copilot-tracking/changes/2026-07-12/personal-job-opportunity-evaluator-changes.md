<!-- markdownlint-disable-file -->
# Release Changes: Personal Job Opportunity Evaluator

**Related Plan**: personal-job-opportunity-evaluator-plan.instructions.md
**Implementation Date**: 2026-07-12

## Summary
Extended the initial MVP scaffold with basic URL import and local persistence, allowing evaluations to be prefilled from a job page URL and saved for later review.

## Changes

### Added
* app/services/importer.py - basic HTML-based job URL parsing and form prefill
* app/db.py - SQLite persistence for saved evaluations
* templates/history.html - saved evaluations index page
* templates/history_detail.html - saved evaluation detail page
* tests/test_importer.py - regression tests for job URL import parsing

### Modified
* app/main.py - added import, save, and history routes
* templates/index.html - added URL import form, prefill fields, and history link

### Removed
* None

## Additional or Deviating Changes
* The implementation uses a simple parser with graceful fallback to manual entry when parsing is incomplete.
  * Reason: This keeps the MVP useful and lightweight while still supporting the URL import workflow.

## Release Summary
Implemented the next slice of the MVP: a lightweight Python web app that accepts manual or URL-imported job inputs, computes a simple 100-point score and recommendation, saves evaluations locally, and supports browsing prior results. Validation completed with pytest: 3 passed.
