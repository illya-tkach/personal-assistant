"""Atomic JSON file access with corruption detection."""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any

from personal_assistant.domain.errors import StorageError, ValidationError

SCHEMA_VERSION = 1


class CorruptFileError(Exception):
    """The file exists but does not hold a readable JSON object. Internal to infrastructure."""


class JsonFile:
    def __init__(self, path: Path) -> None:
        self.path = path

    def read(self) -> dict[str, Any] | None:
        """Return the parsed object, or None if the file does not exist."""
        try:
            text = self.path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        except UnicodeDecodeError as exc:
            raise CorruptFileError(str(self.path)) from exc
        except OSError as exc:
            raise StorageError(str(self.path)) from exc
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CorruptFileError(str(self.path)) from exc
        if not isinstance(data, dict):
            raise CorruptFileError(str(self.path))
        return data

    def write(self, data: dict[str, Any]) -> None:
        """Write atomically: temp file in the same directory, fsync, then os.replace."""
        tmp_name: str | None = None
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w",
                encoding="utf-8",
                dir=self.path.parent,
                prefix=f".{self.path.stem}-",
                suffix=".tmp",
                delete=False,
            ) as tmp:
                tmp_name = tmp.name
                json.dump(data, tmp, ensure_ascii=False, indent=2)
                tmp.flush()
                os.fsync(tmp.fileno())
            os.replace(tmp_name, self.path)
        except OSError as exc:
            if tmp_name is not None:
                Path(tmp_name).unlink(missing_ok=True)
            raise StorageError(str(self.path)) from exc

    def quarantine(self) -> Path:
        """Move an unreadable file aside so the app can start with empty data."""
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S")
        target = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}.json")
        counter = 1
        while target.exists():
            target = self.path.with_name(f"{self.path.stem}.corrupt-{stamp}-{counter}.json")
            counter += 1
        try:
            os.replace(self.path, target)
        except OSError as exc:
            raise StorageError(str(self.path)) from exc
        return target


def require(value: Any, kind: type[Any]) -> Any:
    """Raise TypeError when a value loaded from JSON has an unexpected type."""
    if not isinstance(value, kind):
        raise TypeError(f"expected {kind.__name__}, got {type(value).__name__}")
    return value


# Anything that means "the file content is unusable" (as opposed to an I/O failure).
LOAD_ERRORS: tuple[type[Exception], ...] = (
    CorruptFileError,
    KeyError,
    TypeError,
    ValueError,
    ValidationError,
)
