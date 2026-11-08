from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_DIR = Path(__file__).resolve().parent.parent / "data"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "evaluations.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS evaluations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            summary TEXT,
            score REAL NOT NULL,
            recommendation TEXT NOT NULL,
            raw_scores TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


def save_evaluation(result: dict[str, Any]) -> int:
    initialize_database()
    conn = get_connection()
    created_at = datetime.now(timezone.utc).isoformat()
    cursor = conn.execute(
        """
        INSERT INTO evaluations (
            title, company, location, summary, score, recommendation, raw_scores, created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.get("title", "Untitled"),
            result.get("company", "Unknown"),
            result.get("location", "Unknown"),
            result.get("summary", ""),
            float(result.get("score", 0)),
            result.get("recommendation", "Low fit"),
            json.dumps(result.get("raw_scores", {})),
            created_at,
        ),
    )
    conn.commit()
    evaluation_id = int(cursor.lastrowid)
    conn.close()
    return evaluation_id


def list_evaluations() -> list[dict[str, Any]]:
    initialize_database()
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM evaluations ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [serialize_evaluation(row) for row in rows]


def get_evaluation(evaluation_id: int) -> dict[str, Any] | None:
    initialize_database()
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM evaluations WHERE id = ?",
        (evaluation_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    return serialize_evaluation(row)


def serialize_evaluation(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "id": int(row["id"]),
        "title": row["title"],
        "company": row["company"],
        "location": row["location"],
        "summary": row["summary"],
        "score": float(row["score"]),
        "recommendation": row["recommendation"],
        "raw_scores": json.loads(row["raw_scores"]),
        "created_at": row["created_at"],
    }
