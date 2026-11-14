"""SQLite connection, schema and error translation shared by the SQLite repositories.

Proves that storage is swappable: the SQLite repositories satisfy the same ports and pass
the same contract tests as the JSON and in-memory implementations.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from personal_assistant.domain.errors import StorageError

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE IF NOT EXISTS contacts (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    name_key TEXT NOT NULL UNIQUE,
    email TEXT,
    address TEXT,
    birthday TEXT
);
CREATE TABLE IF NOT EXISTS contact_phones (
    contact_id TEXT NOT NULL REFERENCES contacts(id) ON DELETE CASCADE,
    phone TEXT NOT NULL,
    position INTEGER NOT NULL,
    PRIMARY KEY (contact_id, phone)
);
CREATE TABLE IF NOT EXISTS notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    text TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS note_tags (
    note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
    tag TEXT NOT NULL,
    PRIMARY KEY (note_id, tag)
);
"""


@contextmanager
def storage_errors() -> Iterator[None]:
    """Translate sqlite3 errors into the domain StorageError."""
    try:
        yield
    except sqlite3.Error as exc:
        raise StorageError(str(exc)) from exc


class SqliteDatabase:
    """Owns the single connection used for the whole program run."""

    def __init__(self, path: Path) -> None:
        with storage_errors():
            path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(path)
            try:
                self.connection.execute("PRAGMA foreign_keys = ON")
                with self.connection:
                    self.connection.executescript(_SCHEMA)
                    self.connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
            except sqlite3.Error:
                self.connection.close()
                raise

    def close(self) -> None:
        self.connection.close()
