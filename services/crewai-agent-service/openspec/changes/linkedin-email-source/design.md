## Context

job-scout currently uses Tavily (Google-indexed LinkedIn scraping) and Adzuna (EU job aggregator API) as sources. Both have fundamental limitations: Tavily's static HTML scraping misses JS-rendered metadata (posting age, closed status), and Adzuna produces too many irrelevant results. The user receives daily LinkedIn job alert emails for 3 saved searches; these emails contain accurate server-rendered metadata and pre-filtered results. The Gmail account is already configured for SMTP sending; the same app password works for IMAP reading.

## Goals / Non-Goals

**Goals:**
- Replace Tavily and Adzuna with LinkedIn alert email parsing as the sole job source
- Implement two-level deduplication: email-level (processed_emails table) + job-level (existing seen_jobs table)
- Fetch full JD text from LinkedIn job pages to support meaningful Gemini evaluation
- Eliminate the cmd.exe console window that appears every 30 minutes
- Remove title and freshness pre-filters (LinkedIn's alert filtering makes them redundant)

**Non-Goals:**
- Real-time alerting (daily email cadence is accepted)
- LinkedIn API integration (email parsing is sufficient)
- Log rotation or log size management

## Decisions

### Gmail access via IMAP (not Gmail API)
`imaplib` is in the Python standard library, requires no new OAuth setup, and works with the existing Gmail app password. Gmail API would require OAuth credentials and a separate registration. IMAP is simpler for a personal tool.

### Email search strategy: SINCE 7 days + Message-ID dedup in DB
Rather than relying on IMAP `\Seen` flags (which the user's own email reads would set, confusing the bot), each processed email's `Message-ID` header is stored in a `processed_emails` SQLite table. On each poll, IMAP searches for LinkedIn alert emails from the last 7 days; any whose `Message-ID` is already in the table is skipped. This is read/unread-independent.

### JD fetch order: after URL dedup, before Gemini
```
parse email → (title, company, location, url) → is_seen(url)? → skip
                                                      ↓ no
                                               fetch JD page
                                                      ↓
                                               Gemini filter
```
HTTP requests only happen for unseen jobs. On most 30-min runs after the daily email is already processed, the IMAP search returns 0 new emails and exits immediately.

### JD fetch: requests with browser headers, no login
LinkedIn job page JD body text is in static HTML (`<div class="show-more-less-html__markup">`). Fetch using `requests` with realistic `User-Agent` and `Accept-Language` headers. No session or cookie required for the JD body.

If the fetch returns < 200 chars (login wall or empty), the job proceeds to Gemini with snippet set to `"[limited info — JD not accessible]"`. The job is not skipped.

### Redirect URL resolution
LinkedIn alert email links use tracking URLs (`linkedin.com/comm/jobs/view/XXXXXXXX/`). `requests.get(..., allow_redirects=True)` follows the redirect to the canonical job URL (`linkedin.com/jobs/view/XXXXXXXX/`), which becomes the dedup key stored in `seen_jobs`.

### Task Scheduler: pythonw.exe direct, no cmd.exe
The current task runs `cmd.exe /c run_scout.bat`, which creates a visible console window on each 30-min invocation. The fix: re-register the task to execute `pythonw.exe` directly with `main.py --once` as the argument. Python's own stdout/stderr routing to `scout.log` (already in place) makes `cmd.exe` and the bat file unnecessary. `run_scout.bat` is deleted.

### Remove title and freshness pre-filters
LinkedIn's saved search alert already filters by role keyword and only sends alerts for active, recent postings. The title regex and `_POSTED_RE` freshness checks add no value and are removed along with `searcher.py` and `adzuna_searcher.py`.

## Risks / Trade-offs

**LinkedIn HTML structure changes** → The JD extractor targets `div.show-more-less-html__markup`. If LinkedIn restructures its job page, extraction silently returns short/empty text and jobs proceed with `[limited info]`. Mitigation: log when extracted content is short; maintainer can update the selector.

**Login wall rate variability** → LinkedIn's gating of unauthenticated requests is inconsistent. Some fetches return full JDs; others hit a login wall. Mitigation: `[limited info]` fallback ensures no jobs are silently dropped. The user can review `[limited info]` emails and decide if quality is acceptable.

**Daily cadence** → LinkedIn sends one alert email per day per saved search. job-scout processes it within 30 minutes of arrival. This is a safety-net posture, not real-time. Accepted by the user.

**Email format changes** → If LinkedIn restructures its alert email HTML, the parser breaks. Mitigation: log when 0 jobs are parsed from an email with known-LinkedIn origin.

## Migration Plan

1. Re-register Task Scheduler task (`pythonw.exe` direct, no bat file) — eliminates console window immediately
2. Implement `linkedin_email_source.py` and update `db.py`
3. Update `main.py` to use new source
4. Delete `searcher.py`, `adzuna_searcher.py`, `run_scout.bat`
5. Update `requirements.txt`
6. Smoke test: run `main.py --once` manually, verify emails processed and JD fetched
7. Remove unused credentials from `config.env` (TAVILY_API_KEY, ADZUNA_APP_ID, ADZUNA_APP_KEY)

Rollback: `searcher.py` and `adzuna_searcher.py` are in git history. `config.env` credentials remain until manually removed.

## Open Questions

- Which Gmail folder to search? INBOX assumed; LinkedIn alerts may be in a different label if the user has Gmail filters set up.
- Should processed emails be marked as read in Gmail as a secondary action (for cleanliness), or leave read/unread state entirely to the user?
