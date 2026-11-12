from __future__ import annotations

from collections.abc import Callable
from datetime import date

import pytest

from personal_assistant.application.ports import ContactRepository
from personal_assistant.domain.contact import Contact, ContactId
from personal_assistant.domain.errors import ContactNotFoundError, DuplicateContactError
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone

Factory = Callable[[], ContactRepository]


def full_contact(name: str = "Іван") -> Contact:
    return Contact.create(
        Name(name),
        phones=[Phone("0501234567"), Phone("0671112233")],
        email=Email("ivan@mail.com"),
        address=Address("Київ"),
        birthday=Birthday(date(1990, 3, 15)),
    )


def test_add_and_get(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    c = full_contact()
    repo.add(c)
    assert repo.get(c.id) == c


def test_find_by_name_case_insensitive_cyrillic(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    c = full_contact("Іван")
    repo.add(c)
    found = repo.find_by_name("іВАН")
    assert found is not None and found.id == c.id
    assert repo.find_by_name("Петро") is None


def test_add_duplicate_name_raises(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    repo.add(Contact.create(Name("Іван")))
    with pytest.raises(DuplicateContactError):
        repo.add(Contact.create(Name("іван")))


def test_update_persists_changes(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    c = full_contact()
    repo.add(c)
    c.set_phones([Phone("0939998877")])
    c.email = Email("new@mail.com")
    repo.update(c)
    stored = repo.get(c.id)
    assert stored.phones == [Phone("0939998877")]
    assert stored.email == Email("new@mail.com")


def test_update_rename_case_only_allowed(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    c = Contact.create(Name("іван"))
    repo.add(c)
    c.name = Name("Іван")
    repo.update(c)
    assert repo.get(c.id).name == Name("Іван")


def test_update_rename_to_other_contact_raises(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    repo.add(Contact.create(Name("Іван")))
    petro = Contact.create(Name("Петро"))
    repo.add(petro)
    petro.name = Name("ІВАН")
    with pytest.raises(DuplicateContactError):
        repo.update(petro)
    assert repo.get(petro.id).name == Name("Петро")


def test_update_missing_raises(contact_repo_factory: Factory) -> None:
    with pytest.raises(ContactNotFoundError):
        contact_repo_factory().update(Contact.create(Name("Іван")))


def test_get_missing_raises(contact_repo_factory: Factory) -> None:
    with pytest.raises(ContactNotFoundError):
        contact_repo_factory().get(ContactId("missing"))


def test_delete_missing_raises(contact_repo_factory: Factory) -> None:
    with pytest.raises(ContactNotFoundError):
        contact_repo_factory().delete(ContactId("missing"))


def test_delete_removes(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    c = full_contact()
    repo.add(c)
    repo.delete(c.id)
    assert repo.list_all() == []
    assert repo.find_by_name("Іван") is None


def test_list_all_returns_copies(contact_repo_factory: Factory) -> None:
    repo = contact_repo_factory()
    c = full_contact()
    repo.add(c)
    repo.list_all()[0].phones.append(Phone("0939998877"))
    c.phones.append(Phone("0631234567"))
    assert len(repo.get(c.id).phones) == 2


def test_data_survives_reopen(contact_repo_factory: Factory, skip_if_memory: None) -> None:
    c = full_contact()
    contact_repo_factory().add(c)
    reopened = contact_repo_factory()
    assert reopened.get(c.id) == c
    assert reopened.list_all() == [c]
