import html
import json
import re
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

_ADZUNA_BASE = "https://api.adzuna.com/v1/api/jobs"

# Countries Adzuna supports in Europe/UK (Hungary not available — covered by Tavily)
_COUNTRIES = ["gb", "at", "de", "fr", "it", "nl", "pl"]

_ROLES = [
    "head of engineering",
    "engineering manager",
    "senior engineering manager",
    "director of engineering",
    "head of software engineering",
]

_TITLE_RE = re.compile(
    r'\b(engineering manager|senior engineering manager|head of engineering|'
    r'director of engineering|engineering director|head of software engineering|'
    r'team lead|team leader)\b',
    re.IGNORECASE,
)

_HTML_TAG_RE = re.compile(r'<[^>]+>')


def _strip_html(text: str) -> str:
    return html.unescape(_HTML_TAG_RE.sub('', text)).strip()


def search(app_id: str, app_key: str, max_age_days: int = 3) -> list[dict]:
    if not app_id or not app_key:
        print("[adzuna] Skipping — ADZUNA_APP_ID / ADZUNA_APP_KEY not set")
        return []

    cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
    seen_urls: set[str] = set()
    results: list[dict] = []

    for country in _COUNTRIES:
        for role in _ROLES:
            query_url = (
                f"{_ADZUNA_BASE}/{country}/search/1"
                f"?app_id={app_id}&app_key={app_key}"
                f"&what={urllib.parse.quote(role)}"
                f"&results_per_page=20"
                f"&sort_by=date"
                f"&max_days_old={max_age_days}"
                f"&content-type=application%2Fjson"
            )
            try:
                req = urllib.request.Request(query_url)
                with urllib.request.urlopen(req, timeout=15) as resp:
                    data = json.loads(resp.read())

                for item in data.get("results", []):
                    job_url = item.get("redirect_url", "")
                    if not job_url or job_url in seen_urls:
                        continue
                    seen_urls.add(job_url)

                    title = item.get("title", "")
                    if not _TITLE_RE.search(title):
                        continue

                    pub_dt = None
                    created_str = item.get("created", "")
                    if created_str:
                        try:
                            pub_dt = datetime.fromisoformat(created_str.replace("Z", "+00:00"))
                            if pub_dt < cutoff:
                                continue
                        except (ValueError, TypeError):
                            pass

                    company = item.get("company", {}).get("display_name", "")
                    snippet = _strip_html(item.get("description", ""))[:500]

                    results.append({
                        "url": job_url,
                        "title": title,
                        "company": company,
                        "snippet": snippet,
                        "published_date": pub_dt.isoformat() if pub_dt else None,
                        "source": "adzuna",
                    })

            except Exception as e:
                print(f"[adzuna] Query failed ({role!r} / {country!r}): {e}")

    print(f"[adzuna] {len(results)} jobs passed pre-filter")
    return results
