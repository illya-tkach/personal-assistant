"""Note use cases: add, search, edit, delete, tag search and grouping."""

from __future__ import annotations

from collections.abc import Iterable

from personal_assistant.application.ports import Clock, NoteRepository
from personal_assistant.domain.note import NewNote, Note
from personal_assistant.domain.sorting import ukrainian_sort_key
from personal_assistant.domain.value_objects import Tag


class NoteService:
    def __init__(self, repository: NoteRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def add(self, text: str, tags: Iterable[Tag] = ()) -> Note:
        return self._repository.add(NewNote(text, frozenset(tags), self._clock.now()))

    def get(self, note_id: int) -> Note:
        return self._repository.get(note_id)

    def list_all(self) -> list[Note]:
        return sorted(self._repository.list_all(), key=lambda n: (n.created_at, n.id))

    def search(self, query: str) -> list[Note]:
        notes = self.list_all()
        if not query.strip():
            return notes
        return [n for n in notes if n.matches(query)]

    def update(
        self, note_id: int, text: str | None = None, tags: Iterable[Tag] | None = None
    ) -> Note:
        note = self._repository.get(note_id)
        now = self._clock.now()
        if text is not None:
            note.edit_text(text, now)
        if tags is not None:
            note.set_tags(tags, now)
        self._repository.update(note)
        return note

    def delete(self, note_id: int) -> None:
        self._repository.delete(note_id)

    def find_by_tags(self, tags: Iterable[Tag]) -> list[Note]:
        wanted = frozenset(tags)
        if not wanted:
            return []
        return [n for n in self.list_all() if n.has_all_tags(wanted)]

    def group_by_tags(self) -> dict[Tag | None, list[Note]]:
        """Notes grouped by tag, tags alphabetically; untagged notes last under ``None``."""
        notes = self.list_all()
        groups: dict[Tag | None, list[Note]] = {}
        all_tags = {tag for note in notes for tag in note.tags}
        for tag in sorted(all_tags, key=lambda t: ukrainian_sort_key(t.value)):
            groups[tag] = [n for n in notes if tag in n.tags]
        untagged = [n for n in notes if not n.tags]
        if untagged:
            groups[None] = untagged
        return groups
