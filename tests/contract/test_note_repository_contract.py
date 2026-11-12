from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone

import pytest

from personal_assistant.application.ports import NoteRepository
from personal_assistant.domain.errors import NoteNotFoundError
from personal_assistant.domain.note import NewNote, Note
from personal_assistant.domain.value_objects import Tag

Factory = Callable[[], NoteRepository]
T0 = datetime(2026, 11, 12, 10, tzinfo=timezone.utc)


def draft(text: str = "Купити молоко", *tags: str) -> NewNote:
    return NewNote(text, frozenset(Tag(t) for t in tags), T0)


def test_add_assigns_incrementing_ids(note_repo_factory: Factory) -> None:
    repo = note_repo_factory()
    assert [repo.add(draft("a")).id, repo.add(draft("b")).id] == [1, 2]


def test_add_returns_stored_note(note_repo_factory: Factory) -> None:
    repo = note_repo_factory()
    note = repo.add(draft("a", "x", "y"))
    assert repo.get(note.id) == note
    assert note.tags == {Tag("x"), Tag("y")}


def test_ids_not_reused_after_delete(note_repo_factory: Factory) -> None:
    repo = note_repo_factory()
    repo.add(draft("a"))
    second = repo.add(draft("b"))
    repo.delete(second.id)
    assert repo.add(draft("c")).id == 3


def test_update_persists_text_and_tags(note_repo_factory: Factory) -> None:
    repo = note_repo_factory()
    note = repo.add(draft("a", "x"))
    later = T0 + timedelta(hours=1)
    note.edit_text("b", later)
    note.set_tags([Tag("z")], later)
    repo.update(note)
    stored = repo.get(note.id)
    assert (stored.text, stored.tags, stored.updated_at) == ("b", {Tag("z")}, later)


def test_list_all_returns_copies(note_repo_factory: Factory) -> None:
    repo = note_repo_factory()
    note = repo.add(draft("a"))
    repo.list_all()[0].text = "changed"
    assert repo.get(note.id).text == "a"


@pytest.mark.parametrize("operation", ["get", "update", "delete"])
def test_missing_note_raises(note_repo_factory: Factory, operation: str) -> None:
    repo = note_repo_factory()
    with pytest.raises(NoteNotFoundError):
        if operation == "get":
            repo.get(42)
        elif operation == "update":
            repo.update(Note.from_draft(42, draft()))
        else:
            repo.delete(42)


def test_data_survives_reopen(note_repo_factory: Factory, skip_if_memory: None) -> None:
    repo = note_repo_factory()
    first = repo.add(draft("a", "x"))
    second = repo.add(draft("b"))
    repo.delete(second.id)
    reopened = note_repo_factory()
    assert reopened.list_all() == [first]
    assert reopened.add(draft("c")).id == 3
