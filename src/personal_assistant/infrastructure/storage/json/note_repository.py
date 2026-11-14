"""Note repository persisted to a JSON file."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from personal_assistant.domain.note import Note, validate_note_text
from personal_assistant.domain.value_objects import Tag
from personal_assistant.infrastructure.storage.json.file import (
    LOAD_ERRORS,
    SCHEMA_VERSION,
    JsonFile,
    require,
)
from personal_assistant.infrastructure.storage.memory.repositories import InMemoryNoteRepository


def note_to_dict(note: Note) -> dict[str, Any]:
    return {
        "id": note.id,
        "text": note.text,
        "tags": sorted(tag.value for tag in note.tags),
        "created_at": note.created_at.isoformat(),
        "updated_at": note.updated_at.isoformat(),
    }


def note_from_dict(item: Any) -> Note:
    require(item, dict)
    return Note(
        id=require(item["id"], int),
        text=validate_note_text(require(item["text"], str)),
        tags=frozenset(Tag(require(t, str)) for t in require(item["tags"], list)),
        created_at=datetime.fromisoformat(require(item["created_at"], str)),
        updated_at=datetime.fromisoformat(require(item["updated_at"], str)),
    )


class JsonNoteRepository(InMemoryNoteRepository):
    def __init__(self, file: JsonFile) -> None:
        self._file = file
        self.quarantined: Path | None = None
        notes, next_id = self._load()
        super().__init__(notes, next_id)

    def _load(self) -> tuple[dict[int, Note], int]:
        try:
            data = self._file.read()
            if data is None:
                return {}, 1
            notes = [note_from_dict(item) for item in require(data["items"], list)]
            stored_next_id = require(data["next_id"], int)
        except LOAD_ERRORS:
            self.quarantined = self._file.quarantine()
            return {}, 1
        highest = max((note.id for note in notes), default=0)
        return {note.id: note for note in notes}, max(stored_next_id, highest + 1)

    def _commit(self, state: dict[int, Note], next_id: int) -> None:
        self._file.write(
            {
                "version": SCHEMA_VERSION,
                "next_id": next_id,
                "items": [note_to_dict(n) for n in state.values()],
            }
        )
        super()._commit(state, next_id)
