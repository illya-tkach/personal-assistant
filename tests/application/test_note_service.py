from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from personal_assistant.application.note_service import NoteService
from personal_assistant.domain.errors import NoteNotFoundError
from personal_assistant.domain.value_objects import Tag
from personal_assistant.infrastructure.storage.memory.repositories import InMemoryNoteRepository
from tests.conftest import FixedClock


def tags(*values: str) -> list[Tag]:
    return [Tag(v) for v in values]


@pytest.fixture
def repo() -> InMemoryNoteRepository:
    return InMemoryNoteRepository()


@pytest.fixture
def service(repo: InMemoryNoteRepository, clock: FixedClock) -> NoteService:
    return NoteService(repo, clock)


def test_add_uses_clock_and_assigns_id(service: NoteService, clock: FixedClock) -> None:
    note = service.add("Купити молоко", tags("shop"))
    assert note.id == 1
    assert note.created_at == clock.now()
    assert service.get(1).tags == {Tag("shop")}


def test_update_text_only_keeps_tags(service: NoteService) -> None:
    note = service.add("a", tags("x"))
    updated = service.update(note.id, text="b")
    assert (updated.text, updated.tags) == ("b", {Tag("x")})
    assert service.get(note.id).text == "b"


def test_update_tags_only_keeps_text(service: NoteService) -> None:
    note = service.add("a", tags("x"))
    service.update(note.id, tags=tags("y"))
    stored = service.get(note.id)
    assert (stored.text, stored.tags) == ("a", {Tag("y")})


def test_update_sets_updated_at(repo: InMemoryNoteRepository, clock: FixedClock) -> None:
    note = NoteService(repo, clock).add("a")
    later = FixedClock(clock.now() + timedelta(hours=2))
    NoteService(repo, later).update(note.id, text="b")
    assert repo.get(note.id).updated_at == later.now()


def test_update_missing_raises(service: NoteService) -> None:
    with pytest.raises(NoteNotFoundError):
        service.update(5, text="x")


def test_list_all_sorted_by_created_at(repo: InMemoryNoteRepository) -> None:
    t0 = datetime(2026, 1, 1, tzinfo=timezone.utc)
    NoteService(repo, FixedClock(t0 + timedelta(days=1))).add("second")
    NoteService(repo, FixedClock(t0)).add("first")
    assert [n.text for n in NoteService(repo, FixedClock(t0)).list_all()] == ["first", "second"]


def test_search_text_and_tags(service: NoteService) -> None:
    service.add("Купити молоко", tags("shop"))
    service.add("Зателефонувати мамі", tags("family"))
    assert [n.text for n in service.search("молоко")] == ["Купити молоко"]
    assert [n.text for n in service.search("FAM")] == ["Зателефонувати мамі"]
    assert len(service.search(" ")) == 2


def test_find_by_tags_requires_all(service: NoteService) -> None:
    service.add("ab", tags("a", "b"))
    service.add("a", tags("a"))
    service.add("b", tags("b"))
    assert [n.text for n in service.find_by_tags(tags("a", "b"))] == ["ab"]


def test_find_by_empty_tags_returns_empty(service: NoteService) -> None:
    service.add("a", tags("a"))
    assert service.find_by_tags([]) == []


def test_group_by_tags(service: NoteService) -> None:
    service.add("both", tags("work", "home"))
    service.add("work only", tags("work"))
    service.add("untagged")
    groups = service.group_by_tags()
    assert list(groups) == [Tag("home"), Tag("work"), None]
    assert [n.text for n in groups[Tag("work")]] == ["both", "work only"]
    assert [n.text for n in groups[None]] == ["untagged"]


def test_group_without_untagged_has_no_none_key(service: NoteService) -> None:
    service.add("a", tags("x"))
    assert None not in service.group_by_tags()


def test_delete_missing_raises(service: NoteService) -> None:
    with pytest.raises(NoteNotFoundError):
        service.delete(1)


def test_delete_removes(service: NoteService) -> None:
    note = service.add("a")
    service.delete(note.id)
    assert service.list_all() == []


def test_group_by_tags_uses_ukrainian_alphabet(service: NoteService) -> None:
    service.add("a", tags("яблука", "їжа", "інше", "гроші"))
    assert list(service.group_by_tags()) == tags("гроші", "інше", "їжа", "яблука")
