import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

_LOCATION_KEYWORDS = ["Remote", "Budapest", "Hybrid", "EMEA", "Europe", "Hungary", "UK"]


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


class Notifier:
    def __init__(self, gmail_address: str, app_password: str):
        self.gmail_address = gmail_address
        self.app_password = app_password

    def send(self, job: dict, verdict: str, explanation: str):
        title = job.get("title", "Unknown Role")
        company = job.get("company") or _extract_company(title) or "Unknown Company"
        location = job.get("location") or _extract_location(job)
        role = _clean_title(title)

        subject = f"[Job Scout] {role} – {company} ({location})"

        body = (
            f"{verdict}\n\n"
            f"{explanation}\n\n"
            f"---\n"
            f"Role:    {title}\n"
            f"URL:     {job['url']}\n"
        )

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

        print(f"[notifier] Sent: {subject}")
