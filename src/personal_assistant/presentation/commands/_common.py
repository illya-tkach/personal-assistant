"""Small helpers shared by command handlers."""

from __future__ import annotations

from rich.text import Text

from personal_assistant.presentation.registry import CommandContext


def text(raw: str) -> str:
    """Parser for free-text answers that only need trimming."""
    return raw.strip()


def success(ctx: CommandContext, message: str) -> None:
    ctx.console.print(Text(message, style="green"))


def info(ctx: CommandContext, message: str) -> None:
    ctx.console.print(Text(message, style="dim"))
