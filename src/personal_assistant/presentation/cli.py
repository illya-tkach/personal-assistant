"""The read-dispatch loop. The only place that turns exceptions into messages."""

from __future__ import annotations

from collections.abc import Callable

from personal_assistant.domain.errors import DomainError
from personal_assistant.presentation import messages
from personal_assistant.presentation.registry import CommandContext, CommandRegistry, Outcome


class AssistantCLI:
    def __init__(
        self,
        registry: CommandRegistry,
        context: CommandContext,
        read_command: Callable[[], str],
    ) -> None:
        self._registry = registry
        self._context = context
        self._read_command = read_command
        self._console = context.console

    def run(self) -> None:
        self._console.print(messages.WELCOME, highlight=False)
        while True:
            try:
                line = self._read_command()
            except (KeyboardInterrupt, EOFError):
                break
            if self.handle_line(line) is Outcome.EXIT:
                break
        self._console.print(messages.GOODBYE, highlight=False)

    def handle_line(self, line: str) -> Outcome:
        """Run the command named by the first word; arguments are ignored (commands ask)."""
        words = line.split()
        if not words:
            return Outcome.CONTINUE
        name = words[0].lower()
        command = self._registry.get(name)
        if command is None:
            self._report_unknown(name)
            return Outcome.CONTINUE
        try:
            return command.handler(self._context)
        except (KeyboardInterrupt, EOFError):
            self._console.print(f"[yellow]{messages.CANCELLED}[/yellow]", highlight=False)
        except DomainError as exc:
            self._error(messages.error_message(exc))
        except Exception as exc:
            self._error(messages.UNEXPECTED_ERROR.format(error=exc))
        return Outcome.CONTINUE

    def _report_unknown(self, name: str) -> None:
        suggestions = self._registry.suggest(name)
        if suggestions:
            self._error(messages.UNKNOWN_COMMAND.format(suggestions=", ".join(suggestions)))
        else:
            self._error(messages.UNKNOWN_COMMAND_NO_SUGGESTIONS)

    def _error(self, text: str) -> None:
        self._console.print(f"[red]✗ {text}[/red]", highlight=False)
