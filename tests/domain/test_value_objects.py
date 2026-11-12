from datetime import date

import pytest

from personal_assistant.domain.errors import (
    InvalidAddressError,
    InvalidBirthdayError,
    InvalidEmailError,
    InvalidNameError,
    InvalidPhoneError,
    InvalidTagError,
)
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone, Tag

TODAY = date(2026, 11, 12)


@pytest.mark.parametrize(
    "raw",
    [
        "+380501234567",
        "380501234567",
        "0501234567",
        "050 123 45 67",
        "(050) 123-45-67",
        "+38 (050) 123-45-67",
    ],
)
def test_phone_normalizes_to_plus380(raw: str) -> None:
    assert Phone(raw).value == "+380501234567"


@pytest.mark.parametrize(
    "raw",
    ["", "12345", "050123456", "05012345678", "+1501234567", "abc0501234567", "+3805012345678"],
)
def test_phone_rejects_invalid(raw: str) -> None:
    with pytest.raises(InvalidPhoneError):
        Phone(raw)


def test_phone_digits() -> None:
    assert Phone("0501234567").digits == "380501234567"


def test_email_lowercases() -> None:
    assert Email("  Ivan@Mail.COM ").value == "ivan@mail.com"


@pytest.mark.parametrize(
    "raw",
    ["", "ivan", "ivan@", "@mail.com", "ivan@mail", "iv an@mail.com", "a@@mail.com", "ivan@mail.c"],
)
def test_email_rejects_invalid(raw: str) -> None:
    with pytest.raises(InvalidEmailError):
        Email(raw)


def test_name_strips() -> None:
    assert Name("  Іван Петренко ").value == "Іван Петренко"


@pytest.mark.parametrize("raw", ["", "   ", "x" * 51])
def test_name_rejects_invalid(raw: str) -> None:
    with pytest.raises(InvalidNameError):
        Name(raw)


def test_name_allows_50_chars() -> None:
    assert len(Name("x" * 50).value) == 50


def test_address_strips() -> None:
    assert Address("  Київ ").value == "Київ"


def test_address_rejects_201_chars() -> None:
    with pytest.raises(InvalidAddressError):
        Address("x" * 201)


def test_address_rejects_blank() -> None:
    with pytest.raises(InvalidAddressError):
        Address("  ")


def test_tag_normalizes() -> None:
    assert Tag("  #Work ").value == "work"


@pytest.mark.parametrize("raw", ["", "#", "two words", "x" * 31])
def test_tag_rejects_invalid(raw: str) -> None:
    with pytest.raises(InvalidTagError):
        Tag(raw)


def test_tags_sort_alphabetically() -> None:
    assert sorted([Tag("b"), Tag("a")]) == [Tag("a"), Tag("b")]


def test_birthday_parse() -> None:
    assert Birthday.parse("15.03.1990", TODAY).value == date(1990, 3, 15)


def test_birthday_format() -> None:
    assert Birthday(date(1990, 3, 5)).format() == "05.03.1990"


@pytest.mark.parametrize(
    "raw", ["1990-03-15", "32.01.1990", "29.02.2025", "13.11.2026", "31.12.1899", ""]
)
def test_birthday_rejects_invalid(raw: str) -> None:
    with pytest.raises(InvalidBirthdayError):
        Birthday.parse(raw, TODAY)


def test_birthday_today_is_allowed() -> None:
    assert Birthday.parse("12.11.2026", TODAY).value == TODAY


def test_birthday_before_1900_rejected_on_construction() -> None:
    with pytest.raises(InvalidBirthdayError):
        Birthday(date(1899, 12, 31))
