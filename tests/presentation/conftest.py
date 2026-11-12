from __future__ import annotations

from dataclasses import dataclass, field

import pytest
from rich.console import Console

from personal_assistant.application.contact_service import ContactService
from personal_assistant.application.note_service import NoteService
from personal_assistant.infrastructure.memory_repositories import (
    InMemoryContactRepository,
    InMemoryNoteRepository,
)
from personal_assistant.presentation.commands import build_registry
from personal_assistant.presentation.prompts import Prompter
from personal_assistant.presentation.registry import CommandContext
from tests.conftest import FixedClock


@dataclass
class Harness:
    """Real services on in-memory storage, scripted user input, recorded output."""

    context: CommandContext
    console: Console
    answers: list[str | BaseException] = field(default_factory=list)

    def say(self, *answers: str | BaseException) -> None:
        self.answers.extend(answers)

    def output(self) -> str:
        return self.console.export_text()

    def run(self, command: str) -> object:
        cmd = self.context.registry.get(command)
        assert cmd is not None, command
        return cmd.handler(self.context)


@pytest.fixture
def harness(clock: FixedClock) -> Harness:
    console = Console(record=True, width=140)
    answers: list[str | BaseException] = []

    def input_fn(_label: str) -> str:
        answer = answers.pop(0)
        if isinstance(answer, BaseException):
            raise answer
        return answer

    context = CommandContext(
        contacts=ContactService(InMemoryContactRepository(), clock),
        notes=NoteService(InMemoryNoteRepository(), clock),
        prompter=Prompter(input_fn, console),
        console=console,
        clock=clock,
        registry=build_registry(),
    )
    return Harness(context, console, answers)
