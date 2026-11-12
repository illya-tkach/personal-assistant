"""Step-by-step questions: each field is validated immediately and re-asked on error.

KeyboardInterrupt / EOFError from the input function are not handled here; the CLI loop
treats them as "cancel this command".
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TypeVar

from rich.console import Console

from personal_assistant.domain.errors import ValidationError
from personal_assistant.presentation import messages

T = TypeVar("T")
InputFn = Callable[[str], str]

CLEAR_MARKER = "-"
YES_ANSWERS = frozenset({"y", "yes", "т", "так"})


class Prompter:
    def __init__(self, input_fn: InputFn, console: Console) -> None:
        self._input = input_fn
        self._console = console

    def ask(self, label: str, parser: Callable[[str], T]) -> T:
        """Required field: blank or invalid input is reported and asked again."""
        while True:
            raw = self._input(f"{label}: ")
            if not raw.strip():
                self._error(messages.REQUIRED_FIELD)
                continue
            parsed = self._try_parse(raw, parser)
            if parsed is not None:
                return parsed[0]

    def ask_optional(self, label: str, parser: Callable[[str], T]) -> T | None:
        """Optional field: blank input means no value."""
        while True:
            raw = self._input(f"{label}: ")
            if not raw.strip():
                return None
            parsed = self._try_parse(raw, parser)
            if parsed is not None:
                return parsed[0]

    def ask_edit(
        self,
        label: str,
        parser: Callable[[str], T],
        current: T | None,
        current_display: str,
        clearable: bool = True,
    ) -> T | None:
        """Edit field: blank keeps ``current``; ``-`` clears it when ``clearable``."""
        while True:
            raw = self._input(f"{label} [{current_display}]: ")
            if not raw.strip():
                return current
            if clearable and raw.strip() == CLEAR_MARKER:
                return None
            parsed = self._try_parse(raw, parser)
            if parsed is not None:
                return parsed[0]

    def confirm(self, question: str) -> bool:
        return self._input(f"{question} ").strip().lower() in YES_ANSWERS

    def _try_parse(self, raw: str, parser: Callable[[str], T]) -> tuple[T] | None:
        try:
            return (parser(raw),)
        except ValidationError as exc:
            self._error(messages.error_message(exc))
            return None

    def _error(self, text: str) -> None:
        self._console.print(f"[red]✗ {text}[/red]", highlight=False)
