"""Contact entity and birthday rules."""

from __future__ import annotations

import calendar
import re
import uuid
from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date
from typing import NewType

from personal_assistant.domain.errors import PhoneNotFoundError
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone

ContactId = NewType("ContactId", str)


def _unique(phones: Iterable[Phone]) -> list[Phone]:
    return list(dict.fromkeys(phones))


def _birthday_in_year(birthday: date, year: int) -> date:
    """Feb 29 is celebrated on Feb 28 in non-leap years."""
    if birthday.month == 2 and birthday.day == 29 and not calendar.isleap(year):
        return date(year, 2, 28)
    return birthday.replace(year=year)


@dataclass
class Contact:
    id: ContactId
    name: Name
    phones: list[Phone] = field(default_factory=list)
    email: Email | None = None
    address: Address | None = None
    birthday: Birthday | None = None

    @classmethod
    def create(
        cls,
        name: Name,
        phones: Iterable[Phone] = (),
        email: Email | None = None,
        address: Address | None = None,
        birthday: Birthday | None = None,
    ) -> Contact:
        return cls(
            id=ContactId(uuid.uuid4().hex),
            name=name,
            phones=_unique(phones),
            email=email,
            address=address,
            birthday=birthday,
        )

    def add_phone(self, phone: Phone) -> None:
        if phone not in self.phones:
            self.phones.append(phone)

    def remove_phone(self, phone: Phone) -> None:
        if phone not in self.phones:
            raise PhoneNotFoundError(phone.value)
        self.phones.remove(phone)

    def set_phones(self, phones: Iterable[Phone]) -> None:
        self.phones = _unique(phones)

    def next_birthday(self, today: date) -> date | None:
        if self.birthday is None:
            return None
        candidate = _birthday_in_year(self.birthday.value, today.year)
        if candidate < today:
            candidate = _birthday_in_year(self.birthday.value, today.year + 1)
        return candidate

    def days_until_birthday(self, today: date) -> int | None:
        upcoming = self.next_birthday(today)
        return None if upcoming is None else (upcoming - today).days

    def age_on_next_birthday(self, today: date) -> int | None:
        upcoming = self.next_birthday(today)
        if upcoming is None or self.birthday is None:
            return None
        return upcoming.year - self.birthday.value.year

    def matches(self, query: str) -> bool:
        """Case-insensitive substring search; phones are compared by digits only."""
        needle = query.strip().casefold()
        texts = [self.name.value]
        if self.email:
            texts.append(self.email.value)
        if self.address:
            texts.append(self.address.value)
        if self.birthday:
            texts.append(self.birthday.format())
        if any(needle in text.casefold() for text in texts):
            return True
        digits = re.sub(r"\D", "", needle)
        return bool(digits) and any(digits in phone.digits for phone in self.phones)
