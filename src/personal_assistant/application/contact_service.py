"""Contact use cases: add, find, edit, delete, upcoming birthdays."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from personal_assistant.application.ports import Clock, ContactRepository
from personal_assistant.domain.contact import Contact
from personal_assistant.domain.errors import ContactNotFoundError, InvalidDaysError
from personal_assistant.domain.sorting import ukrainian_sort_key
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone

MAX_BIRTHDAY_WINDOW_DAYS = 365


@dataclass(frozen=True)
class ContactData:
    """All editable fields of a contact, already validated."""

    name: Name
    phones: tuple[Phone, ...] = ()
    email: Email | None = None
    address: Address | None = None
    birthday: Birthday | None = None


@dataclass(frozen=True)
class UpcomingBirthday:
    contact: Contact
    date: date
    days_until: int
    age: int


class ContactService:
    def __init__(self, repository: ContactRepository, clock: Clock) -> None:
        self._repository = repository
        self._clock = clock

    def add(self, data: ContactData) -> Contact:
        contact = Contact.create(
            data.name,
            phones=data.phones,
            email=data.email,
            address=data.address,
            birthday=data.birthday,
        )
        self._repository.add(contact)
        return contact

    def get(self, name: str) -> Contact:
        contact = self._repository.find_by_name(name)
        if contact is None:
            raise ContactNotFoundError(name)
        return contact

    def list_all(self) -> list[Contact]:
        return sorted(self._repository.list_all(), key=lambda c: ukrainian_sort_key(c.name.value))

    def search(self, query: str) -> list[Contact]:
        contacts = self.list_all()
        if not query.strip():
            return contacts
        return [c for c in contacts if c.matches(query)]

    def update(self, name: str, data: ContactData) -> Contact:
        contact = self.get(name)
        contact.name = data.name
        contact.set_phones(data.phones)
        contact.email = data.email
        contact.address = data.address
        contact.birthday = data.birthday
        self._repository.update(contact)
        return contact

    def delete(self, name: str) -> None:
        self._repository.delete(self.get(name).id)

    def upcoming_birthdays(self, days: int) -> list[UpcomingBirthday]:
        if not 0 <= days <= MAX_BIRTHDAY_WINDOW_DAYS:
            raise InvalidDaysError(str(days))
        today = self._clock.today()
        result: list[UpcomingBirthday] = []
        for contact in self._repository.list_all():
            upcoming = contact.next_birthday(today)
            age = contact.age_on_next_birthday(today)
            if upcoming is None or age is None:
                continue
            days_until = (upcoming - today).days
            if days_until <= days:
                result.append(UpcomingBirthday(contact, upcoming, days_until, age))
        return sorted(
            result, key=lambda r: (r.days_until, ukrainian_sort_key(r.contact.name.value))
        )
