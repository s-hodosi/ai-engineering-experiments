## 1. Project Scaffold

- [x] 1.1 Create `services/job-scout/` directory with `main.py`, `searcher.py`, `filter.py`, `notifier.py`, `db.py`
- [x] 1.2 Create `requirements.txt` with dependencies: `tavily-python`, `litellm`, `apscheduler`, `python-dotenv`
- [x] 1.3 Create `config.env` template with: `TAVILY_API_KEY`, `GEMINI_API_KEY`, `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`, `SCHEDULE_INTERVAL_HOURS=6`
- [x] 1.4 Create `profile.md` with candidate background (technical foundation, leadership trajectory, AWS certs, AI learning, target roles, location preferences, hard disqualifiers)

## 2. Database Layer

- [x] 2.1 Implement `db.py`: SQLite schema with `seen_jobs(url TEXT PRIMARY KEY, title TEXT, company TEXT, verdict TEXT, fetched_at TEXT)`
- [x] 2.2 Implement `db.is_seen(url)` and `db.mark_seen(url, title, company, verdict)` functions
- [x] 2.3 Auto-create database file and table on first run if not exists

## 3. Job Searcher

- [x] 3.1 Implement `searcher.py`: define the 8 Tavily query templates covering EM/Senior EM/Director/Head of Engineering/Team Lead × Remote EMEA/Budapest hybrid
- [x] 3.2 Execute all queries with `days=2` freshness filter, collect results (url, title, snippet, location metadata)
- [x] 3.3 Implement Stage 1 metadata pre-filter: discard results not matching target titles or locations

## 4. LLM Relevance Filter

- [x] 4.1 Implement `filter.py`: load `profile.md` at startup, fail with clear error if missing
- [x] 4.2 Implement `filter.evaluate(job)`: construct prompt with profile + job title/location/snippet, call Gemini via LiteLLM at temperature=0.1
- [x] 4.3 Parse LLM response to extract verdict (RELEVANT/UNSURE/SKIP) and explanation paragraph; default to UNSURE on parse failure

## 5. Email Notifier

- [x] 5.1 Implement `notifier.py`: Gmail SMTP connection using `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` from config
- [x] 5.2 Implement `notifier.send(job, verdict, explanation)`: compose email with subject `[Job Scout] <Title> – <Company> (<Location>)` and body with URL + AI paragraph
- [x] 5.3 Fail at startup with clear error if `GMAIL_ADDRESS` or `GMAIL_APP_PASSWORD` are missing from config

## 6. Main Orchestrator

- [x] 6.1 Implement `main.py`: load config from `config.env`, initialise all components, validate required config keys at startup
- [x] 6.2 Implement `run_once()`: search → deduplicate → LLM filter → notify, logging counts at each stage
- [x] 6.3 Wire APScheduler to call `run_once()` on `SCHEDULE_INTERVAL_HOURS` interval; run once immediately on startup then on schedule
- [x] 6.4 Add graceful shutdown on SIGINT/SIGTERM

## 7. Smoke Test

- [x] 7.1 Run the service manually with a forced single execution (`python main.py --once`) and verify: Tavily queries fire, deduplication works, at least one LLM call is made, email is sent for any RELEVANT/UNSURE result
