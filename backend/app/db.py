"""SQLite persistence layer. Uses stdlib sqlite3 — zero extra dependencies."""
import sqlite3
from contextlib import contextmanager

from .config import settings

DB_PATH = settings.database_url.replace("sqlite:///", "")

SCHEMA_VERSION = 2


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def db():
    conn = get_conn()
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with db() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                marketplace TEXT NOT NULL,
                image TEXT DEFAULT '',
                current_price REAL,
                min_price REAL,
                max_price REAL,
                target_price REAL,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS price_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id INTEGER NOT NULL REFERENCES products(id) ON DELETE CASCADE,
                price REAL NOT NULL,
                recorded_at TEXT DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_history_product ON price_history(product_id);

            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER NOT NULL
            );
            """
        )
        # Lightweight migrations: add columns if missing
        cols = {r[1] for r in conn.execute("PRAGMA table_info(products)").fetchall()}
        if "target_price" not in cols:
            conn.execute("ALTER TABLE products ADD COLUMN target_price REAL")
        if "note" not in cols:
            conn.execute("ALTER TABLE products ADD COLUMN note TEXT DEFAULT ''")
        if "archived" not in cols:
            conn.execute("ALTER TABLE products ADD COLUMN archived INTEGER DEFAULT 0")

        # Track the schema version so health checks can report it
        row = conn.execute("SELECT version FROM schema_version").fetchone()
        if row is None:
            conn.execute("INSERT INTO schema_version (version) VALUES (?)", (SCHEMA_VERSION,))
