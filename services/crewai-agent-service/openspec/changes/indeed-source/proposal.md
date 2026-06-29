## Why

Job Scout currently searches LinkedIn jobs via Tavily/Google, which has a 12–24 hour indexing lag — too slow for competitive applications where being in the first 10–20 applicants matters. Additionally, EMEA-anchored query keywords miss valid roles in UK, Gibraltar, and other EU countries where job descriptions use "work from anywhere" or regional language rather than "EMEA".

## What Changes

- Add **Indeed RSS** as a parallel job source alongside Tavily, reducing end-to-end latency to 1–3 hours
- Replace 8 EMEA/Europe/Budapest-variant Tavily query templates with 6 role-title-variant Indeed RSS queries using structured `l=Europe` and `l=Budapest` location parameters
- Remove the **location pre-filter** (regex check on title+content+url) — Indeed already filters by location server-side; let Gemini handle final location judgment
- Keep Tavily as a complementary fallback source (catches LinkedIn-only posts not cross-posted to Indeed)
- Change scheduler interval from **2 hours to 30 minutes**

## Capabilities

### New Capabilities
- `job-search-indeed`: Indeed RSS feed polling — role-title queries, Europe-wide coverage, structured pubDate freshness

### Modified Capabilities
- `job-search`: Adds a second source (Indeed), removes location pre-filter requirement, changes schedule interval from 2h to 30min

## Impact

- `services/job-scout/searcher.py` — add `indeed_search()` function (or new `indeed_searcher.py`)
- `services/job-scout/main.py` — combine results from both sources before dedup; change interval config default
- `services/job-scout/config.env` — add `SCHEDULE_INTERVAL_MINUTES` (replaces `SCHEDULE_INTERVAL_HOURS`)
- New dependency: `feedparser` (RSS parsing) or stdlib `xml.etree.ElementTree`
- No changes to `filter.py`, `db.py`, `notifier.py`, or `profile.md`
