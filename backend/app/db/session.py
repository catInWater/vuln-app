"""Database connection and schema initialization.

Educational code: deliberately simple. No connection pooling, no ORM, and one
shared connection per handler (check_same_thread=False). The database file
lives at the project root and is created automatically by sqlite3 on first
connect; init_db() layers the users table on top (CREATE TABLE IF NOT EXISTS),
which also recreates everything after the file is deleted (lab reset feature).
"""

import sqlite3
from pathlib import Path

# vulnerable_app.db at project root (two levels above backend/app/db/)
DB_PATH = Path(__file__).resolve().parents[3] / "vulnerable_app.db"


def get_db() -> sqlite3.Connection:
    """Open a connection with dict-style row access."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users table if it does not exist (idempotent)."""
    conn = get_db()
    try:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS users ("
            "    id       INTEGER PRIMARY KEY AUTOINCREMENT,"
            "    username TEXT UNIQUE,"
            "    email    TEXT,"
            "    password TEXT"
            ")"
        )
        conn.commit()
    finally:
        conn.close()