"""User text that looks like Rich markup must be shown literally and never crash."""

from __future__ import annotations

from personal_assistant.presentation.cli import AssistantCLI
from personal_assistant.presentation.registry import Outcome
from tests.presentation.conftest import Harness


def cli(h: Harness) -> AssistantCLI:
    return AssistantCLI(h.context.registry, h.context, lambda: "exit")


def test_contact_name_with_markup_is_shown_literally(harness: Harness) -> None:
    harness.say("Bob[/green]", "", "", "", "")
    assert cli(harness).handle_line("add-contact") is Outcome.CONTINUE
    assert "Bob[/green]" in harness.output()
    cli(harness).handle_line("list-contacts")  # output() above cleared the record buffer
    assert "│ Bob[/green] │" in harness.output()


def test_note_text_with_brackets_is_listed_intact(harness: Harness) -> None:
    harness.say("see [/] here", "")
    cli(harness).handle_line("add-note")
    harness.say("buy milk [urgent] now", "")
    cli(harness).handle_line("add-note")
    for command in ("list-notes", "notes-by-tag"):
        assert cli(harness).handle_line(command) is Outcome.CONTINUE
    out = harness.output()
    assert "see [/] here" in out
    assert "buy milk [urgent] now" in out
    assert "неочікувана" not in out


def test_error_message_with_markup_does_not_crash(harness: Harness) -> None:
    harness.say("X[/red]")
    assert cli(harness).handle_line("delete-contact") is Outcome.CONTINUE
    assert "X[/red]" in harness.output()


def test_validation_message_for_markup_input_does_not_crash(harness: Harness) -> None:
    harness.say("[bold]", "0501234567")
    from personal_assistant.domain.value_objects import Phone

    assert harness.context.prompter.ask("Телефон", Phone) == Phone("0501234567")
