"""Storage selection. Adding a backend = one builder function + one registry entry."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from personal_assistant.application.ports import ContactRepository, NoteRepository
from personal_assistant.domain.errors import StorageError, UnknownStorageBackendError
from personal_assistant.infrastructure.paths import resolve_data_dir
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

STORAGE_ENV = "PERSONAL_ASSISTANT_STORAGE"
DEFAULT_STORAGE = "json"


@dataclass(frozen=True)
class Settings:
    storage: str
    data_dir: Path

    @classmethod
    def from_env(cls, env: Mapping[str, str]) -> Settings:
        storage = env.get(STORAGE_ENV, "").strip().lower() or DEFAULT_STORAGE
        return cls(storage=storage, data_dir=resolve_data_dir(env))


def _no_op() -> None:
    return None


@dataclass
class StorageBundle:
    """Repositories of one backend plus what the app needs to know about opening them."""

    contacts: ContactRepository
    notes: NoteRepository
    quarantined: list[Path] = field(default_factory=list)
    close: Callable[[], None] = _no_op


def _json_storage(data_dir: Path) -> StorageBundle:
    contacts = JsonContactRepository(JsonFile(data_dir / "contacts.json"))
    notes = JsonNoteRepository(JsonFile(data_dir / "notes.json"))
    quarantined = [p for p in (contacts.quarantined, notes.quarantined) if p is not None]
    return StorageBundle(contacts, notes, quarantined)


def _sqlite_storage(data_dir: Path) -> StorageBundle:
    db = SqliteDatabase(data_dir / "assistant.db")
    return StorageBundle(SqliteContactRepository(db), SqliteNoteRepository(db), close=db.close)


def _memory_storage(data_dir: Path) -> StorageBundle:
    return StorageBundle(InMemoryContactRepository(), InMemoryNoteRepository())


STORAGE_BACKENDS: dict[str, Callable[[Path], StorageBundle]] = {
    "json": _json_storage,
    "sqlite": _sqlite_storage,
    "memory": _memory_storage,
}


def create_storage(settings: Settings) -> StorageBundle:
    """Build the configured backend. Raises UnknownStorageBackendError or StorageError."""
    builder = STORAGE_BACKENDS.get(settings.storage)
    if builder is None:
        raise UnknownStorageBackendError(settings.storage)
    try:
        return builder(settings.data_dir)
    except OSError as exc:
        raise StorageError(str(exc)) from exc
