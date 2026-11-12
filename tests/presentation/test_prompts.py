from __future__ import annotations

from collections.abc import Callable, Iterable

from rich.console import Console

from personal_assistant.domain.errors import DomainError, InvalidPhoneError, ValidationError
from personal_assistant.domain.value_objects import Email, Name, Phone
from personal_assistant.presentation.messages import error_message
from personal_assistant.presentation.prompts import Prompter


def scripted(answers: Iterable[str]) -> Callable[[str], str]:
    queue = list(answers)
    return lambda _label: queue.pop(0)


def prompter(*answers: str) -> tuple[Prompter, Console]:
    console = Console(record=True, width=120)
    return Prompter(scripted(answers), console), console


def test_ask_retries_until_valid() -> None:
    p, console = prompter("123", "0501234567")
    assert p.ask("Телефон", Phone) == Phone("0501234567")
    assert "Некоректний номер" in console.export_text()


def test_ask_retries_on_blank_required() -> None:
    p, console = prompter("", "  ", "Іван")
    assert p.ask("Ім'я", Name) == Name("Іван")
    assert console.export_text().count("обов'язкове") == 2


def test_ask_optional_blank_returns_none() -> None:
    p, _ = prompter("")
    assert p.ask_optional("Email", Email) is None


def test_ask_optional_retries_invalid() -> None:
    p, _ = prompter("bad", "a@b.com")
    assert p.ask_optional("Email", Email) == Email("a@b.com")


def test_ask_edit_blank_keeps_current() -> None:
    p, _ = prompter("")
    assert p.ask_edit("Email", Email, Email("a@b.com"), "a@b.com") == Email("a@b.com")


def test_ask_edit_dash_clears() -> None:
    p, _ = prompter("-")
    assert p.ask_edit("Email", Email, Email("a@b.com"), "a@b.com") is None


def test_ask_edit_dash_not_clearable_goes_to_parser() -> None:
    p, _ = prompter("-")
    assert p.ask_edit("Ім'я", Name, Name("Іван"), "Іван", clearable=False) == Name("-")


def test_ask_edit_new_value() -> None:
    p, _ = prompter("new@b.com")
    assert p.ask_edit("Email", Email, None, "") == Email("new@b.com")


def test_ask_edit_label_shows_current_value() -> None:
    labels: list[str] = []

    def record(label: str) -> str:
        labels.append(label)
        return ""

    Prompter(record, Console(record=True)).ask_edit("Email", Email, Email("a@b.com"), "a@b.com")
    assert "a@b.com" in labels[0]


def test_confirm() -> None:
    assert prompter("так")[0].confirm("Видалити?") is True
    assert prompter("Y")[0].confirm("Видалити?") is True
    assert prompter("n")[0].confirm("Видалити?") is False
    assert prompter("")[0].confirm("Видалити?") is False


def test_error_message_specific() -> None:
    assert "+380" in error_message(InvalidPhoneError("x"))


def test_error_message_falls_back_to_parent_class() -> None:
    class CustomValidationError(ValidationError):
        pass

    class CustomDomainError(DomainError):
        pass

    assert error_message(CustomValidationError()) == error_message(ValidationError())
    assert error_message(CustomDomainError()) == error_message(DomainError())
