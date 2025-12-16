import os
import json
import sqlite3
from datetime import datetime, timezone
from typing import Any, Dict, List

DEFAULT_DB_PATH = os.getenv("DEEPSYMBOL_DB_PATH", "data/deepsymbol.db")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DEFAULT_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    conn = _connect()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS interpretations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                objects_json TEXT NOT NULL,
                interpretation TEXT NOT NULL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()


def save_interpretation(objects: List[str], interpretation: str) -> int:
    conn = _connect()
    try:
        created_at = datetime.now(timezone.utc).isoformat()
        objects_json = json.dumps(objects, ensure_ascii=False)
        cur = conn.execute(
            """
            INSERT INTO interpretations (created_at, objects_json, interpretation)
            VALUES (?, ?, ?)
            """,
            (created_at, objects_json, interpretation),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


def get_history(limit: int = 20) -> List[Dict[str, Any]]:
    conn = _connect()
    try:
        cur = conn.execute(
            """
            SELECT id, created_at, objects_json, interpretation
            FROM interpretations
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
        out = []
        for r in rows:
            out.append(
                {
                    "id": r["id"],
                    "created_at": r["created_at"],
                    "objects": json.loads(r["objects_json"]),
                    "interpretation": r["interpretation"],
                }
            )
        return out
    finally:
        conn.close()

