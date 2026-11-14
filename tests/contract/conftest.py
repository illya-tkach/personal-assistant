"""Shared fixtures: every storage backend must pass the same contract tests.

Each fixture returns a factory; calling it again re-opens the *same* storage,
which lets tests check that data survives a restart.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from personal_assistant.application.ports import ContactRepository, NoteRepository
from personal_assistant.infrastructure.storage.json.contact_repository import JsonContactRepository
from personal_assistant.infrastructure.storage.json.file import JsonFile
from personal_assistant.infrastructure.storage.json.note_repository import JsonNoteRepository
from personal_assistant.infrastructure.storage.memory.repositories import (
    InMemoryContactRepository,
    InMemoryNoteRepository,
)
from personal_assistant.infrastructure.storage.sqlite.contact_repository import (
    SqliteContactRepository,
)
from personal_assistant.infrastructure.storage.sqlite.database import SqliteDatabase
from personal_assistant.infrastructure.storage.sqlite.note_repository import SqliteNoteRepository

BACKENDS = ["memory", "json", "sqlite"]


class _SqliteOpener:
    """Re-opens the same database file, closing the previous connection first."""

    def __init__(self, path: Path) -> None:
        self._path = path
        self._db: SqliteDatabase | None = None

    def open(self) -> SqliteDatabase:
        self.close()
        self._db = SqliteDatabase(self._path)
        return self._db

    def close(self) -> None:
        if self._db is not None:
            self._db.close()
            self._db = None


@pytest.fixture(params=BACKENDS)
def backend(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def contact_repo_factory(backend: str, tmp_path: Path) -> Iterator[Callable[[], ContactRepository]]:
    if backend == "memory":
        repo = InMemoryContactRepository()
        yield lambda: repo
    elif backend == "json":
        yield lambda: JsonContactRepository(JsonFile(tmp_path / "contacts.json"))
    elif backend == "sqlite":
        opener = _SqliteOpener(tmp_path / "assistant.db")
        yield lambda: SqliteContactRepository(opener.open())
        opener.close()
    else:  # pragma: no cover - extended by later backends
        raise AssertionError(backend)


@pytest.fixture
def note_repo_factory(backend: str, tmp_path: Path) -> Iterator[Callable[[], NoteRepository]]:
    if backend == "memory":
        repo = InMemoryNoteRepository()
        yield lambda: repo
    elif backend == "json":
        yield lambda: JsonNoteRepository(JsonFile(tmp_path / "notes.json"))
    elif backend == "sqlite":
        opener = _SqliteOpener(tmp_path / "assistant.db")
        yield lambda: SqliteNoteRepository(opener.open())
        opener.close()
    else:  # pragma: no cover - extended by later backends
        raise AssertionError(backend)


@pytest.fixture
def skip_if_memory(backend: str) -> None:
    if backend == "memory":
        pytest.skip("in-memory storage does not survive a restart")
