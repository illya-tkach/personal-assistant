from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

import pytest

from personal_assistant.domain.contact import Contact
from personal_assistant.domain.errors import StorageError
from personal_assistant.domain.note import NewNote
from personal_assistant.domain.value_objects import Name, Phone, Tag
from personal_assistant.infrastructure.storage.json.contact_repository import JsonContactRepository
from personal_assistant.infrastructure.storage.json.file import JsonFile
from personal_assistant.infrastructure.storage.json.note_repository import JsonNoteRepository

T0 = datetime(2026, 11, 12, 10, tzinfo=timezone.utc)


def contacts_repo(tmp_path: Path) -> JsonContactRepository:
    return JsonContactRepository(JsonFile(tmp_path / "contacts.json"))


def test_repository_state_unchanged_when_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = contacts_repo(tmp_path)

    def broken_replace(src: str, dst: str) -> None:
        raise OSError("read-only")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(StorageError):
        repo.add(Contact.create(Name("Іван")))
    assert repo.list_all() == []
    assert repo.find_by_name("Іван") is None


def test_note_counter_unchanged_when_write_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = JsonNoteRepository(JsonFile(tmp_path / "notes.json"))
    original_replace = os.replace

    def broken_replace(src: str, dst: str) -> None:
        raise OSError("read-only")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(StorageError):
        repo.add(NewNote("a", frozenset(), T0))
    monkeypatch.setattr(os, "replace", original_replace)
    assert repo.add(NewNote("b", frozenset(), T0)).id == 1


VALID_ITEM = {
    "id": "x",
    "name": "Іван",
    "phones": ["+380501234567"],
    "email": None,
    "address": None,
    "birthday": None,
}


@pytest.mark.parametrize(
    "content",
    [
        "{not json",
        "[]",
        '{"version": 1}',
        '{"version": 1, "items": [{"id": "x"}]}',
        json.dumps({"version": 1, "items": [{**VALID_ITEM, "phones": ["123"]}]}),
        json.dumps({"version": 1, "items": [{**VALID_ITEM, "birthday": "not-a-date"}]}),
        json.dumps({"version": 1, "items": "oops"}),
    ],
)
def test_corrupt_contacts_file_is_quarantined(tmp_path: Path, content: str) -> None:
    (tmp_path / "contacts.json").write_text(content, encoding="utf-8")
    repo = contacts_repo(tmp_path)
    assert repo.list_all() == []
    assert repo.quarantined is not None and repo.quarantined.exists()
    assert repo.quarantined.name.startswith("contacts.corrupt-")
    assert not (tmp_path / "contacts.json").exists()


def test_valid_file_is_not_quarantined(tmp_path: Path) -> None:
    (tmp_path / "contacts.json").write_text(
        json.dumps({"version": 1, "items": [VALID_ITEM]}), encoding="utf-8"
    )
    repo = contacts_repo(tmp_path)
    assert repo.quarantined is None
    assert [c.name.value for c in repo.list_all()] == ["Іван"]


def test_corrupt_notes_file_is_quarantined(tmp_path: Path) -> None:
    (tmp_path / "notes.json").write_text("{not json", encoding="utf-8")
    repo = JsonNoteRepository(JsonFile(tmp_path / "notes.json"))
    assert repo.list_all() == []
    assert repo.quarantined is not None and repo.quarantined.name.startswith("notes.corrupt-")


def test_contacts_file_format(tmp_path: Path) -> None:
    repo = contacts_repo(tmp_path)
    repo.add(Contact.create(Name("Іван"), phones=[Phone("0501234567")]))
    data = json.loads((tmp_path / "contacts.json").read_text(encoding="utf-8"))
    assert data["version"] == 1
    assert data["items"][0]["phones"] == ["+380501234567"]


def test_notes_file_format(tmp_path: Path) -> None:
    repo = JsonNoteRepository(JsonFile(tmp_path / "notes.json"))
    repo.add(NewNote("a", frozenset({Tag("b"), Tag("a")}), T0))
    data = json.loads((tmp_path / "notes.json").read_text(encoding="utf-8"))
    assert data["version"] == 1 and data["next_id"] == 2
    item = data["items"][0]
    assert item["tags"] == ["a", "b"]
    assert item["created_at"] == T0.isoformat()
