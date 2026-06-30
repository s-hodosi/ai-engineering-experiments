## Purpose

~~Multi-source job search (Tavily + Adzuna) with title pre-filtering, feeding the relevance filter pipeline.~~

**Retired**: Replaced by LinkedIn email source. Tavily (Google-indexed LinkedIn scraping) and Adzuna are removed. LinkedIn job alert emails are the new sole source, providing accurate server-rendered metadata without scraping. `searcher.py` deleted.

The title pre-filter, snippet-based age filter, and `published_date` filter are also removed — LinkedIn's saved search alert handles keyword filtering, and alert emails only contain active recent postings.

## Requirements

_All requirements removed. This capability is retired. See `linkedin-email-source` spec._
