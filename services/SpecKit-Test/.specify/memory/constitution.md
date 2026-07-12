<!--
Sync Impact Report
- Version change: [TEMPLATE] → 1.0.0 (initial ratification)
- Modified principles: n/a (first fill-in of template placeholders)
- Added sections:
  - I. Simplicity First (YAGNI)
  - II. Test-First Verification
  - III. Traceable Spec-Driven Development
  - Development Workflow (Section 2)
  - Quality Gates (Section 3)
  - Governance
- Removed sections: none
- Templates requiring updates:
  - ✅ .specify/templates/plan-template.md — Constitution Check gate reads the constitution dynamically, no hardcoded principle names to update
  - ✅ .specify/templates/spec-template.md — no constitution-specific references present
  - ✅ .specify/templates/tasks-template.md — no constitution-specific references present
  - ✅ .specify/templates/checklist-template.md — no constitution-specific references present
- Follow-up TODOs: none
-->

# SpecKit-Test Constitution

## Core Principles

### I. Simplicity First (YAGNI)

Every feature and abstraction MUST be justified by a current, concrete requirement in
the active spec — not a hypothetical future one. Prefer the simplest solution that
satisfies the spec's acceptance criteria; avoid premature abstraction, speculative
configuration options, or extensibility that no user story currently needs. When a
simpler alternative is rejected, the reason MUST be recorded in the plan's Complexity
Tracking table.

**Rationale**: This is a sandbox project for exercising the SpecKit workflow. Velocity
and clarity matter more here than anticipating scale or requirements that may never
materialize; unjustified complexity makes the spec → plan → tasks trail harder to
follow and defeats the purpose of the exercise.

### II. Test-First Verification

A feature MUST NOT be marked complete based solely on it compiling, type-checking, or
"looking right." It MUST be verified end-to-end against the spec's acceptance
scenarios — via automated tests where practical, or via a documented manual
verification step when automation isn't feasible. When tests are written, they MUST
be written before implementation and MUST fail first (red-green-refactor).

**Rationale**: SpecKit's plan → tasks → implement flow only stays trustworthy if tasks
marked "done" were actually validated against the spec. Skipping verification quietly
erodes trust in the whole artifact chain.

### III. Traceable Spec-Driven Development

Non-trivial work MUST originate from a written spec (or a task explicitly derived from
one) before implementation begins. Code changes SHOULD be traceable back to the
spec/plan/tasks artifacts that motivated them, and deviations from those artifacts
MUST be reflected back into them (via `/speckit-clarify`, `/speckit-plan`, or a direct
edit) rather than left undocumented.

**Rationale**: This project exists specifically to exercise the SpecKit workflow.
Bypassing the spec step produces undocumented, hard-to-audit changes and defeats the
reason this repository exists.

## Development Workflow

Feature specs, plans, and tasks are the source of truth for what to build. Ad-hoc
changes made outside this flow MUST be rare and MUST be justified in the commit
message that introduces them. Formal multi-reviewer PR approval is NOT required given
the sandbox nature of this project, but every change SHOULD be summarized clearly
enough that a future reader can understand its intent without re-deriving it from the
diff alone.

## Quality Gates

Before a task is marked complete, the implementer MUST confirm the change satisfies
its acceptance criteria (via a test run or an explicit manual check) and introduces no
known regressions. When a change alters observable behavior, the relevant spec,
quickstart, or README content MUST be updated in the same change so documentation
never drifts from what the code actually does.

## Governance

This constitution supersedes ad-hoc practice for this repository. Amendments are made
by editing `.specify/memory/constitution.md` directly (typically via the
`/speckit-constitution` command), and every amendment MUST update the version number,
the Sync Impact Report, and the Last Amended date in the same change.

Versioning follows semantic versioning:

- **MAJOR**: Backward-incompatible principle removals or redefinitions.
- **MINOR**: A new principle or section is added, or existing guidance is materially
  expanded.
- **PATCH**: Wording clarifications, typo fixes, and other non-semantic refinements.

Compliance is self-reviewed by whoever implements a task — there is no formal audit
process given this project's sandbox purpose — but this MUST be reconsidered (adding
real review gates) before any work here graduates into a production system. Any plan
produced by `/speckit-plan` MUST include a Constitution Check step that verifies the
proposed approach against the principles above before implementation begins.

**Version**: 1.0.0 | **Ratified**: 2026-07-12 | **Last Amended**: 2026-07-12
