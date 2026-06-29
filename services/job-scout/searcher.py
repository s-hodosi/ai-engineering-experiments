import re
from datetime import datetime, timedelta, timezone
from tavily import TavilyClient

_QUERY_TEMPLATES = [
    'site:linkedin.com/jobs "engineering manager" remote EMEA',
    'site:linkedin.com/jobs "senior engineering manager" remote Europe',
    'site:linkedin.com/jobs "head of engineering" remote EMEA',
    'site:linkedin.com/jobs "director of engineering" remote Europe',
    'site:linkedin.com/jobs "engineering manager" Budapest hybrid',
    'site:linkedin.com/jobs "head of engineering" Budapest',
    'site:linkedin.com/jobs "team lead" engineering remote EMEA',
    'site:linkedin.com/jobs "team leader" engineering Budapest',
]

_TITLE_RE = re.compile(
    r'\b(engineering manager|senior engineering manager|head of engineering|'
    r'director of engineering|engineering director|head of software engineering|'
    r'team lead|team leader)\b',
    re.IGNORECASE,
)

# Matches: "2 days ago", "5 months ago", "Posted 3 weeks ago", "Reposted 1 day ago", etc.
_POSTED_RE = re.compile(
    r'(?:(?:Posted|Reposted)\s+)?(\d+)\s+(hour|day|week|month)s?\s+ago',
    re.IGNORECASE,
)

_DAYS_PER_UNIT = {"hour": 1/24, "day": 1, "week": 7, "month": 30}


def _parse_snippet_age_days(snippet: str) -> float | None:
    m = _POSTED_RE.search(snippet)
    if not m:
        return None
    amount = int(m.group(1))
    unit = m.group(2).lower()
    return amount * _DAYS_PER_UNIT.get(unit, 1)


def _is_fresh(result: dict, max_age_days: int, max_published_days: int) -> bool:
    snippet = result.get("content", "")

    if "no longer accepting" in snippet.lower():
        return False

    snippet_age = _parse_snippet_age_days(snippet)
    if snippet_age is not None:
        return snippet_age <= max_age_days

    published_date = result.get("published_date")
    if published_date:
        try:
            pub_dt = datetime.fromisoformat(published_date.replace("Z", "+00:00"))
            age_days = (datetime.now(timezone.utc) - pub_dt).days
            return age_days <= max_published_days
        except (ValueError, TypeError):
            pass

    return True  # age unknown — pass through


def _is_individual_job(url: str) -> bool:
    if "linkedin.com" in url:
        return "/jobs/view/" in url
    return True


def _passes_prefilter(result: dict, max_age_days: int, max_published_days: int) -> bool:
    url = result.get("url", "")
    title = result.get("title", "")
    if not _is_individual_job(url):
        return False
    if not _TITLE_RE.search(title):
        return False
    return _is_fresh(result, max_age_days, max_published_days)


def search(api_key: str, max_age_days: int = 3, max_published_days: int = 7) -> list[dict]:
    after_date = (datetime.now(timezone.utc) - timedelta(days=max_age_days)).strftime("%Y-%m-%d")
    client = TavilyClient(api_key=api_key)
    seen_urls: set[str] = set()
    results: list[dict] = []

    for template in _QUERY_TEMPLATES:
        query = f"{template} after:{after_date}"
        try:
            response = client.search(query, search_depth="advanced", max_results=10)
            for r in response.get("results", []):
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                if _passes_prefilter(r, max_age_days, max_published_days):
                    results.append({
                        "url": url,
                        "title": r.get("title", ""),
                        "snippet": r.get("content", ""),
                        "published_date": r.get("published_date"),
                    })
        except Exception as e:
            print(f"[searcher] Query failed ({query!r}): {e}")

    print(f"[searcher] {len(results)} jobs passed pre-filter (freshness: {max_age_days}d snippet / {max_published_days}d published)")
    return results
