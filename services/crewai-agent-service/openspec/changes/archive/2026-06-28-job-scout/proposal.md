## Why

Manually browsing LinkedIn for EM/Director/Head of Engineering roles takes significant time daily with inconsistent coverage. An automated scout that runs several times per day, filters for genuine fit using the candidate's profile, and sends immediate email notifications would reclaim that time and ensure no relevant opportunity is missed.

## What Changes

- New standalone Python service `services/job-scout/` (separate from crewai-agent-service)
- Scheduled Tavily-powered LinkedIn job search (8 query variants, every 4-6 hours)
- Two-stage relevance filter: fast metadata stage + Gemini LLM stage against candidate profile
- SQLite deduplication — each job URL notified at most once
- Immediate Gmail email per matched job with title, link, and AI-generated relevance paragraph
- Plain-text `profile.md` encoding candidate background — editable without code changes
- `config.env` for API keys, email credentials, and schedule interval

## Capabilities

### New Capabilities
- `job-search`: Periodic Tavily-based LinkedIn job search with title and location pre-filtering
- `job-relevance-filter`: LLM-based relevance judgment (RELEVANT/UNSURE/SKIP) against candidate profile
- `job-deduplication`: SQLite-backed seen-job tracking to prevent re-notification
- `job-notification`: Gmail SMTP email notification with AI relevance paragraph

### Modified Capabilities
<!-- None — this is a new standalone service with no changes to crewai-agent-service -->

## Impact

- New service directory: `services/job-scout/`
- New dependencies: `tavily-python`, `google-generativeai` or `litellm`, `apscheduler`, no additional infrastructure
- Requires: Tavily API key (existing), Gemini API key (existing), Gmail app password (new)
- No changes to existing crewai-agent-service code or API
