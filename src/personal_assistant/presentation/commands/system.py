"""help and exit."""

from __future__ import annotations

from personal_assistant.presentation import messages
from personal_assistant.presentation.io import views
from personal_assistant.presentation.registry import Command, CommandContext, Outcome


def show_help(ctx: CommandContext) -> Outcome:
    ctx.console.print(views.help_table(ctx.registry.commands()))
    return Outcome.CONTINUE


def exit_app(ctx: CommandContext) -> Outcome:
    return Outcome.EXIT


SYSTEM_COMMANDS = (
    Command("help", messages.HELP_HELP, show_help),
    Command("exit", messages.HELP_EXIT, exit_app, aliases=("close",)),
)
