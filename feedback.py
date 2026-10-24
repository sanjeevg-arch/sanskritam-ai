"""Local SQLite feedback store. Do not store API keys or user identity."""
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB = Path(__file__).parent / 'feedback.sqlite3'

def save_feedback(source, direction, rating, category, comment):
    with sqlite3.connect(DB, timeout=10) as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_utc TEXT NOT NULL,
            source TEXT NOT NULL,
            direction TEXT NOT NULL,
            rating TEXT NOT NULL,
            category TEXT NOT NULL,
            comment TEXT NOT NULL
        )""")
        conn.execute('INSERT INTO feedback (created_utc,source,direction,rating,category,comment) VALUES (?,?,?,?,?,?)',
                     (datetime.now(timezone.utc).isoformat(),source[:1600],direction[:50],rating[:30],category[:50],comment[:1000]))
