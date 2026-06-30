## 1. Task Scheduler Fix

- [x] 1.1 Re-register the JobScout scheduled task to execute `pythonw.exe` directly with `main.py --once`, removing the `cmd.exe` wrapper
- [x] 1.2 Delete `run_scout.bat`
- [x] 1.3 Verify no console window appears on next scheduled run

## 2. Database

- [x] 2.1 Add `processed_emails` table to `db.py` with `message_id TEXT PRIMARY KEY` and `processed_at TEXT`
- [x] 2.2 Add `init_processed_emails(path)`, `is_email_processed(message_id, path)`, and `mark_email_processed(message_id, path)` functions to `db.py`
- [x] 2.3 Update `init_db()` to create `processed_emails` table alongside `seen_jobs`

## 3. LinkedIn Email Source

- [x] 3.1 Create `linkedin_email_source.py` with Gmail IMAP connection using `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD`
- [x] 3.2 Implement IMAP search for LinkedIn alert emails (FROM `jobalerts-noreply@linkedin.com`) within last 7 days
- [x] 3.3 Implement email HTML parsing to extract job listings (title, company, location, redirect URL) from LinkedIn alert email body using `beautifulsoup4`
- [x] 3.4 Implement redirect URL resolution: follow `linkedin.com/comm/jobs/view/` tracking URLs to canonical `linkedin.com/jobs/view/` URLs
- [x] 3.5 Implement JD page fetching with browser-realistic headers; extract description text from `div.show-more-less-html__markup`
- [x] 3.6 Implement `[limited info]` fallback: if extracted text < 200 chars or fetch fails, set snippet to `[limited info — JD not accessible]`
- [x] 3.7 Implement email-level dedup: skip emails whose Message-ID is in `processed_emails`; insert Message-ID after processing
- [x] 3.8 Add `beautifulsoup4` to `requirements.txt` and remove `tavily-python`

## 4. Main Pipeline

- [x] 4.1 Update `main.py`: replace `tavily_search` + `adzuna_search` imports and calls with `linkedin_email_source.fetch_jobs()`
- [x] 4.2 Remove title pre-filter logic from `main.py` (if any residual references remain)
- [x] 4.3 Update `run_once()` to pass `GMAIL_ADDRESS` and `GMAIL_APP_PASSWORD` to `linkedin_email_source.fetch_jobs()`

## 5. Cleanup

- [x] 5.1 Delete `searcher.py`
- [x] 5.2 Delete `adzuna_searcher.py`
- [x] 5.3 Update `test_smoke.py` to use `linkedin_email_source` instead of `tavily_search` / `adzuna_search`
- [x] 5.4 Note in `config.env` that `TAVILY_API_KEY`, `ADZUNA_APP_ID`, `ADZUNA_APP_KEY` are no longer used (do not commit config.env)

## 6. Smoke Test

- [x] 6.1 Run `python main.py --once` manually and verify LinkedIn alert emails are found and parsed
- [x] 6.2 Verify at least one JD is fetched and snippet is populated (or `[limited info]` logged with reason)
- [x] 6.3 Verify no duplicate emails are sent on second run
