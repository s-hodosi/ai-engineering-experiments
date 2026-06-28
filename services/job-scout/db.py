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
