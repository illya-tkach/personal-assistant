"""Contact repository persisted to a JSON file."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

from personal_assistant.domain.contact import Contact, ContactId
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone
from personal_assistant.infrastructure.storage.json.file import (
    LOAD_ERRORS,
    SCHEMA_VERSION,
    JsonFile,
    require,
)
from personal_assistant.infrastructure.storage.memory.repositories import InMemoryContactRepository


def contact_to_dict(contact: Contact) -> dict[str, Any]:
    return {
        "id": contact.id,
        "name": contact.name.value,
        "phones": [phone.value for phone in contact.phones],
        "email": contact.email.value if contact.email else None,
        "address": contact.address.value if contact.address else None,
        "birthday": contact.birthday.value.isoformat() if contact.birthday else None,
    }


def contact_from_dict(item: Any) -> Contact:
    require(item, dict)
    email = item["email"]
    address = item["address"]
    birthday = item["birthday"]
    return Contact(
        id=ContactId(require(item["id"], str)),
        name=Name(require(item["name"], str)),
        phones=[Phone(require(p, str)) for p in require(item["phones"], list)],
        email=Email(require(email, str)) if email is not None else None,
        address=Address(require(address, str)) if address is not None else None,
        birthday=Birthday(date.fromisoformat(require(birthday, str)))
        if birthday is not None
        else None,
    )


class JsonContactRepository(InMemoryContactRepository):
    def __init__(self, file: JsonFile) -> None:
        self._file = file
        self.quarantined: Path | None = None
        super().__init__(self._load())

    def _load(self) -> dict[ContactId, Contact]:
        try:
            data = self._file.read()
            if data is None:
                return {}
            contacts = [contact_from_dict(item) for item in require(data["items"], list)]
        except LOAD_ERRORS:
            self.quarantined = self._file.quarantine()
            return {}
        return {contact.id: contact for contact in contacts}

    def _commit(self, state: dict[ContactId, Contact]) -> None:
        self._file.write(
            {"version": SCHEMA_VERSION, "items": [contact_to_dict(c) for c in state.values()]}
        )
        super()._commit(state)
