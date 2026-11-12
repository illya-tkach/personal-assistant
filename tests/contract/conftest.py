"""Shared fixtures: every storage backend must pass the same contract tests.

Each fixture returns a factory; calling it again re-opens the *same* storage,
which lets tests check that data survives a restart.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

import pytest

from personal_assistant.application.ports import ContactRepository, NoteRepository
from personal_assistant.infrastructure.memory_repositories import (
    InMemoryContactRepository,
    InMemoryNoteRepository,
)

BACKENDS = ["memory"]


@pytest.fixture(params=BACKENDS)
def backend(request: pytest.FixtureRequest) -> str:
    return str(request.param)


@pytest.fixture
def contact_repo_factory(backend: str, tmp_path: Path) -> Iterator[Callable[[], ContactRepository]]:
    if backend == "memory":
        repo = InMemoryContactRepository()
        yield lambda: repo
    else:  # pragma: no cover - extended by later backends
        raise AssertionError(backend)


@pytest.fixture
def note_repo_factory(backend: str, tmp_path: Path) -> Iterator[Callable[[], NoteRepository]]:
    if backend == "memory":
        repo = InMemoryNoteRepository()
        yield lambda: repo
    else:  # pragma: no cover - extended by later backends
        raise AssertionError(backend)


@pytest.fixture
def skip_if_memory(backend: str) -> None:
    if backend == "memory":
        pytest.skip("in-memory storage does not survive a restart")
