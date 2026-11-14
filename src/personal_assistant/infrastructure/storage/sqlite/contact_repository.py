"""Contact repository backed by SQLite."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import date

from personal_assistant.domain.contact import Contact, ContactId
from personal_assistant.domain.errors import (
    ContactNotFoundError,
    DuplicateContactError,
    StorageError,
)
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone
from personal_assistant.infrastructure.storage.sqlite.database import (
    SqliteDatabase,
    storage_errors,
)


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
        with storage_errors(), self._conn:
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
        with storage_errors():
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
