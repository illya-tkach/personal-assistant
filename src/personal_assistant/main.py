"""Composition root: the only module that knows every layer."""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from rich.console import Console

from personal_assistant.application.contact_service import ContactService
from personal_assistant.application.note_service import NoteService
from personal_assistant.domain.errors import StorageError
from personal_assistant.infrastructure.clock import SystemClock
from personal_assistant.infrastructure.factory import Settings, StorageBundle, create_storage
from personal_assistant.presentation import messages
from personal_assistant.presentation.cli import AssistantCLI
from personal_assistant.presentation.commands import build_registry
from personal_assistant.presentation.prompts import Prompter
from personal_assistant.presentation.registry import CommandContext


def _open_storage(env: Mapping[str, str], console: Console) -> StorageBundle | None:
    try:
        return create_storage(Settings.from_env(env))
    except StorageError as exc:
        error = messages.error_message(exc)
    except OSError as exc:
        error = str(exc)
    console.print(f"[red]{messages.STORAGE_START_FAILED.format(error=error)}[/red]")
    return None


def main(env: Mapping[str, str] | None = None) -> int:
    console = Console()
    storage = _open_storage(os.environ if env is None else env, console)
    if storage is None:
        return 1
    try:
        for path in storage.quarantined:
            console.print(f"[yellow]{messages.STORAGE_QUARANTINED.format(path=path)}[/yellow]")
        clock = SystemClock()
        registry = build_registry()
        field_session: PromptSession[str] = PromptSession()
        command_session: PromptSession[str] = PromptSession(
            completer=WordCompleter(registry.names(), ignore_case=True)
        )
        context = CommandContext(
            contacts=ContactService(storage.contacts, clock),
            notes=NoteService(storage.notes, clock),
            prompter=Prompter(field_session.prompt, console),
            console=console,
            clock=clock,
            registry=registry,
        )
        AssistantCLI(registry, context, lambda: command_session.prompt(messages.PROMPT)).run()
    finally:
        storage.close()
    return 0


def run() -> None:
    sys.exit(main())
