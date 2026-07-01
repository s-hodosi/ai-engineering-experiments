import email
import imaplib
import re
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from db import is_email_processed, is_seen, mark_email_processed

_IMAP_HOST = "imap.gmail.com"
_LINKEDIN_FROM = "jobalerts-noreply@linkedin.com"
_LOOKBACK_DAYS = 7
_MIN_JD_LENGTH = 200

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


def _parse_jobs_from_email(html_body: str) -> list[dict]:
    soup = BeautifulSoup(html_body, "html.parser")

    # Collect all link texts per job_id — LinkedIn emails have 3 links per job:
    # 1. icon link (empty text), 2. rich card (title+company+location crammed), 3. title only
    raw: dict[str, dict] = {}
    for link in soup.find_all("a", href=True):
        href = link.get("href", "")
        m = re.search(r"/jobs/view/(\d+)", href)
        if not m:
            continue
        job_id = m.group(1)
        text = link.get_text(strip=True)
        if not text:
            continue
        if job_id not in raw:
            raw[job_id] = {"tracking_url": href, "texts": []}
        raw[job_id]["texts"].append(text)

    jobs = []
    for job_id, data in raw.items():
        texts = sorted(data["texts"], key=len)
        title = texts[0]  # shortest = clean title only
        if len(title) < 3:
            continue

        canonical_url = f"https://www.linkedin.com/jobs/view/{job_id}/"
        company = ""
        location = ""

        if len(texts) > 1:
            # Longest text = rich card: "{title}{company} · {location}{noise}"
            rich = texts[-1]
            if rich.startswith(title):
                remainder = rich[len(title):]
                parts = remainder.split(" · ")
                company = parts[0].strip()
                if len(parts) > 1:
                    loc_raw = parts[1]
                    # Strip trailing noise: applicant counts, "Actively recruiting", "Easy Apply", etc.
                    location = re.split(r"\s*(?:\d+\s|\(On-site\)|\(Hybrid\)|\(Remote\)|Actively|Easy|Fast)", loc_raw)[0].strip()
                    # Re-attach work type if it was in parens at the end of location
                    wt = re.search(r"(\(On-site\)|\(Hybrid\)|\(Remote\))", loc_raw)
                    if wt:
                        location = location.rstrip(" ,") + " " + wt.group(1)

        jobs.append({
            "title": title,
            "company": company,
            "location": location,
            "canonical_url": canonical_url,
            "tracking_url": data["tracking_url"],
        })

    return jobs


def _fetch_jd(canonical_url: str) -> str:
    m = re.search(r"/jobs/view/(\d+)", canonical_url)
    if not m:
        return "[limited info — invalid URL]"

    job_id = m.group(1)
    guest_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"

    try:
        resp = requests.get(guest_url, headers=_HEADERS, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")

        jd_div = (
            soup.find("div", class_=re.compile(r"show-more-less-html__markup"))
            or soup.find("div", class_=re.compile(r"description__text"))
            or soup.find("section", class_=re.compile(r"description"))
        )

        text = jd_div.get_text(separator="\n", strip=True) if jd_div else ""

        if len(text) >= _MIN_JD_LENGTH:
            return text[:3000]
        return "[limited info — JD not accessible]"

    except Exception as e:
        print(f"[linkedin] JD fetch failed for {canonical_url}: {e}")
        return "[limited info — fetch failed]"


def fetch_jobs(gmail_address: str, app_password: str, db_path: str) -> list[dict]:
    try:
        mail = imaplib.IMAP4_SSL(_IMAP_HOST)
        mail.login(gmail_address, app_password)
        mail.select("INBOX")
    except Exception as e:
        print(f"[linkedin] IMAP connection failed: {e}")
        return []

    since_date = (datetime.now() - timedelta(days=_LOOKBACK_DAYS)).strftime("%d-%b-%Y")
    try:
        _, raw_ids = mail.search(None, f'FROM "{_LINKEDIN_FROM}" SINCE "{since_date}"')
        msg_ids = raw_ids[0].split()
    except Exception as e:
        print(f"[linkedin] IMAP search failed: {e}")
        mail.logout()
        return []

    print(f"[linkedin] {len(msg_ids)} LinkedIn alert emails found in last {_LOOKBACK_DAYS}d")

    results: list[dict] = []
    seen_this_run: set[str] = set()

    for msg_id_bytes in msg_ids:
        try:
            _, msg_data = mail.fetch(msg_id_bytes, "(RFC822)")
            msg = email.message_from_bytes(msg_data[0][1])
        except Exception as e:
            print(f"[linkedin] Failed to fetch email: {e}")
            continue

        message_id = msg.get("Message-ID", "").strip()
        if not message_id or is_email_processed(message_id, db_path):
            continue

        html_body = _get_html_body(msg)
        if not html_body:
            print(f"[linkedin] No HTML body in email, skipping")
            mark_email_processed(message_id, db_path)
            continue

        parsed = _parse_jobs_from_email(html_body)
        print(f"[linkedin] Email parsed: {len(parsed)} jobs found")

        if not parsed:
            mark_email_processed(message_id, db_path)
            continue

        for job in parsed:
            canonical_url = job["canonical_url"]
            if canonical_url in seen_this_run or is_seen(canonical_url, db_path):
                continue
            seen_this_run.add(canonical_url)

            snippet = _fetch_jd(canonical_url)
            time.sleep(1)

            results.append({
                "url": canonical_url,
                "title": job["title"],
                "company": job["company"],
                "location": job["location"],
                "snippet": snippet,
                "source": "linkedin-email",
            })

        mark_email_processed(message_id, db_path)

    mail.logout()
    print(f"[linkedin] {len(results)} new jobs to evaluate")
    return results
