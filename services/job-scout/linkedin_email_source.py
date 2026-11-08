import email
import imaplib
import os
import re
import time
from datetime import datetime, timedelta
from typing import NamedTuple

import requests
from bs4 import BeautifulSoup

from db import is_email_processed, is_pending, is_seen, mark_email_processed

_IMAP_HOST = "imap.gmail.com"
_LINKEDIN_FROM = "jobalerts-noreply@linkedin.com"
_LOOKBACK_DAYS = 7
_MIN_JD_LENGTH = 200

# Transient JD fetch failures (LinkedIn intermittently serves pages without the
# description) are retried after these waits, in seconds.
_RETRY_WAITS = (3, 10)
_MAX_RETRY_AFTER = 30
_DEBUG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "debug", "jd_failures")
_MAX_CAPTURES = 50

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xhtml+xml;q=0.9,*/*;q=0.8",
}


def _get_html_body(msg) -> str:
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/html":
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="replace")
    elif msg.get_content_type() == "text/html":
        charset = msg.get_content_charset() or "utf-8"
        return msg.get_payload(decode=True).decode(charset, errors="replace")
    return ""


_JOB_VIEW_RE = re.compile(r"/jobs/view/(\d+)")
_WORK_TYPE = r"\(On-site\)|\(Hybrid\)|\(Remote\)"
_LOCATION_NOISE_RE = re.compile(rf"\s*(?:\d+\s|{_WORK_TYPE}|Actively|Easy|Fast)")
_WORK_TYPE_RE = re.compile(rf"({_WORK_TYPE})")


def _collect_link_texts(soup) -> dict[str, dict]:
    """Group non-empty link texts by job_id.

    LinkedIn emails have 3 links per job: 1. icon link (empty text),
    2. rich card (title+company+location crammed), 3. title only.
    """
    raw: dict[str, dict] = {}
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        m = _JOB_VIEW_RE.search(href)
        text = link.get_text(strip=True)
        if not m or not text:
            continue
        entry = raw.setdefault(m.group(1), {"tracking_url": href, "texts": []})
        entry["texts"].append(text)
    return raw


def _clean_location(loc_raw: str) -> str:
    # Strip trailing noise: applicant counts, "Actively recruiting", "Easy Apply", etc.
    location = _LOCATION_NOISE_RE.split(loc_raw)[0].strip()
    # Re-attach work type if it was in parens in the raw location
    wt = _WORK_TYPE_RE.search(loc_raw)
    if not wt:
        return location
    return location.rstrip(" ,") + " " + wt.group(1)


def _parse_rich_card(title: str, rich: str) -> tuple[str, str]:
    """Split a rich card "{title}{company} · {location}{noise}" into (company, location)."""
    if not rich.startswith(title):
        return "", ""
    parts = rich[len(title):].split(" · ")
    company = parts[0].strip()
    location = _clean_location(parts[1]) if len(parts) > 1 else ""
    return company, location


def _build_job(job_id: str, data: dict) -> dict | None:
    texts = sorted(data["texts"], key=len)
    title = texts[0]  # shortest = clean title only
    if len(title) < 3:
        return None
    # Longest text = rich card (only when there is more than one text)
    company, location = _parse_rich_card(title, texts[-1]) if len(texts) > 1 else ("", "")
    return {
        "title": title,
        "company": company,
        "location": location,
        "canonical_url": f"https://www.linkedin.com/jobs/view/{job_id}/",
        "tracking_url": data["tracking_url"],
    }


def _parse_jobs_from_email(html_body: str) -> list[dict]:
    soup = BeautifulSoup(html_body, "html.parser")
    jobs = (_build_job(job_id, data) for job_id, data in _collect_link_texts(soup).items())
    return [job for job in jobs if job is not None]


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


class _JdAttempt(NamedTuple):
    outcome: str
    text: str
    resp: requests.Response | None


def _fetch_jd_once(guest_url: str) -> _JdAttempt:
    """Single attempt; see design.md for outcomes."""
    try:
        resp = requests.get(guest_url, headers=_HEADERS, timeout=15)
    except Exception as e:
        return _JdAttempt("error", str(e), None)

    if resp.status_code in (404, 410):
        return _JdAttempt("gone", "", resp)
    if resp.status_code != 200:
        return _JdAttempt(f"http_{resp.status_code}", "", resp)

    soup = BeautifulSoup(resp.text, "html.parser")
    jd_div = (
        soup.find("div", class_=re.compile(r"show-more-less-html__markup"))
        or soup.find("div", class_=re.compile(r"description__text"))
        or soup.find("section", class_=re.compile(r"description"))
    )
    if not jd_div:
        return _JdAttempt("no_jd", "", resp)

    text = jd_div.get_text(separator="\n", strip=True)
    if len(text) < _MIN_JD_LENGTH:
        return _JdAttempt("short", text, resp)
    return _JdAttempt("ok", text, resp)


def _retry_wait(resp, default: int) -> int:
    retry_after = resp.headers.get("Retry-After", "") if resp is not None else ""
    if retry_after.strip().isdigit():
        return min(int(retry_after), _MAX_RETRY_AFTER)
    return default


def _save_failure(job_id: str, resp):
    try:
        os.makedirs(_DEBUG_DIR, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        path = os.path.join(_DEBUG_DIR, f"{job_id}_{stamp}.html")
        headers = "\n".join(f"{k}: {v}" for k, v in resp.headers.items()).replace("--", "- -")
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"<!--\nstatus: {resp.status_code}\n{headers}\n-->\n{resp.text}")

        captures = sorted(
            (os.path.join(_DEBUG_DIR, n) for n in os.listdir(_DEBUG_DIR) if n.endswith(".html")),
            key=os.path.getmtime,
        )
        for old in captures[:-_MAX_CAPTURES]:
            os.remove(old)
    except Exception as e:
        print(f"[linkedin] {_now()} Could not save failed response for job {job_id}: {e}")


_ATTEMPTS = len(_RETRY_WAITS) + 1
# Outcomes that retrying cannot fix.
_PERMANENT_OUTCOMES = ("gone", "short")


def _log_attempt_failure(job_id: str, attempt: int, result: _JdAttempt) -> None:
    resp = result.resp
    status = resp.status_code if resp is not None else "-"
    length = len(resp.text) if resp is not None else 0
    detail = f" ({result.text})" if result.outcome == "error" else ""
    print(
        f"[linkedin] {_now()} JD fetch attempt {attempt}/{_ATTEMPTS} failed for job {job_id}: "
        f"status={status} outcome={result.outcome} length={length}{detail}"
    )


def _log_recovery(job_id: str, attempt: int) -> None:
    if attempt > 1:
        print(f"[linkedin] {_now()} JD fetch recovered for job {job_id} on attempt {attempt}/{_ATTEMPTS}")


def _should_retry(outcome: str, attempt: int) -> bool:
    return outcome not in _PERMANENT_OUTCOMES and attempt < _ATTEMPTS


def _fetch_jd_with_retries(job_id: str) -> tuple[_JdAttempt, int]:
    """Returns the last attempt's result and how many attempts were made."""
    guest_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
    for attempt in range(1, _ATTEMPTS + 1):
        result = _fetch_jd_once(guest_url)
        if result.outcome == "ok":
            _log_recovery(job_id, attempt)
            break
        _log_attempt_failure(job_id, attempt, result)
        if not _should_retry(result.outcome, attempt):
            break
        time.sleep(_retry_wait(result.resp, _RETRY_WAITS[attempt - 1]))
    return result, attempt


def _report_give_up(job_id: str, attempt: int, result: _JdAttempt) -> None:
    # A short JD is a real (if thin) page, not a failure worth capturing.
    if result.outcome == "short":
        return
    print(f"[linkedin] {_now()} JD fetch gave up for job {job_id} after {attempt} attempt(s): {result.outcome}")
    if result.resp is not None:
        _save_failure(job_id, result.resp)


def _limited_info(outcome: str) -> str:
    if outcome == "error" or outcome.startswith("http_"):
        return "[limited info — fetch failed]"
    return "[limited info — JD not accessible]"


def _fetch_jd(canonical_url: str) -> str:
    m = _JOB_VIEW_RE.search(canonical_url)
    if not m:
        return "[limited info — invalid URL]"

    job_id = m.group(1)
    result, attempt = _fetch_jd_with_retries(job_id)
    if result.outcome == "ok":
        return result.text[:3000]

    _report_give_up(job_id, attempt, result)
    return _limited_info(result.outcome)


def _connect(gmail_address: str, app_password: str):
    try:
        mail = imaplib.IMAP4_SSL(_IMAP_HOST)
        mail.login(gmail_address, app_password)
        mail.select("INBOX")
        return mail
    except Exception as e:
        print(f"[linkedin] IMAP connection failed: {e}")
        return None


def _search_alert_ids(mail) -> list[bytes] | None:
    since_date = (datetime.now() - timedelta(days=_LOOKBACK_DAYS)).strftime("%d-%b-%Y")
    try:
        _, raw_ids = mail.search(None, f'FROM "{_LINKEDIN_FROM}" SINCE "{since_date}"')
        return raw_ids[0].split()
    except Exception as e:
        print(f"[linkedin] IMAP search failed: {e}")
        return None


def _fetch_message(mail, msg_id_bytes: bytes):
    try:
        _, msg_data = mail.fetch(msg_id_bytes, "(RFC822)")
        return email.message_from_bytes(msg_data[0][1])
    except Exception as e:
        print(f"[linkedin] Failed to fetch email: {e}")
        return None


def _is_known(canonical_url: str, db_path: str, seen_this_run: set[str]) -> bool:
    if canonical_url in seen_this_run:
        return True
    return is_seen(canonical_url, db_path) or is_pending(canonical_url, db_path)


def _to_candidate(job: dict) -> dict:
    snippet = _fetch_jd(job["canonical_url"])
    time.sleep(1)
    return {
        "url": job["canonical_url"],
        "title": job["title"],
        "company": job["company"],
        "location": job["location"],
        "snippet": snippet,
        "source": "linkedin-email",
    }


def _new_jobs_from_body(html_body: str, db_path: str, seen_this_run: set[str]) -> list[dict]:
    if not html_body:
        print("[linkedin] No HTML body in email, skipping")
        return []

    parsed = _parse_jobs_from_email(html_body)
    print(f"[linkedin] Email parsed: {len(parsed)} jobs found")

    candidates = []
    for job in parsed:
        if _is_known(job["canonical_url"], db_path, seen_this_run):
            continue
        seen_this_run.add(job["canonical_url"])
        candidates.append(_to_candidate(job))
    return candidates


def _jobs_from_message(msg, db_path: str, seen_this_run: set[str]) -> list[dict]:
    message_id = msg.get("Message-ID", "").strip()
    if not message_id or is_email_processed(message_id, db_path):
        return []
    candidates = _new_jobs_from_body(_get_html_body(msg), db_path, seen_this_run)
    mark_email_processed(message_id, db_path)
    return candidates


def fetch_jobs(gmail_address: str, app_password: str, db_path: str) -> list[dict]:
    mail = _connect(gmail_address, app_password)
    if mail is None:
        return []

    msg_ids = _search_alert_ids(mail)
    if msg_ids is None:
        mail.logout()
        return []

    print(f"[linkedin] {len(msg_ids)} LinkedIn alert emails found in last {_LOOKBACK_DAYS}d")

    results: list[dict] = []
    seen_this_run: set[str] = set()
    for msg_id_bytes in msg_ids:
        msg = _fetch_message(mail, msg_id_bytes)
        if msg is not None:
            results.extend(_jobs_from_message(msg, db_path, seen_this_run))

    mail.logout()
    print(f"[linkedin] {len(results)} new jobs to evaluate")
    return results
