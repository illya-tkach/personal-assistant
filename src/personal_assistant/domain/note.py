"""Note entity with tags."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from personal_assistant.domain.errors import InvalidNoteTextError
from personal_assistant.domain.value_objects import Tag


def validate_note_text(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise InvalidNoteTextError(text)
    return cleaned


@dataclass(frozen=True)
class NewNote:
    """A note that has not been stored yet; storage assigns its id."""

    text: str
    tags: frozenset[Tag]
    created_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "text", validate_note_text(self.text))


@dataclass
class Note:
    id: int
    text: str
    tags: frozenset[Tag]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_draft(cls, note_id: int, draft: NewNote) -> Note:
        return cls(
            id=note_id,
            text=draft.text,
            tags=draft.tags,
            created_at=draft.created_at,
            updated_at=draft.created_at,
        )

    def edit_text(self, text: str, now: datetime) -> None:
        self.text = validate_note_text(text)
        self.updated_at = now

    def set_tags(self, tags: Iterable[Tag], now: datetime) -> None:
        self.tags = frozenset(tags)
        self.updated_at = now

    def matches(self, query: str) -> bool:
        needle = query.strip().casefold()
        return needle in self.text.casefold() or any(needle in tag.value for tag in self.tags)

    def has_all_tags(self, tags: Iterable[Tag]) -> bool:
        return frozenset(tags) <= self.tags
