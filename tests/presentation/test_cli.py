from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from personal_assistant.main import main
from personal_assistant.presentation.cli import AssistantCLI
from personal_assistant.presentation.registry import Command, CommandContext, Outcome
from tests.presentation.conftest import Harness


def reader(*lines: str | BaseException) -> Callable[[], str]:
    queue = list(lines)

    def read() -> str:
        item = queue.pop(0)
        if isinstance(item, BaseException):
            raise item
        return item

    return read


def cli(h: Harness, *lines: str | BaseException) -> AssistantCLI:
    return AssistantCLI(h.context.registry, h.context, reader(*lines))


def test_unknown_command_suggests(harness: Harness) -> None:
    assert cli(harness).handle_line("add-contct") is Outcome.CONTINUE
    out = harness.output()
    assert "Можливо, ви мали на увазі" in out and "add-contact" in out


def test_unknown_command_without_close_match(harness: Harness) -> None:
    cli(harness).handle_line("zzz")
    assert "Введіть help" in harness.output()


def test_empty_line_is_ignored(harness: Harness) -> None:
    assert cli(harness).handle_line("   ") is Outcome.CONTINUE
    assert harness.output() == ""


def test_command_is_case_insensitive_and_ignores_args(harness: Harness) -> None:
    cli(harness).handle_line("HELP me")
    assert "add-contact" in harness.output()


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt(), EOFError()])
def test_interrupt_in_wizard_cancels_and_continues(
    harness: Harness, interrupt: BaseException
) -> None:
    harness.say("Іван", interrupt)
    assert cli(harness).handle_line("add-contact") is Outcome.CONTINUE
    assert "Скасовано" in harness.output()
    assert harness.context.contacts.list_all() == []


def test_domain_error_shown_without_traceback(harness: Harness) -> None:
    harness.say("Ніхто")
    cli(harness).handle_line("delete-contact")
    out = harness.output()
    assert "Контакт «Ніхто» не знайдено" in out
    assert "Traceback" not in out


def test_unexpected_error_is_caught(harness: Harness) -> None:
    def boom(ctx: CommandContext) -> Outcome:
        raise RuntimeError("boom")

    harness.context.registry.register(Command("boom", "", boom))
    assert cli(harness).handle_line("boom") is Outcome.CONTINUE
    assert "Сталася неочікувана помилка: boom" in harness.output()


@pytest.mark.parametrize("interrupt", [KeyboardInterrupt(), EOFError()])
def test_run_exits_on_interrupt_at_prompt(harness: Harness, interrupt: BaseException) -> None:
    cli(harness, "help", interrupt).run()
    out = harness.output()
    assert "Вітаю" in out and "До побачення" in out


def test_run_exits_on_exit_command(harness: Harness) -> None:
    cli(harness, "close", "help").run()  # "help" is never read
    assert "До побачення" in harness.output()
    assert "Доступні команди" not in harness.output()


def test_main_returns_1_on_unknown_backend(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    env = {"PERSONAL_ASSISTANT_STORAGE": "mongo", "PERSONAL_ASSISTANT_HOME": str(tmp_path)}
    assert main(env) == 1
    assert "mongo" in capsys.readouterr().out


def test_main_returns_1_on_corrupt_sqlite(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "assistant.db").write_bytes(b"garbage" * 200)
    env = {"PERSONAL_ASSISTANT_STORAGE": "sqlite", "PERSONAL_ASSISTANT_HOME": str(tmp_path)}
    assert main(env) == 1
    assert "Traceback" not in capsys.readouterr().out
