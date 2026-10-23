import sqlite3
from datetime import datetime, timezone


def init_db(path: str):
    with sqlite3.connect(path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS seen_jobs (
                url      TEXT PRIMARY KEY,
                title    TEXT,
                company  TEXT,
                verdict  TEXT,
                fetched_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS processed_emails (
                message_id   TEXT PRIMARY KEY,
                processed_at TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pending_jobs (
                url               TEXT PRIMARY KEY,
                title             TEXT,
                company           TEXT,
                location          TEXT,
                snippet           TEXT,
                attempts          INTEGER NOT NULL DEFAULT 0,
                first_deferred_at TEXT,
                last_error        TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS service_state (
                key   TEXT PRIMARY KEY,
                value TEXT
            )
        """)
        conn.commit()


def is_seen(url: str, path: str) -> bool:
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT 1 FROM seen_jobs WHERE url = ?", (url,)).fetchone()
    return row is not None


def mark_seen(url: str, title: str, company: str, verdict: str, path: str):
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO seen_jobs (url, title, company, verdict, fetched_at) VALUES (?, ?, ?, ?, ?)",
            (url, title, company, verdict, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def is_email_processed(message_id: str, path: str) -> bool:
    with sqlite3.connect(path) as conn:
        row = conn.execute(
            "SELECT 1 FROM processed_emails WHERE message_id = ?", (message_id,)
        ).fetchone()
    return row is not None


def mark_email_processed(message_id: str, path: str):
    with sqlite3.connect(path) as conn:
        conn.execute(
            "INSERT OR IGNORE INTO processed_emails (message_id, processed_at) VALUES (?, ?)",
            (message_id, datetime.now(timezone.utc).isoformat()),
        )
        conn.commit()


def defer_job(job: dict, last_error: str, count_attempt: bool, path: str) -> int:
    """Upsert a job into pending_jobs; returns its attempt count afterwards."""
    increment = 1 if count_attempt else 0
    with sqlite3.connect(path) as conn:
        conn.execute(
            """
            INSERT INTO pending_jobs
                (url, title, company, location, snippet, attempts, first_deferred_at, last_error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(url) DO UPDATE SET
                attempts = attempts + excluded.attempts,
                last_error = excluded.last_error
            """,
            (
                job["url"], job.get("title", ""), job.get("company", ""),
                job.get("location", ""), job.get("snippet", ""), increment,
                datetime.now(timezone.utc).isoformat(), last_error,
            ),
        )
        conn.commit()
        row = conn.execute("SELECT attempts FROM pending_jobs WHERE url = ?", (job["url"],)).fetchone()
    return row[0]


def load_pending(path: str) -> list[dict]:
    with sqlite3.connect(path) as conn:
        # Guard against a crash between mark_seen and remove_pending.
        conn.execute("DELETE FROM pending_jobs WHERE url IN (SELECT url FROM seen_jobs)")
        conn.commit()
        rows = conn.execute(
            "SELECT url, title, company, location, snippet FROM pending_jobs ORDER BY first_deferred_at"
        ).fetchall()
    return [
        {"url": url, "title": title, "company": company, "location": location,
         "snippet": snippet, "source": "pending"}
        for url, title, company, location, snippet in rows
    ]


def remove_pending(url: str, path: str):
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM pending_jobs WHERE url = ?", (url,))
        conn.commit()


def is_pending(url: str, path: str) -> bool:
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT 1 FROM pending_jobs WHERE url = ?", (url,)).fetchone()
    return row is not None


def count_pending(path: str) -> int:
    with sqlite3.connect(path) as conn:
        return conn.execute("SELECT COUNT(*) FROM pending_jobs").fetchone()[0]


def get_state(key: str, path: str) -> str | None:
    with sqlite3.connect(path) as conn:
        row = conn.execute("SELECT value FROM service_state WHERE key = ?", (key,)).fetchone()
    return row[0] if row else None


def set_state(key: str, value: str | None, path: str):
    with sqlite3.connect(path) as conn:
        if value is None:
            conn.execute("DELETE FROM service_state WHERE key = ?", (key,))
        else:
            conn.execute(
                "INSERT INTO service_state (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, value),
            )
        conn.commit()
