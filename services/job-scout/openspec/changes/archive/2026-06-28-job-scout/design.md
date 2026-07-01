## Context

The user manually browses LinkedIn multiple times daily for EM/Director/Head of Engineering roles. This is a new standalone Python service separate from the existing crewai-agent-service. It reuses existing API keys (Tavily, Gemini) and adds only a Gmail app password. No web framework or agent orchestration framework is needed — this is a lightweight scheduled script.

## Goals / Non-Goals

**Goals:**
- Automated periodic job discovery via Tavily LinkedIn search
- LLM-based relevance filtering against a fixed candidate profile
- Immediate Gmail notification per matched job
- SQLite deduplication to prevent re-notification
- Zero-infrastructure: runs as a Python process, no Docker or server required

**Non-Goals:**
- Full job evaluation (that's crewai-agent-service's role)
- Scraping LinkedIn directly (ToS risk, fragility)
- Digest/batching (immediate per-job email is sufficient at 1-3 matches/day)
- Multi-user support
- Web UI

## Decisions

### D1: Tavily search-engine approach over direct LinkedIn scraping
LinkedIn blocks scrapers aggressively and the ToS prohibits it. Tavily's indexed search is stable, uses the existing API key, and is accurate enough for this volume. Freshness lag of 24-48 hours is acceptable.

### D2: Snippet-based LLM filter (not full page fetch)
Tavily snippets (150-300 words) capture enough signal to detect hard requirements and location nuance. Fetching full LinkedIn pages requires authentication and is fragile. If a snippet is insufficient, the LLM returns UNSURE — which triggers notification anyway, letting the user read the full JD themselves.

### D3: Gemini called directly via LiteLLM, not through CrewAI
The filter is a single LLM call — no agent orchestration needed. Using LiteLLM directly (same as in crewai-agent-service) keeps the dependency consistent without CrewAI overhead.

### D4: SQLite for deduplication (not a flat file)
A flat file (JSON/text) of seen URLs would work but SQLite is only marginally more complex and gives queryable history (verdict, timestamp, company) at no extra infrastructure cost. A single table suffices.

### D5: APScheduler for scheduling (not Windows Task Scheduler / cron)
APScheduler runs inside the Python process — no OS-level scheduling configuration needed. The service is started once and runs indefinitely, making it portable across environments.

### D6: profile.md as plain text (not YAML/JSON)
The LLM prompt injects the profile verbatim. A plain paragraph reads more naturally in a prompt than structured data, and the user can edit it without caring about syntax.

### D7: Temperature 0.1 for LLM filter
Consistency matters more than creativity for a binary classification call. Low temperature reduces day-to-day variation in verdicts for the same job.

## Risks / Trade-offs

- **[Search index lag]** LinkedIn jobs may not appear in Tavily results for 24-48h after posting → Mitigation: acceptable for personal use; running every 4-6h with days=2 freshness filter covers the window
- **[Snippet incompleteness]** Key requirements may not appear in the snippet → Mitigation: UNSURE verdict for ambiguous cases; user reads the full JD from the link
- **[Tavily query quota]** 8 queries × 4-6 runs/day = 32-48 queries/day → well within Tavily free tier; no mitigation needed
- **[Gmail sending rate]** At 1-3 emails/day far below any limit → no mitigation needed
- **[False negatives]** A relevant job not indexed by Tavily in time or filtered too aggressively → UNSURE threshold is intentionally loose to minimise misses

## Open Questions

- None — design is fully specified for v1. Schedule interval (default: 6 hours) configurable via `SCHEDULE_INTERVAL_HOURS` in `config.env`.
