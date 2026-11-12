"""Command registry and the context every command handler receives."""

from __future__ import annotations

import difflib
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from rich.console import Console

from personal_assistant.application.contact_service import ContactService
from personal_assistant.application.note_service import NoteService
from personal_assistant.application.ports import Clock
from personal_assistant.presentation.prompts import Prompter


class Outcome(Enum):
    CONTINUE = "continue"
    EXIT = "exit"


@dataclass
class CommandContext:
    contacts: ContactService
    notes: NoteService
    prompter: Prompter
    console: Console
    clock: Clock
    registry: CommandRegistry


Handler = Callable[[CommandContext], Outcome]


@dataclass(frozen=True)
class Command:
    name: str
    description: str
    handler: Handler
    aliases: tuple[str, ...] = ()


class CommandRegistry:
    def __init__(self) -> None:
        self._commands: list[Command] = []
        self._by_name: dict[str, Command] = {}

    def register(self, command: Command) -> None:
        for name in (command.name, *command.aliases):
            if name in self._by_name:
                raise ValueError(f"duplicate command name: {name}")
        self._commands.append(command)
        for name in (command.name, *command.aliases):
            self._by_name[name] = command

    def get(self, name: str) -> Command | None:
        return self._by_name.get(name)

    def names(self) -> list[str]:
        return list(self._by_name)

    def commands(self) -> list[Command]:
        return list(self._commands)

    def suggest(self, name: str) -> list[str]:
        return difflib.get_close_matches(name, self.names(), n=3, cutoff=0.6)
