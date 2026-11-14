"""Turn raw user input into validated domain values. Raise ValidationError subclasses."""

from __future__ import annotations

import re
from collections.abc import Callable
from datetime import date

from personal_assistant.domain.errors import ValidationError
from personal_assistant.domain.value_objects import Birthday, Phone, Tag

MAX_DAYS = 365


class InvalidNumberError(ValidationError):
    """Input is not a whole number in the allowed range."""


def split_csv(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def parse_phones(raw: str) -> tuple[Phone, ...]:
    return tuple(dict.fromkeys(Phone(part) for part in split_csv(raw)))


def parse_tags(raw: str) -> frozenset[Tag]:
    return frozenset(Tag(part) for part in split_csv(raw))


def birthday_parser(today: date) -> Callable[[str], Birthday]:
    return lambda raw: Birthday.parse(raw, today)


def _parse_int(raw: str, minimum: int, maximum: int | None) -> int:
    cleaned = raw.strip()
    if not re.fullmatch(r"\d+", cleaned):
        raise InvalidNumberError(raw)
    value = int(cleaned)
    if value < minimum or (maximum is not None and value > maximum):
        raise InvalidNumberError(raw)
    return value


def parse_positive_int(raw: str) -> int:
    return _parse_int(raw, 1, None)


def parse_days(raw: str) -> int:
    return _parse_int(raw, 0, MAX_DAYS)
