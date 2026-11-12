from datetime import datetime, timedelta, timezone

import pytest

from personal_assistant.domain.errors import InvalidNoteTextError
from personal_assistant.domain.note import NewNote, Note, validate_note_text
from personal_assistant.domain.value_objects import Tag

T0 = datetime(2026, 11, 12, 10, tzinfo=timezone.utc)
T1 = T0 + timedelta(hours=1)


def note(text: str = "Купити молоко", tags: tuple[str, ...] = ("shop",)) -> Note:
    return Note.from_draft(1, NewNote(text, frozenset(Tag(t) for t in tags), T0))


def test_validate_note_text_strips() -> None:
    assert validate_note_text("  hi ") == "hi"


def test_blank_draft_rejected() -> None:
    with pytest.raises(InvalidNoteTextError):
        NewNote("  ", frozenset(), T0)


def test_draft_text_is_stripped() -> None:
    assert NewNote(" a ", frozenset(), T0).text == "a"


def test_from_draft_sets_fields() -> None:
    n = note()
    assert (n.id, n.text, n.created_at, n.updated_at) == (1, "Купити молоко", T0, T0)


def test_edit_text_strips_and_touches() -> None:
    n = note()
    n.edit_text("  Хліб ", T1)
    assert (n.text, n.updated_at) == ("Хліб", T1)


def test_edit_text_rejects_blank() -> None:
    with pytest.raises(InvalidNoteTextError):
        note().edit_text("", T1)


def test_set_tags_touches() -> None:
    n = note()
    n.set_tags([Tag("a")], T1)
    assert n.tags == {Tag("a")}
    assert n.updated_at == T1


def test_matches_text_and_tag() -> None:
    n = note()
    assert n.matches("МОЛОКО")
    assert n.matches("sho")
    assert not n.matches("xyz")


def test_has_all_tags() -> None:
    n = note(tags=("a", "b"))
    assert n.has_all_tags([Tag("a"), Tag("b")])
    assert not n.has_all_tags([Tag("a"), Tag("c")])


def test_matches_tag_with_hash_prefix() -> None:
    assert note(tags=("робота",)).matches("#робота")
    assert note(tags=("робота",)).matches("#РОБ")
