"""SQLite-backed repositories (stdlib sqlite3, no ORM).

Proves that storage is swappable: these classes satisfy the same ports and pass the
same contract tests as the JSON and in-memory implementations.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date, datetime
from pathlib import Path

from personal_assistant.domain.contact import Contact, ContactId
from personal_assistant.domain.errors import (
    ContactNotFoundError,
    DuplicateContactError,
    NoteNotFoundError,
    StorageError,
)
from personal_assistant.domain.note import NewNote, Note
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone, Tag

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
def _storage_errors() -> Iterator[None]:
    try:
        yield
    except sqlite3.Error as exc:
        raise StorageError(str(exc)) from exc


class SqliteDatabase:
    """Owns the single connection used for the whole program run."""

    def __init__(self, path: Path) -> None:
        with _storage_errors():
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


def _name_key(name: str) -> str:
    return name.strip().casefold()


class SqliteContactRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self._conn = db.connection

    def add(self, contact: Contact) -> None:
        with self._write(contact):
            self._conn.execute(
                "INSERT INTO contacts (id, name, name_key, email, address, birthday)"
                " VALUES (?, ?, ?, ?, ?, ?)",
                (contact.id, *self._columns(contact)),
            )
            self._insert_phones(contact)

    def get(self, contact_id: ContactId) -> Contact:
        contacts = self._select("WHERE id = ?", (contact_id,))
        if not contacts:
            raise ContactNotFoundError(contact_id)
        return contacts[0]

    def find_by_name(self, name: str) -> Contact | None:
        contacts = self._select("WHERE name_key = ?", (_name_key(name),))
        return contacts[0] if contacts else None

    def list_all(self) -> list[Contact]:
        return self._select("", ())

    def update(self, contact: Contact) -> None:
        with self._write(contact):
            cursor = self._conn.execute(
                "UPDATE contacts SET name = ?, name_key = ?, email = ?, address = ?, birthday = ?"
                " WHERE id = ?",
                (*self._columns(contact), contact.id),
            )
            if cursor.rowcount == 0:
                raise ContactNotFoundError(contact.id)
            self._conn.execute("DELETE FROM contact_phones WHERE contact_id = ?", (contact.id,))
            self._insert_phones(contact)

    def delete(self, contact_id: ContactId) -> None:
        with _storage_errors(), self._conn:
            cursor = self._conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        if cursor.rowcount == 0:
            raise ContactNotFoundError(contact_id)

    @contextmanager
    def _write(self, contact: Contact) -> Iterator[None]:
        """One transaction; a UNIQUE(name_key) violation means a duplicate name."""
        try:
            with self._conn:
                yield
        except sqlite3.IntegrityError as exc:
            raise DuplicateContactError(contact.name.value) from exc
        except sqlite3.Error as exc:
            raise StorageError(str(exc)) from exc

    @staticmethod
    def _columns(contact: Contact) -> tuple[str | None, ...]:
        return (
            contact.name.value,
            _name_key(contact.name.value),
            contact.email.value if contact.email else None,
            contact.address.value if contact.address else None,
            contact.birthday.value.isoformat() if contact.birthday else None,
        )

    def _insert_phones(self, contact: Contact) -> None:
        self._conn.executemany(
            "INSERT INTO contact_phones (contact_id, phone, position) VALUES (?, ?, ?)",
            [(contact.id, phone.value, i) for i, phone in enumerate(contact.phones)],
        )

    def _select(self, where: str, params: tuple[str, ...]) -> list[Contact]:
        with _storage_errors():
            rows = self._conn.execute(
                "SELECT id, name, email, address, birthday FROM contacts "
                + where
                + " ORDER BY rowid",
                params,
            ).fetchall()
            contacts: list[Contact] = []
            for contact_id, name, email, address, birthday in rows:
                phones = self._conn.execute(
                    "SELECT phone FROM contact_phones WHERE contact_id = ? ORDER BY position",
                    (contact_id,),
                ).fetchall()
                contacts.append(
                    Contact(
                        id=ContactId(contact_id),
                        name=Name(name),
                        phones=[Phone(p) for (p,) in phones],
                        email=Email(email) if email else None,
                        address=Address(address) if address else None,
                        birthday=Birthday(date.fromisoformat(birthday)) if birthday else None,
                    )
                )
        return contacts


class SqliteNoteRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self._conn = db.connection

    def add(self, draft: NewNote) -> Note:
        created = draft.created_at.isoformat()
        with _storage_errors(), self._conn:
            cursor = self._conn.execute(
                "INSERT INTO notes (text, created_at, updated_at) VALUES (?, ?, ?)",
                (draft.text, created, created),
            )
            note_id = cursor.lastrowid
            if note_id is None:  # pragma: no cover - sqlite always sets it after INSERT
                raise StorageError("no id assigned")
            self._insert_tags(note_id, draft.tags)
        return Note.from_draft(note_id, draft)

    def get(self, note_id: int) -> Note:
        notes = self._select("WHERE id = ?", (note_id,))
        if not notes:
            raise NoteNotFoundError(note_id)
        return notes[0]

    def list_all(self) -> list[Note]:
        return self._select("", ())

    def update(self, note: Note) -> None:
        with _storage_errors(), self._conn:
            cursor = self._conn.execute(
                "UPDATE notes SET text = ?, updated_at = ? WHERE id = ?",
                (note.text, note.updated_at.isoformat(), note.id),
            )
            if cursor.rowcount == 0:
                raise NoteNotFoundError(note.id)
            self._conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note.id,))
            self._insert_tags(note.id, note.tags)

    def delete(self, note_id: int) -> None:
        with _storage_errors(), self._conn:
            cursor = self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        if cursor.rowcount == 0:
            raise NoteNotFoundError(note_id)

    def _insert_tags(self, note_id: int, tags: frozenset[Tag]) -> None:
        self._conn.executemany(
            "INSERT INTO note_tags (note_id, tag) VALUES (?, ?)",
            [(note_id, tag.value) for tag in sorted(tags)],
        )

    def _select(self, where: str, params: tuple[int, ...]) -> list[Note]:
        with _storage_errors():
            rows = self._conn.execute(
                "SELECT id, text, created_at, updated_at FROM notes " + where + " ORDER BY id",
                params,
            ).fetchall()
            notes: list[Note] = []
            for note_id, text, created_at, updated_at in rows:
                tags = self._conn.execute(
                    "SELECT tag FROM note_tags WHERE note_id = ?", (note_id,)
                ).fetchall()
                notes.append(
                    Note(
                        id=note_id,
                        text=text,
                        tags=frozenset(Tag(t) for (t,) in tags),
                        created_at=datetime.fromisoformat(created_at),
                        updated_at=datetime.fromisoformat(updated_at),
                    )
                )
        return notes
