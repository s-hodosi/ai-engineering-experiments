## REMOVED Requirements

### Requirement: Adzuna API job search
**Reason**: Adzuna source replaced by LinkedIn email parsing. Adzuna produced too many irrelevant results for the user's target searches.
**Migration**: `adzuna_searcher.py` deleted. `ADZUNA_APP_ID` and `ADZUNA_APP_KEY` config keys no longer needed.

### Requirement: created-date-based freshness filter
**Reason**: Removed with the Adzuna source. LinkedIn alert emails handle freshness implicitly.
**Migration**: No replacement.
