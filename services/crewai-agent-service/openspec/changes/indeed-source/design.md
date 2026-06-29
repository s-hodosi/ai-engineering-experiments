## Context

Job Scout's current sole source is Tavily, which searches Google's index for `site:linkedin.com/jobs` results. Google's crawl lag for LinkedIn job pages is 12–24 hours, making the service too slow for competitive applications. Additionally, queries are anchored to EMEA/Europe/Budapest keywords, missing legitimate EU roles where the job description uses "work from anywhere" or country-specific language.

Indeed is a major job aggregator that crawls LinkedIn, company career pages, and direct employer postings. Its index is refreshed within 1–3 hours of posting. It also provides structured RSS feeds with no authentication required, a `pubDate` field that reliably reflects the actual post time, and server-side location filtering (`l=Europe`) that removes the need for client-side location regex.

## Goals / Non-Goals

**Goals:**
- Add Indeed RSS as a parallel source, reducing end-to-end latency to 1–3 hours
- Cover all EU countries without per-country query variants
- Remove the location pre-filter, delegating location judgment to Gemini
- Reduce polling interval from 2h to 30min

**Non-Goals:**
- Replace Tavily entirely (it stays as a complementary fallback)
- Scrape LinkedIn directly
- Parse LinkedIn's email alert format
- Change the Gemini filter, deduplication, or notification layers

## Decisions

### 1. feedparser vs xml.etree for RSS parsing
**Decision:** Use `feedparser`.

`feedparser` handles RSS date parsing, encoding quirks, and malformed feeds gracefully. `xml.etree` would require manual date parsing and is fragile against encoding issues. `feedparser` is a well-maintained, single-purpose library with no transitive dependencies.

### 2. New file vs extending searcher.py
**Decision:** Add `indeed_searcher.py` as a separate module.

`searcher.py` contains Tavily-specific logic (TavilyClient, `after:` query construction, `content` field). Indeed RSS is structurally different (HTTP fetch, XML parse, `pubDate` field). Keeping them separate avoids a tangled abstraction and makes each independently testable. `main.py` merges results from both before deduplication.

### 3. Remove location pre-filter vs make it source-aware
**Decision:** Remove the location pre-filter entirely across all sources.

Indeed already performs location filtering server-side (`l=Europe`). For Tavily, the location regex was imprecise anyway (missed Gibraltar, UK "East European" language). Gemini receives the full job title and snippet and is well-suited to reject irrelevant locations. The volume of results that pass the title pre-filter is small enough that a few extra LLM calls per run are acceptable.

### 4. Indeed query design
**Decision:** 6 role-title queries with `l=Europe` plus 2 with `l=Budapest`, `fromage=1`, `sort=date`.

This covers all target role variants across the EU in one location parameter rather than per-country templates. Budapest variants are kept for hybrid roles that may not appear in Europe-wide results. `fromage=1` limits to the last 24 hours server-side; the local `pubDate` freshness filter applies the tighter 3-day window.

### 5. Scheduler interval
**Decision:** Change from hours to minutes; default 30 minutes.

`SCHEDULE_INTERVAL_HOURS` is replaced by `SCHEDULE_INTERVAL_MINUTES`. Indeed RSS is cheap to fetch (lightweight XML, no auth, no per-call cost). 30 minutes means worst-case latency of 30min (poll) + 1–3h (Indeed index) = ~3.5h end-to-end, which meets the target.

## Risks / Trade-offs

- **Indeed coverage gap** → Some LinkedIn-only posts (not cross-posted to Indeed) will still have 24h lag via Tavily. Mitigation: keep Tavily running in parallel.
- **Indeed RSS format changes** → Indeed could alter their RSS schema or URL structure. Mitigation: `feedparser` is tolerant; the freshness and title filters degrade gracefully if fields are missing.
- **feedparser new dependency** → Small, stable library with no transitive deps. Low risk.
- **More LLM calls per run** → Removing location pre-filter may add 2–5 extra Gemini calls per run. At Gemini Flash pricing this is negligible.
- **Duplicate URLs across sources** → Indeed and Tavily may return the same job via different URLs (LinkedIn URL vs Indeed redirect). Mitigation: dedup by URL catches same-source duplicates; cross-source duplicates for the same job go through LLM twice but `mark_seen` prevents double-email.

## Migration Plan

1. Install `feedparser` (`pip install feedparser`, add to requirements)
2. Deploy new `indeed_searcher.py`
3. Update `main.py` to merge sources and use `SCHEDULE_INTERVAL_MINUTES`
4. Update `config.env` — replace `SCHEDULE_INTERVAL_HOURS=2` with `SCHEDULE_INTERVAL_MINUTES=30`
5. Existing `jobs.db` and all other config keys are unchanged

No rollback complexity — reverting means removing the Indeed source from `main.py` and restoring the interval key.
