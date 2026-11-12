"""In-memory repositories: a full storage backend (no persistence) and the base for JSON.

State changes are computed on a copy and handed to ``_commit``; subclasses that persist
state override ``_commit`` so the in-memory state only changes after a successful write.
"""

from __future__ import annotations

import copy

from personal_assistant.domain.contact import Contact, ContactId
from personal_assistant.domain.errors import (
    ContactNotFoundError,
    DuplicateContactError,
    NoteNotFoundError,
)
from personal_assistant.domain.note import NewNote, Note


def _name_key(name: str) -> str:
    return name.strip().casefold()


class InMemoryContactRepository:
    def __init__(self, contacts: dict[ContactId, Contact] | None = None) -> None:
        self._contacts: dict[ContactId, Contact] = contacts or {}

    def add(self, contact: Contact) -> None:
        self._ensure_name_free(contact)
        state = dict(self._contacts)
        state[contact.id] = copy.deepcopy(contact)
        self._commit(state)

    def get(self, contact_id: ContactId) -> Contact:
        try:
            return copy.deepcopy(self._contacts[contact_id])
        except KeyError:
            raise ContactNotFoundError(contact_id) from None

    def find_by_name(self, name: str) -> Contact | None:
        key = _name_key(name)
        for contact in self._contacts.values():
            if _name_key(contact.name.value) == key:
                return copy.deepcopy(contact)
        return None

    def list_all(self) -> list[Contact]:
        return copy.deepcopy(list(self._contacts.values()))

    def update(self, contact: Contact) -> None:
        if contact.id not in self._contacts:
            raise ContactNotFoundError(contact.id)
        self._ensure_name_free(contact)
        state = dict(self._contacts)
        state[contact.id] = copy.deepcopy(contact)
        self._commit(state)

    def delete(self, contact_id: ContactId) -> None:
        if contact_id not in self._contacts:
            raise ContactNotFoundError(contact_id)
        state = dict(self._contacts)
        del state[contact_id]
        self._commit(state)

    def _ensure_name_free(self, contact: Contact) -> None:
        key = _name_key(contact.name.value)
        for other in self._contacts.values():
            if other.id != contact.id and _name_key(other.name.value) == key:
                raise DuplicateContactError(contact.name.value)

    def _commit(self, state: dict[ContactId, Contact]) -> None:
        self._contacts = state


class InMemoryNoteRepository:
    def __init__(self, notes: dict[int, Note] | None = None, next_id: int = 1) -> None:
        self._notes: dict[int, Note] = notes or {}
        self._next_id = next_id

    def add(self, draft: NewNote) -> Note:
        note = Note.from_draft(self._next_id, draft)
        state = dict(self._notes)
        state[note.id] = note
        self._commit(state, self._next_id + 1)
        return copy.deepcopy(note)

    def get(self, note_id: int) -> Note:
        try:
            return copy.deepcopy(self._notes[note_id])
        except KeyError:
            raise NoteNotFoundError(note_id) from None

    def list_all(self) -> list[Note]:
        return copy.deepcopy(list(self._notes.values()))

    def update(self, note: Note) -> None:
        if note.id not in self._notes:
            raise NoteNotFoundError(note.id)
        state = dict(self._notes)
        state[note.id] = copy.deepcopy(note)
        self._commit(state, self._next_id)

    def delete(self, note_id: int) -> None:
        if note_id not in self._notes:
            raise NoteNotFoundError(note_id)
        state = dict(self._notes)
        del state[note_id]
        self._commit(state, self._next_id)

    def _commit(self, state: dict[int, Note], next_id: int) -> None:
        self._notes = state
        self._next_id = next_id
