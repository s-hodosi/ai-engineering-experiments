import re
from tavily import TavilyClient

QUERIES = [
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

_LOCATION_RE = re.compile(
    r'\b(remote|budapest|emea|europe|hungary|hybrid|eu\b)',
    re.IGNORECASE,
)


def _is_individual_job(url: str) -> bool:
    """Reject LinkedIn search/list pages — only keep individual job postings."""
    if "linkedin.com" in url:
        return "/jobs/view/" in url
    return True


def _passes_prefilter(result: dict) -> bool:
    title = result.get("title", "")
    content = result.get("content", "")
    url = result.get("url", "")
    if not _is_individual_job(url):
        return False
    if not _TITLE_RE.search(title):
        return False
    location_text = title + " " + content + " " + url
    return bool(_LOCATION_RE.search(location_text))


def search(api_key: str) -> list[dict]:
    client = TavilyClient(api_key=api_key)
    seen_urls: set[str] = set()
    results: list[dict] = []

    for query in QUERIES:
        try:
            response = client.search(query, search_depth="advanced", max_results=10)
            for r in response.get("results", []):
                url = r.get("url", "")
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                if _passes_prefilter(r):
                    results.append({
                        "url": url,
                        "title": r.get("title", ""),
                        "snippet": r.get("content", ""),
                    })
        except Exception as e:
            print(f"[searcher] Query failed ({query!r}): {e}")

    print(f"[searcher] {len(results)} jobs passed pre-filter across all queries")
    return results
