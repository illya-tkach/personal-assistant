from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from personal_assistant.domain.errors import StorageError
from personal_assistant.infrastructure.json_storage import CorruptFileError, JsonFile


def test_write_then_read_round_trip(tmp_path: Path) -> None:
    file = JsonFile(tmp_path / "data.json")
    file.write({"version": 1, "items": ["Іван"]})
    assert file.read() == {"version": 1, "items": ["Іван"]}


def test_write_keeps_cyrillic_readable(tmp_path: Path) -> None:
    JsonFile(tmp_path / "data.json").write({"name": "Іван"})
    assert "Іван" in (tmp_path / "data.json").read_text(encoding="utf-8")


def test_read_missing_returns_none(tmp_path: Path) -> None:
    assert JsonFile(tmp_path / "missing.json").read() is None


def test_write_creates_parent_dir(tmp_path: Path) -> None:
    JsonFile(tmp_path / "nested" / "data.json").write({})
    assert (tmp_path / "nested" / "data.json").exists()


@pytest.mark.parametrize("content", ["{not json", "[]", '"text"'])
def test_read_invalid_raises_corrupt(tmp_path: Path, content: str) -> None:
    (tmp_path / "data.json").write_text(content, encoding="utf-8")
    with pytest.raises(CorruptFileError):
        JsonFile(tmp_path / "data.json").read()


def test_write_leaves_no_tmp_files(tmp_path: Path) -> None:
    JsonFile(tmp_path / "data.json").write({"a": 1})
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_write_failure_raises_storage_error_and_keeps_old_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    file = JsonFile(tmp_path / "data.json")
    file.write({"old": True})

    def broken_replace(src: str, dst: str) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", broken_replace)
    with pytest.raises(StorageError):
        file.write({"new": True})
    assert json.loads((tmp_path / "data.json").read_text(encoding="utf-8")) == {"old": True}
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


def test_quarantine_renames_file(tmp_path: Path) -> None:
    (tmp_path / "contacts.json").write_text("{bad", encoding="utf-8")
    moved = JsonFile(tmp_path / "contacts.json").quarantine()
    assert moved.exists()
    assert moved.name.startswith("contacts.corrupt-") and moved.suffix == ".json"
    assert not (tmp_path / "contacts.json").exists()
