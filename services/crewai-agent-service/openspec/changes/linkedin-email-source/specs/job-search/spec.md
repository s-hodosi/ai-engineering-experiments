## REMOVED Requirements

### Requirement: Periodic job search via multiple sources
**Reason**: Replaced by LinkedIn email source. Tavily (Google-indexed LinkedIn scraping) and Adzuna (EU job aggregator) are removed. LinkedIn job alert emails are the new sole source, providing accurate server-rendered metadata without scraping.
**Migration**: `searcher.py` deleted. `linkedin_email_source.py` is the replacement.

### Requirement: Title pre-filter
**Reason**: LinkedIn's saved search alert already filters by role keyword. The title regex pre-filter is redundant and is removed.
**Migration**: No replacement. LinkedIn's alert filtering is the gate.

### Requirement: Snippet-based posting age filter
**Reason**: LinkedIn alert emails only contain active, recent postings. Age pre-filtering is no longer needed.
**Migration**: No replacement.

### Requirement: published_date metadata filter
**Reason**: Removed along with the Tavily source that provided this field.
**Migration**: No replacement.
