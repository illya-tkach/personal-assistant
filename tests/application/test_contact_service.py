from __future__ import annotations

from datetime import date

import pytest

from personal_assistant.application.contact_service import ContactData, ContactService
from personal_assistant.domain.errors import (
    ContactNotFoundError,
    DuplicateContactError,
    InvalidDaysError,
)
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone
from personal_assistant.infrastructure.storage.memory.repositories import InMemoryContactRepository
from tests.conftest import FixedClock


@pytest.fixture
def service(clock: FixedClock) -> ContactService:
    return ContactService(InMemoryContactRepository(), clock)


def data(name: str, birthday: str | None = None, **kw: object) -> ContactData:
    bday = Birthday(date.fromisoformat(birthday)) if birthday else None
    return ContactData(name=Name(name), birthday=bday, **kw)  # type: ignore[arg-type]


def test_add_then_get_by_name_case_insensitive(service: ContactService) -> None:
    added = service.add(data("Іван", phones=(Phone("0501234567"),)))
    assert service.get("іван").id == added.id
    assert service.get("іван").phones == [Phone("0501234567")]


def test_add_duplicate_raises(service: ContactService) -> None:
    service.add(data("Іван"))
    with pytest.raises(DuplicateContactError):
        service.add(data("ІВАН"))


def test_get_missing_raises(service: ContactService) -> None:
    with pytest.raises(ContactNotFoundError):
        service.get("Ніхто")


def test_list_all_sorted_by_name(service: ContactService) -> None:
    for name in ["Борис", "андрій", "Яна"]:
        service.add(data(name))
    assert [c.name.value for c in service.list_all()] == ["андрій", "Борис", "Яна"]


def test_search_delegates_to_matches(service: ContactService) -> None:
    service.add(data("Іван", email=Email("ivan@mail.com")))
    service.add(data("Петро"))
    assert [c.name.value for c in service.search("MAIL")] == ["Іван"]


def test_blank_search_returns_all(service: ContactService) -> None:
    service.add(data("Іван"))
    service.add(data("Петро"))
    assert len(service.search("  ")) == 2


def test_update_replaces_fields_and_keeps_id(service: ContactService) -> None:
    original = service.add(data("Іван", email=Email("ivan@mail.com"), address=Address("Київ")))
    updated = service.update("іван", data("Іван Петренко", phones=(Phone("0671112233"),)))
    assert updated.id == original.id
    stored = service.get("Іван Петренко")
    assert stored.email is None and stored.address is None
    assert stored.phones == [Phone("0671112233")]


def test_update_rename_to_taken_name_raises(service: ContactService) -> None:
    service.add(data("Іван"))
    service.add(data("Петро"))
    with pytest.raises(DuplicateContactError):
        service.update("Петро", data("іван"))


def test_update_missing_raises(service: ContactService) -> None:
    with pytest.raises(ContactNotFoundError):
        service.update("Ніхто", data("Ніхто"))


def test_delete_then_get_raises(service: ContactService) -> None:
    service.add(data("Іван"))
    service.delete("ІВАН")
    with pytest.raises(ContactNotFoundError):
        service.get("Іван")


def test_delete_missing_raises(service: ContactService) -> None:
    with pytest.raises(ContactNotFoundError):
        service.delete("Ніхто")


def test_upcoming_birthdays_window(service: ContactService) -> None:
    service.add(data("Сьогодні", "1990-11-12"))
    service.add(data("Тиждень", "2000-11-19"))
    service.add(data("Вісім", "1990-11-20"))
    service.add(data("БезДати"))
    result = service.upcoming_birthdays(7)
    assert [r.contact.name.value for r in result] == ["Сьогодні", "Тиждень"]
    assert [r.days_until for r in result] == [0, 7]
    assert [r.age for r in result] == [36, 26]
    assert result[1].date == date(2026, 11, 19)


def test_upcoming_birthdays_zero_days_only_today(service: ContactService) -> None:
    service.add(data("Сьогодні", "1990-11-12"))
    service.add(data("Завтра", "1990-11-13"))
    assert [r.contact.name.value for r in service.upcoming_birthdays(0)] == ["Сьогодні"]


def test_upcoming_birthdays_ties_sorted_by_name(service: ContactService) -> None:
    service.add(data("Яна", "1990-11-15"))
    service.add(data("андрій", "1985-11-15"))
    assert [r.contact.name.value for r in service.upcoming_birthdays(5)] == ["андрій", "Яна"]


@pytest.mark.parametrize("days", [-1, 366])
def test_invalid_days_raise(service: ContactService, days: int) -> None:
    with pytest.raises(InvalidDaysError):
        service.upcoming_birthdays(days)


def test_list_all_uses_ukrainian_alphabet(service: ContactService) -> None:
    for name in ["Яна", "Ірина", "Євген", "Петро"]:
        service.add(data(name))
    assert [c.name.value for c in service.list_all()] == ["Євген", "Ірина", "Петро", "Яна"]
