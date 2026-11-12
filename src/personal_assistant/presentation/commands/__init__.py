"""All CLI commands, collected into one registry."""

from __future__ import annotations

from personal_assistant.presentation.commands.contacts import CONTACT_COMMANDS
from personal_assistant.presentation.commands.notes import NOTE_COMMANDS
from personal_assistant.presentation.commands.system import SYSTEM_COMMANDS
from personal_assistant.presentation.registry import CommandRegistry


def build_registry() -> CommandRegistry:
    registry = CommandRegistry()
    for command in (*SYSTEM_COMMANDS, *CONTACT_COMMANDS, *NOTE_COMMANDS):
        registry.register(command)
    return registry
