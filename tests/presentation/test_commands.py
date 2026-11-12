from __future__ import annotations

import pytest

from personal_assistant.domain.errors import DuplicateContactError
from personal_assistant.domain.value_objects import Email, Phone, Tag
from personal_assistant.presentation.registry import Outcome
from tests.presentation.conftest import Harness

SPEC_COMMANDS = {
    "help",
    "exit",
    "close",
    "add-contact",
    "list-contacts",
    "search-contacts",
    "edit-contact",
    "delete-contact",
    "birthdays",
    "add-note",
    "list-notes",
    "search-notes",
    "edit-note",
    "delete-note",
    "search-tag",
    "notes-by-tag",
}


def add_ivan(h: Harness) -> None:
    h.say("Іван", "0501234567, 0671112233", "ivan@mail.com", "", "15.11.1990")
    h.run("add-contact")


def test_registry_contains_all_spec_commands(harness: Harness) -> None:
    assert set(harness.context.registry.names()) == SPEC_COMMANDS


def test_registry_suggest(harness: Harness) -> None:
    assert "add-contact" in harness.context.registry.suggest("add-contct")


def test_registry_alias(harness: Harness) -> None:
    assert harness.context.registry.get("close") is harness.context.registry.get("exit")


def test_add_contact_flow(harness: Harness) -> None:
    add_ivan(harness)
    contact = harness.context.contacts.get("Іван")
    assert contact.phones == [Phone("0501234567"), Phone("0671112233")]
    assert contact.address is None
    assert "Іван" in harness.output()


def test_add_contact_reasks_invalid_email(harness: Harness) -> None:
    harness.say("Іван", "", "bad", "ivan@mail.com", "", "")
    harness.run("add-contact")
    assert harness.context.contacts.get("Іван").email == Email("ivan@mail.com")
    assert "Некоректний email" in harness.output()


def test_add_duplicate_contact_shows_error_via_exception(harness: Harness) -> None:
    add_ivan(harness)
    harness.say("іван", "", "", "", "")
    with pytest.raises(DuplicateContactError):  # the CLI loop turns this into a message
        harness.run("add-contact")


def test_list_and_search_contacts(harness: Harness) -> None:
    add_ivan(harness)
    harness.run("list-contacts")
    assert "+380501234567" in harness.output()
    harness.say("zzz")
    harness.run("search-contacts")
    assert "Нічого не знайдено" in harness.output()


def test_edit_contact_keeps_blank_and_clears_dash(harness: Harness) -> None:
    add_ivan(harness)
    harness.say("іван", "", "", "-", "Київ", "")
    harness.run("edit-contact")
    contact = harness.context.contacts.get("Іван")
    assert contact.email is None
    assert contact.address is not None and contact.address.value == "Київ"
    assert len(contact.phones) == 2


def test_edit_contact_clear_phones(harness: Harness) -> None:
    add_ivan(harness)
    harness.say("Іван", "", "-", "", "", "")
    harness.run("edit-contact")
    assert harness.context.contacts.get("Іван").phones == []


def test_delete_contact_declined_keeps_contact(harness: Harness) -> None:
    add_ivan(harness)
    harness.say("Іван", "n")
    harness.run("delete-contact")
    assert harness.context.contacts.get("Іван")
    assert "Скасовано" in harness.output()


def test_delete_contact_confirmed(harness: Harness) -> None:
    add_ivan(harness)
    harness.say("Іван", "так")
    harness.run("delete-contact")
    assert harness.context.contacts.list_all() == []


def test_birthdays_prints_table(harness: Harness) -> None:
    add_ivan(harness)
    harness.say("7")
    harness.run("birthdays")
    out = harness.output()
    assert "15.11.2026" in out and "36" in out


def test_birthdays_none_found(harness: Harness) -> None:
    harness.say("7")
    harness.run("birthdays")
    assert "Немає днів народження" in harness.output()


def test_add_note_and_search_tag_flow(harness: Harness) -> None:
    harness.say("Купити молоко", "shop, home")
    harness.run("add-note")
    harness.say("Подзвонити", "home")
    harness.run("add-note")
    harness.say("shop, home")
    harness.run("search-tag")
    out = harness.output()
    assert "Купити молоко" in out
    assert harness.context.notes.find_by_tags([Tag("home")])[1].text == "Подзвонити"


def test_edit_note_reasks_invalid_id_and_updates(harness: Harness) -> None:
    harness.say("a", "x")
    harness.run("add-note")
    harness.say("abc", "1", "b", "-")
    harness.run("edit-note")
    note = harness.context.notes.get(1)
    assert (note.text, note.tags) == ("b", frozenset())
    assert "ціле число" in harness.output()


def test_delete_note_confirmed(harness: Harness) -> None:
    harness.say("a", "")
    harness.run("add-note")
    harness.say("1", "y")
    harness.run("delete-note")
    assert harness.context.notes.list_all() == []


def test_list_and_search_notes(harness: Harness) -> None:
    harness.say("Купити молоко", "shop")
    harness.run("add-note")
    harness.run("list-notes")
    harness.say("молоко")
    harness.run("search-notes")
    assert harness.output().count("Купити молоко") >= 2


def test_notes_by_tag_output_order(harness: Harness) -> None:
    for text, tags in [("both", "work, home"), ("w", "work"), ("plain", "")]:
        harness.say(text, tags)
        harness.run("add-note")
    harness.run("notes-by-tag")
    out = harness.output()
    assert out.index("home") < out.index("work") < out.index("без тегів")


def test_exit_returns_exit_outcome(harness: Harness) -> None:
    assert harness.run("exit") is Outcome.EXIT


def test_help_lists_commands(harness: Harness) -> None:
    assert harness.run("help") is Outcome.CONTINUE
    out = harness.output()
    assert "add-contact" in out and "notes-by-tag" in out
