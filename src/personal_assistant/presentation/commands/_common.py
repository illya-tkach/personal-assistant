"""Small helpers shared by command handlers."""

from __future__ import annotations

from personal_assistant.presentation.registry import CommandContext


def text(raw: str) -> str:
    """Parser for free-text answers that only need trimming."""
    return raw.strip()


def success(ctx: CommandContext, message: str) -> None:
    ctx.console.print(f"[green]{message}[/green]", highlight=False)


def info(ctx: CommandContext, message: str) -> None:
    ctx.console.print(f"[dim]{message}[/dim]", highlight=False)
