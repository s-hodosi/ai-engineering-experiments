## Why

Tavily (LinkedIn scraping via Google) returns stale, JS-gated results — posting age and "no longer accepting" status are not in the static HTML, causing old and closed jobs to pass through all filters. Adzuna covers EU breadth but produces too much irrelevant noise. LinkedIn's own job alert emails contain accurate server-rendered metadata and are already filtered by the user's saved searches, making them a cleaner and zero-cost source.

## What Changes

- **NEW**: `linkedin_email_source.py` — reads unread LinkedIn job alert emails from Gmail via IMAP, parses job listings from HTML email bodies, fetches full JD text from LinkedIn job pages, and implements email-level deduplication via a `processed_emails` DB table
- **REMOVED**: `searcher.py` (Tavily source) and `adzuna_searcher.py` (Adzuna source)
- **REMOVED**: Title regex pre-filter — LinkedIn's alert filtering makes it redundant
- **REMOVED**: Freshness/age pre-filter — LinkedIn only sends alerts for active, recent postings
- **MODIFIED**: `main.py` — replaces search calls with `linkedin_email_source.fetch_jobs()`
- **MODIFIED**: `db.py` — adds `processed_emails` table for email-level dedup
- **MODIFIED**: `requirements.txt` — removes `tavily-python`, adds `beautifulsoup4`
- **MODIFIED**: Task Scheduler registration — runs `pythonw.exe` directly (no `cmd.exe` wrapper) to eliminate console window popup
- **JD fetch fallback**: if LinkedIn gates the page, job is passed to Gemini with `[limited info]` label rather than skipped

## Capabilities

### New Capabilities
- `linkedin-email-source`: Gmail IMAP reading of LinkedIn job alert emails, HTML job listing extraction, LinkedIn JD page fetching, and email-level deduplication via processed_emails table

### Modified Capabilities
- `job-search`: All Tavily and pre-filter requirements removed (source replaced entirely)
- `job-search-adzuna`: All requirements removed (source replaced entirely)
- `job-deduplication`: New email-level dedup layer added (processed_emails table alongside existing job URL dedup)

## Impact

- `services/job-scout/linkedin_email_source.py` — new file
- `services/job-scout/searcher.py` — deleted
- `services/job-scout/adzuna_searcher.py` — deleted
- `services/job-scout/main.py` — updated imports and run_once() logic
- `services/job-scout/db.py` — new processed_emails table
- `services/job-scout/requirements.txt` — dependency swap
- `services/job-scout/run_scout.bat` — deleted (Task Scheduler updated to call pythonw.exe directly)
- Windows Task Scheduler "JobScout" task — re-registered without cmd.exe wrapper
- Config: `TAVILY_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` no longer needed (can be removed from config.env)
