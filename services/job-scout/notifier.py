import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_ALERT_TEXT = {
    "billing": (
        "Gemini prepay credits are depleted. Top up (or enable auto-reload) at "
        "https://aistudio.google.com/ — pending jobs will be evaluated automatically "
        "on the next run after that."
    ),
    "auth": "The Gemini API key was rejected. Check GOOGLE_API_KEY in config.env.",
}

_LOCATION_KEYWORDS =["Remote", "Budapest", "Hybrid", "EMEA", "Europe", "Hungary", "UK"]


def _extract_company(title: str) -> str:
    for sep in [" at ", " - ", " | "]:
        if sep.lower() in title.lower():
            parts = title.split(sep, 1)
            if len(parts) == 2 and parts[1].strip():
                return parts[1].strip()
    return ""


def _extract_location(job: dict) -> str:
    text = job.get("title", "") + " " + job.get("snippet", "")
    for kw in _LOCATION_KEYWORDS:
        if kw.lower() in text.lower():
            return kw
    return "Location unclear"


def _clean_title(title: str) -> str:
    for sep in [" at ", " - ", " | "]:
        if sep.lower() in title.lower():
            return title.split(sep, 1)[0].strip()
    return title.strip()


def _render_entry(job: dict, scope: str) -> str:
    title = job.get("title", "Unknown Role")
    company = job.get("company") or _extract_company(title) or "Unknown Company"
    location = job.get("location") or _extract_location(job)
    role = _clean_title(title)

    return f"{role} – {company} · {location}\n\n{scope}\n\n{job['url']}\n"


class Notifier:
    def __init__(self, gmail_address: str, app_password: str):
        self.gmail_address = gmail_address
        self.app_password = app_password

    def send_digest(self, entries: list[tuple[dict, str, str]]):
        if not entries:
            return

        n = len(entries)
        subject = f"[Job Scout] {n} new match{'es' if n != 1 else ''}"

        separator = "\n" + ("=" * 40) + "\n\n"
        body = separator.join(
            _render_entry(job, scope) for job, _verdict, scope in entries
        )

        self._send(subject, body)
        print(f"[notifier] Sent digest: {subject}")

    def send_alert(self, reason: str, pending_count: int):
        subject = f"[Job Scout] Filter down: {reason}"
        explanation = _ALERT_TEXT.get(reason, "The relevance filter is failing. Check scout.log.")
        body = f"{explanation}\n\n{pending_count} job(s) pending.\n"
        self._send(subject, body)
        print(f"[notifier] Sent alert: {subject}")

    def _send(self, subject: str, body: str):
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = self.gmail_address
        msg["To"] = self.gmail_address
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(self.gmail_address, self.app_password)
            smtp.sendmail(self.gmail_address, self.gmail_address, msg.as_string())
