import sqlite3
from pathlib import Path

DB_PATH = Path("data/app.db")


def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_conn() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS guests(
            guest_id TEXT PRIMARY KEY,
            uses INTEGER DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS history(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            mode TEXT, input TEXT, length TEXT, style TEXT,
            report TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        try:
            c.execute("ALTER TABLE history ADD COLUMN saved INTEGER DEFAULT 0")
        except sqlite3.OperationalError:
            pass   # column already exists