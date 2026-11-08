<!-- markdownlint-disable-file -->
<!-- markdown-table-prettify-ignore-start -->
# Personal Job Opportunity Evaluator - Product Requirements Document (PRD)
Version 0.1 | Status Draft | Owner You | Team Personal | Target MVP | Lifecycle Discovery

## Progress Tracker
| Phase | Done | Gaps | Updated |
|-------|------|------|---------|
| Context | Yes | None | 2026-07-12 |
| Problem & Users | Yes | Minor refinement | 2026-07-12 |
| Scope | Yes | Confirm MVP priorities | 2026-07-12 |
| Requirements | Yes | Add detailed scoring logic | 2026-07-12 |
| Metrics & Risks | Partial | Add success thresholds | 2026-07-12 |
| Operationalization | Partial | Define deployment and support plan | 2026-07-12 |
| Finalization | Partial | Review with user | 2026-07-12 |
Unresolved Critical Questions: 3 | TBDs: 4

## 1. Executive Summary
### Context
You want a personal web application that helps evaluate job opportunities before you invest time in applying. The app should make it easier to compare roles, assess fit, and decide which opportunities are worth pursuing.
### Core Opportunity
A single dashboard can reduce decision fatigue by consolidating job data, role fit analysis, salary context, and application priorities in one place.
### Goals
| Goal ID | Statement | Type | Baseline | Target | Timeframe | Priority |
|---------|-----------|------|----------|--------|-----------|----------|
| G-001 | Help me quickly decide whether a job opportunity is worth pursuing. | User value | Manual spreadsheet or ad hoc evaluation | < 5 minutes per opportunity | MVP | High |
| G-002 | Provide a consistent framework for comparing multiple roles. | Productivity | Inconsistent evaluation across roles | Standardized scorecard for every role | MVP | High |
| G-003 | Reduce the time spent reviewing job postings and deciding where to apply. | Efficiency | Manual review of each posting | 50% reduction in review time | MVP | Medium |

## 2. Problem Definition
### Current Situation
Job search involves reviewing many postings, comparing compensation and responsibilities, and deciding which roles align with your goals. This process is often fragmented across job boards, notes, and spreadsheets.
### Problem Statement
It is difficult to evaluate and compare job opportunities consistently and efficiently, which leads to wasted effort on roles that are not a strong fit.
### Root Causes
* Job data is scattered across multiple sources.
* There is no lightweight personal scoring model for role fit.
* Decision-making is often based on intuition rather than a repeatable framework.
### Impact of Inaction
Time is lost on weak opportunities, confidence in decision-making is lower, and it becomes harder to prioritize applications effectively.

## 3. Users & Personas
| Persona | Goals | Pain Points | Impact |
|---------|-------|------------|--------|
| Job Seeker | Evaluate opportunities quickly and consistently | Too many roles, unclear fit, hard to compare | Better prioritization and less wasted effort |

### Journeys (Optional)
1. User imports or enters a job opportunity.
2. The app analyzes key attributes such as role fit, compensation, location, and growth potential.
3. The app produces a score and recommendation.
4. The user saves the result and decides whether to apply.

## 4. Scope
### In Scope
* Capture basic job opportunity details.
* Support basic import of a job opportunity from a pasted job description URL.
* Evaluate opportunity fit using a configurable scoring model.
* Show a simple recommendation such as strong fit, moderate fit, or low fit.
* Allow users to save and review past opportunities.
### Out of Scope (justify if empty)
* Automated application submission.
* Full recruiter or networking workflow.
* Real-time job scraping from all job boards in MVP.
### Assumptions
* The user will enter or import job data manually in the MVP.
* The app will be used by a single user.
### Constraints
* MVP should remain lightweight and easy to maintain.
* The initial experience should prioritize clarity over advanced automation.
* Python should be used when possible for implementation and any server-side processing.

## 5. Product Overview
### Value Proposition
The app gives you a repeatable way to assess job opportunities so you can focus on the roles most likely to align with your goals.
### Differentiators (Optional)
* Personalized evaluation rules.
* Simple and private experience for a single user.
### UX / UI (Conditional)
A clean dashboard with a form for entering opportunities, a score summary, and a history list of prior evaluations. UX Status: Draft

## 6. Functional Requirements
| FR ID | Title | Description | Goals | Personas | Priority | Acceptance | Notes |
|-------|-------|------------|-------|----------|----------|-----------|-------|
| FR-001 | Capture opportunity details | The app shall allow the user to enter or import the title, company, location, salary, remote policy, and summary of a job opportunity. | G-001, G-002 | Job Seeker | High | A user can create a new opportunity record with the required fields. | MVP |
| FR-002 | Import opportunity from pasted URL | The app shall allow the user to paste a job description URL and use it as a starting point for populating the opportunity details. | G-001, G-003 | Job Seeker | High | A user can submit a URL and receive a basic parsed summary for review. | Basic import only |
| FR-003 | Evaluate fit score | The app shall compute a simple weighted fit score out of 100 based on configurable criteria such as role alignment, location, growth potential, and effort to apply. | G-001, G-002 | Job Seeker | High | The app displays a numeric score and a recommendation label. | Score model to be refined |
| FR-004 | Save and review history | The app shall persist opportunities so the user can revisit previous evaluations. | G-002, G-003 | Job Seeker | High | A user can view a list of all saved opportunities and open an individual record. | MVP |
| FR-005 | Customize evaluation weights | The app shall allow the user to change the scoring weights or criteria for future evaluations. | G-002 | Job Seeker | Medium | The user can update evaluation preferences from a settings screen. | Nice to have in MVP |
| FR-006 | Export or share summary | The app shall provide a simple export or shareable summary for an opportunity. | G-003 | Job Seeker | Low | The user can export a summary as plain text or PDF. | Optional |

### Scoring Rubric
The app shall use a weighted rubric to evaluate each opportunity on a 100-point scale. The rubric is intended to be transparent, configurable, and easy to adjust as preferences change.

| Criterion | Weight | Scoring Guidance | Notes |
|-----------|--------|------------------|-------|
| Salary fit | 25% | Score based on whether the compensation meets your target range and expectations. | Use a simple 1–5 scale and map it to the weighted total. |
| Role alignment | 25% | Score based on how closely the role matches your experience, interests, and career goals. | This is the most important qualitative factor. |
| Location and flexibility | 15% | Score based on commute, relocation needs, and remote work policy. | Can be adjusted based on your preferences. |
| Growth potential | 15% | Score based on learning opportunities, progression, and long-term upside. | Useful for roles that may be promising but not ideal immediately. |
| Company and team fit | 10% | Score based on company reputation, mission, team quality, or culture fit. | Keep this lightweight and subjective. |
| Effort to apply | 10% | Score based on how much time or friction is involved in pursuing the role. | Helps prioritize roles that are worth the effort. |

#### Score Bands
| Total Score | Recommendation |
|------------|----------------|
| 85–100 | Strong fit |
| 65–84 | Good fit |
| 45–64 | Moderate fit |
| 0–44 | Low fit |

#### Scoring Rules
* Each criterion shall be scored on a 1–5 scale before being converted to the weighted total.
* The app shall display both the raw criterion scores and the final weighted score.
* The user shall be able to edit the weights or disable criteria in settings.
* The rubric shall be stored as part of the evaluation configuration so it remains consistent across opportunities.

#### Simple Example
Assume the app evaluates one opportunity with the following scores:

| Criterion | Score (1–5) | Weight | Weighted Contribution |
|-----------|-------------|--------|------------------------|
| Salary fit | 4 | 25% | 20 |
| Role alignment | 5 | 25% | 25 |
| Location and flexibility | 3 | 15% | 9 |
| Growth potential | 4 | 15% | 12 |
| Company and team fit | 3 | 10% | 6 |
| Effort to apply | 2 | 10% | 4 |

Total score: 76/100

Recommendation: Good fit

## 7. Non-Functional Requirements
| NFR ID | Category | Requirement | Metric/Target | Priority | Validation | Notes |
|--------|----------|------------|--------------|----------|-----------|-------|
| NFR-001 | Usability | The interface should be easy to understand and use without training. | First-time user can create an evaluation in under 5 minutes | High | User testing | MVP |
| NFR-002 | Performance | The app should respond quickly for common actions such as save and score. | Page interactions complete in under 2 seconds | High | Manual benchmark | MVP |
| NFR-003 | Privacy | Opportunity data should remain private to the user. | No data shared externally without explicit user action | High | Review | MVP |
| NFR-004 | Reliability | The app should preserve evaluations safely. | No data loss for normal save operations | High | Manual test | MVP |

## 8. Data & Analytics (Conditional)
### Inputs
* Job title
* Company name
* Location
* Salary or compensation range
* Remote status
* Notes or summary
### Outputs / Events
* Fit score
* Recommendation level
* Saved opportunity record
### Instrumentation Plan
| Event | Trigger | Payload | Purpose | Owner |
|-------|---------|--------|---------|-------|
| Opportunity evaluated | User submits a score evaluation | Opportunity ID, score, recommendation | Measure usage and quality | You |
| Opportunity saved | User saves a record | Opportunity ID, timestamp | Track retention and usage | You |
### Metrics & Success Criteria
| Metric | Type | Baseline | Target | Window | Source |
|--------|------|----------|--------|--------|--------|
| Time to evaluate one opportunity | Efficiency | Manual review | < 5 minutes | Per evaluation | App logs |
| Number of opportunities reviewed | Usage | 0 | 10+ per month | Monthly | App logs |

## 9. Dependencies
| Dependency | Type | Criticality | Owner | Risk | Mitigation |
|-----------|------|------------|-------|------|-----------|
| Simple hosting solution | Technical | High | You | Low | Use low-cost static or lightweight web hosting |
| Storage for saved evaluations | Technical | High | You | Medium | Start with local storage or a simple database |

## 10. Risks & Mitigations
| Risk ID | Description | Severity | Likelihood | Mitigation | Owner | Status |
|---------|-------------|---------|-----------|-----------|-------|--------|
| R-001 | The scoring model may not reflect the user’s actual preferences. | Medium | Medium | Allow easy adjustment of weights and criteria. | You | Open |
| R-002 | Data entry may be too manual for regular use. | Medium | Medium | Add import or paste-from-link capabilities later. | You | Open |

## 11. Privacy, Security & Compliance
### Data Classification
Personal career and employment data.
### PII Handling
The app should store only the information necessary for evaluation and avoid sharing it with third parties.
### Threat Considerations
* Accidental exposure of personal career history.
* Loss of saved opportunity records.
### Regulatory / Compliance (Conditional)
No immediate regulatory requirements identified for the MVP.

## 12. Operational Considerations
| Aspect | Requirement | Notes |
|--------|------------|-------|
| Deployment | Deploy as a simple personal web app with minimal maintenance | |
| Rollback | Keep data export and backup simple | |
| Monitoring | Track basic usage and errors | |
| Alerting | Not required for MVP | |
| Support | Self-service for the single user | |
| Capacity Planning | Minimal capacity requirements | |

## 13. Rollout & Launch Plan
### Phases / Milestones
| Phase | Date | Gate Criteria | Owner |
|-------|------|--------------|-------|
| MVP build | 2026-07 | Core evaluation flow works | You |
| Initial use | 2026-08 | User can create and review evaluations | You |
### Feature Flags (Conditional)
No feature flags planned for MVP.
### Communication Plan (Optional)
Not required for the MVP.

## 14. Open Questions
| Q ID | Question | Owner | Deadline | Status |
|------|----------|-------|---------|--------|
| Q-001 | Should the app use a simple score out of 100 or a more nuanced rating system? | You | 2026-07-19 | Resolved: use a simple score out of 100 |
| Q-002 | Should the app support importing job postings from URLs or plain text? | You | 2026-07-19 | Updated: MVP will support pasted JD URLs first |
| Q-003 | Do you want the app to include salary benchmarking or just self-defined preferences? | You | 2026-07-19 | Resolved: use self-defined preferences only; no salary benchmarking |

## 15. Changelog
| Version | Date | Author | Summary | Type |
|---------|------|-------|---------|------|
| 0.1 | 2026-07-12 | You | Initial draft PRD for a personal job opportunity evaluator | Initial Draft |

## 16. References & Provenance
| Ref ID | Type | Source | Summary | Conflict Resolution |
|--------|------|--------|---------|--------------------|
| REF-001 | User input | Conversation | Initial product concept and scope | N/A |

### Citation Usage
This PRD is based on the initial product concept provided in the conversation.

## 17. Appendices (Optional)
### Glossary
| Term | Definition |
|------|-----------|
| Opportunity | A job posting or role being considered |
| Fit score | A personalized score representing alignment with the user’s criteria |
### Additional Notes
The app can evolve later into a more automated role-tracking and application-management tool.

Generated 2026-07-12 by GitHub Copilot (mode: PRD Builder)
<!-- markdown-table-prettify-ignore-end -->
