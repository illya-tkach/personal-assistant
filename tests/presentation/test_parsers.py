from __future__ import annotations

from datetime import date

import pytest

from personal_assistant.domain.errors import InvalidBirthdayError, InvalidPhoneError
from personal_assistant.domain.value_objects import Birthday, Phone, Tag
from personal_assistant.presentation.parsers import (
    InvalidNumberError,
    birthday_parser,
    parse_days,
    parse_phones,
    parse_positive_int,
    parse_tags,
    split_csv,
)


def test_split_csv() -> None:
    assert split_csv("a, ,b,") == ["a", "b"]


def test_parse_phones() -> None:
    assert parse_phones("0501234567, 067 111 22 33") == (Phone("0501234567"), Phone("0671112233"))


def test_parse_phones_rejects_any_invalid() -> None:
    with pytest.raises(InvalidPhoneError):
        parse_phones("0501234567, 123")


def test_parse_tags_dedupes() -> None:
    assert parse_tags("Work, #work") == frozenset({Tag("work")})


def test_birthday_parser_uses_today() -> None:
    parse = birthday_parser(date(2026, 11, 12))
    assert parse("12.11.2026") == Birthday(date(2026, 11, 12))
    with pytest.raises(InvalidBirthdayError):
        parse("13.11.2026")


@pytest.mark.parametrize("raw", ["abc", "-3", "1.5", "0", "", " "])
def test_parse_positive_int_rejects(raw: str) -> None:
    with pytest.raises(InvalidNumberError):
        parse_positive_int(raw)


def test_parse_positive_int_accepts() -> None:
    assert parse_positive_int(" 12 ") == 12


@pytest.mark.parametrize("raw", ["-1", "366", "x", "7.0"])
def test_parse_days_rejects(raw: str) -> None:
    with pytest.raises(InvalidNumberError):
        parse_days(raw)


def test_parse_days_accepts_0_and_365() -> None:
    assert (parse_days("0"), parse_days("365")) == (0, 365)
