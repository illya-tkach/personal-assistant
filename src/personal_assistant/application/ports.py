"""Ports: abstractions the services depend on. Infrastructure provides implementations.

Repositories work with individual records (not whole files), so they map equally
well onto a JSON file or a SQL database. They raise only domain errors.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Protocol

from personal_assistant.domain.contact import Contact, ContactId
from personal_assistant.domain.note import NewNote, Note


class ContactRepository(Protocol):
    def add(self, contact: Contact) -> None:
        """Store a new contact. Raises DuplicateContactError if the name is taken."""

    def get(self, contact_id: ContactId) -> Contact:
        """Raises ContactNotFoundError."""

    def find_by_name(self, name: str) -> Contact | None:
        """Case-insensitive lookup by name."""

    def list_all(self) -> list[Contact]:
        """Return copies of all contacts."""

    def update(self, contact: Contact) -> None:
        """Raises ContactNotFoundError or DuplicateContactError."""

    def delete(self, contact_id: ContactId) -> None:
        """Raises ContactNotFoundError."""


class NoteRepository(Protocol):
    def add(self, draft: NewNote) -> Note:
        """Store a new note; the storage assigns an id that is never reused."""

    def get(self, note_id: int) -> Note:
        """Raises NoteNotFoundError."""

    def list_all(self) -> list[Note]:
        """Return copies of all notes."""

    def update(self, note: Note) -> None:
        """Raises NoteNotFoundError."""

    def delete(self, note_id: int) -> None:
        """Raises NoteNotFoundError."""


class Clock(Protocol):
    def now(self) -> datetime: ...

    def today(self) -> date: ...
