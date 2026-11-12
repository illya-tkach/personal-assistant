from __future__ import annotations

from pathlib import Path

import pytest

from personal_assistant.domain.contact import Contact
from personal_assistant.domain.errors import UnknownStorageBackendError
from personal_assistant.domain.value_objects import Name
from personal_assistant.infrastructure.clock import SystemClock
from personal_assistant.infrastructure.factory import Settings, create_storage
from personal_assistant.infrastructure.paths import resolve_data_dir


def test_data_dir_from_env_is_created(tmp_path: Path) -> None:
    target = tmp_path / "data"
    assert resolve_data_dir({"PERSONAL_ASSISTANT_HOME": str(target)}) == target
    assert target.is_dir()


def test_data_dir_defaults_to_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    assert resolve_data_dir({}) == tmp_path / ".personal_assistant"
    assert (tmp_path / ".personal_assistant").is_dir()


def test_settings_default_storage_is_json(tmp_path: Path) -> None:
    settings = Settings.from_env({"PERSONAL_ASSISTANT_HOME": str(tmp_path)})
    assert settings == Settings(storage="json", data_dir=tmp_path)


def test_settings_storage_is_case_insensitive(tmp_path: Path) -> None:
    env = {"PERSONAL_ASSISTANT_HOME": str(tmp_path), "PERSONAL_ASSISTANT_STORAGE": " SQLite "}
    assert Settings.from_env(env).storage == "sqlite"


@pytest.mark.parametrize("name", ["json", "sqlite", "memory"])
def test_create_storage_returns_working_repositories(tmp_path: Path, name: str) -> None:
    bundle = create_storage(Settings(storage=name, data_dir=tmp_path))
    bundle.contacts.add(Contact.create(Name("Іван")))
    assert [c.name.value for c in bundle.contacts.list_all()] == ["Іван"]
    assert bundle.notes.list_all() == []
    assert bundle.quarantined == []
    bundle.close()


def test_json_backend_creates_expected_files(tmp_path: Path) -> None:
    bundle = create_storage(Settings(storage="json", data_dir=tmp_path))
    bundle.contacts.add(Contact.create(Name("Іван")))
    bundle.close()
    assert (tmp_path / "contacts.json").exists()


def test_sqlite_backend_creates_db_file(tmp_path: Path) -> None:
    create_storage(Settings(storage="sqlite", data_dir=tmp_path)).close()
    assert (tmp_path / "assistant.db").exists()


def test_unknown_backend_raises(tmp_path: Path) -> None:
    with pytest.raises(UnknownStorageBackendError) as info:
        create_storage(Settings(storage="mongo", data_dir=tmp_path))
    assert info.value.name == "mongo"


def test_quarantined_files_reported(tmp_path: Path) -> None:
    (tmp_path / "contacts.json").write_text("{broken", encoding="utf-8")
    bundle = create_storage(Settings(storage="json", data_dir=tmp_path))
    assert len(bundle.quarantined) == 1
    assert bundle.quarantined[0].name.startswith("contacts.corrupt-")


def test_system_clock_today_matches_now() -> None:
    clock = SystemClock()
    assert clock.now().tzinfo is not None
    assert clock.today() <= clock.now().date()
