from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from datetime import datetime, timezone
from pathlib import Path

import pytest

from personal_assistant.domain.contact import Contact
from personal_assistant.domain.errors import StorageError
from personal_assistant.domain.note import NewNote
from personal_assistant.domain.value_objects import Name, Phone, Tag
from personal_assistant.infrastructure.sqlite_repositories import (
    SqliteContactRepository,
    SqliteDatabase,
    SqliteNoteRepository,
)

T0 = datetime(2026, 11, 12, 10, tzinfo=timezone.utc)


@pytest.fixture
def db_path(tmp_path: Path) -> Path:
    return tmp_path / "assistant.db"


@pytest.fixture
def db(db_path: Path) -> Iterator[SqliteDatabase]:
    database = SqliteDatabase(db_path)
    yield database
    database.close()


def inspect(path: Path, sql: str) -> list[tuple[object, ...]]:
    with sqlite3.connect(path) as conn:
        return conn.execute(sql).fetchall()


def test_schema_created_on_first_open(db: SqliteDatabase, db_path: Path) -> None:
    tables = {
        row[0] for row in inspect(db_path, "SELECT name FROM sqlite_master WHERE type='table'")
    }
    assert {"contacts", "contact_phones", "notes", "note_tags"} <= tables
    assert inspect(db_path, "PRAGMA user_version") == [(1,)]


def test_reopen_does_not_fail_on_existing_schema(db: SqliteDatabase, db_path: Path) -> None:
    SqliteContactRepository(db).add(Contact.create(Name("Іван")))
    db.close()
    reopened = SqliteDatabase(db_path)
    assert [c.name.value for c in SqliteContactRepository(reopened).list_all()] == ["Іван"]
    reopened.close()


def test_delete_contact_cascades_phones(db: SqliteDatabase, db_path: Path) -> None:
    repo = SqliteContactRepository(db)
    contact = Contact.create(Name("Іван"), phones=[Phone("0501234567")])
    repo.add(contact)
    repo.delete(contact.id)
    assert inspect(db_path, "SELECT COUNT(*) FROM contact_phones") == [(0,)]


def test_phone_order_preserved(db: SqliteDatabase) -> None:
    repo = SqliteContactRepository(db)
    phones = [Phone("0939998877"), Phone("0501234567"), Phone("0671112233")]
    contact = Contact.create(Name("Іван"), phones=phones)
    repo.add(contact)
    assert repo.get(contact.id).phones == phones


def test_delete_note_cascades_tags(db: SqliteDatabase, db_path: Path) -> None:
    repo = SqliteNoteRepository(db)
    note = repo.add(NewNote("a", frozenset({Tag("x")}), T0))
    repo.delete(note.id)
    assert inspect(db_path, "SELECT COUNT(*) FROM note_tags") == [(0,)]


def test_corrupt_db_file_raises_storage_error(db_path: Path) -> None:
    db_path.write_bytes(b"this is definitely not a sqlite database" * 100)
    with pytest.raises(StorageError):
        SqliteDatabase(db_path)
