"""Note repository backed by SQLite."""

from __future__ import annotations

from datetime import datetime

from personal_assistant.domain.errors import NoteNotFoundError, StorageError
from personal_assistant.domain.note import NewNote, Note
from personal_assistant.domain.value_objects import Tag
from personal_assistant.infrastructure.storage.sqlite.database import (
    SqliteDatabase,
    storage_errors,
)


class SqliteNoteRepository:
    def __init__(self, db: SqliteDatabase) -> None:
        self._conn = db.connection

    def add(self, draft: NewNote) -> Note:
        created = draft.created_at.isoformat()
        with storage_errors(), self._conn:
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
        with storage_errors(), self._conn:
            cursor = self._conn.execute(
                "UPDATE notes SET text = ?, updated_at = ? WHERE id = ?",
                (note.text, note.updated_at.isoformat(), note.id),
            )
            if cursor.rowcount == 0:
                raise NoteNotFoundError(note.id)
            self._conn.execute("DELETE FROM note_tags WHERE note_id = ?", (note.id,))
            self._insert_tags(note.id, note.tags)

    def delete(self, note_id: int) -> None:
        with storage_errors(), self._conn:
            cursor = self._conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
        if cursor.rowcount == 0:
            raise NoteNotFoundError(note_id)

    def _insert_tags(self, note_id: int, tags: frozenset[Tag]) -> None:
        self._conn.executemany(
            "INSERT INTO note_tags (note_id, tag) VALUES (?, ?)",
            [(note_id, tag.value) for tag in sorted(tags)],
        )

    def _select(self, where: str, params: tuple[int, ...]) -> list[Note]:
        with storage_errors():
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
