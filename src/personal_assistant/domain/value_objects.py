"""Immutable, self-validating value objects."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime

from personal_assistant.domain.errors import (
    InvalidAddressError,
    InvalidBirthdayError,
    InvalidEmailError,
    InvalidNameError,
    InvalidPhoneError,
    InvalidTagError,
)

NAME_MAX_LENGTH = 50
ADDRESS_MAX_LENGTH = 200
TAG_MAX_LENGTH = 30
MIN_BIRTH_YEAR = 1900
BIRTHDAY_FORMAT = "%d.%m.%Y"

_PHONE_NOISE = re.compile(r"[\s\-()]")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")


def _set(obj: object, value: object) -> None:
    object.__setattr__(obj, "value", value)


@dataclass(frozen=True)
class Name:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned or len(cleaned) > NAME_MAX_LENGTH:
            raise InvalidNameError(self.value)
        _set(self, cleaned)


@dataclass(frozen=True)
class Phone:
    """Ukrainian phone number, always stored as +380XXXXXXXXX."""

    value: str

    def __post_init__(self) -> None:
        _set(self, _normalize_phone(self.value))

    @property
    def digits(self) -> str:
        return self.value[1:]


def _normalize_phone(raw: str) -> str:
    compact = _PHONE_NOISE.sub("", raw)
    if re.fullmatch(r"\+380\d{9}", compact):
        return compact
    if re.fullmatch(r"380\d{9}", compact):
        return "+" + compact
    if re.fullmatch(r"0\d{9}", compact):
        return "+38" + compact
    raise InvalidPhoneError(raw)


@dataclass(frozen=True)
class Email:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip().lower()
        if not _EMAIL_PATTERN.fullmatch(cleaned):
            raise InvalidEmailError(self.value)
        _set(self, cleaned)


@dataclass(frozen=True)
class Address:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip()
        if not cleaned or len(cleaned) > ADDRESS_MAX_LENGTH:
            raise InvalidAddressError(self.value)
        _set(self, cleaned)


@dataclass(frozen=True, order=True)
class Tag:
    value: str

    def __post_init__(self) -> None:
        cleaned = self.value.strip().lstrip("#").lower()
        if not cleaned or len(cleaned) > TAG_MAX_LENGTH or re.search(r"\s", cleaned):
            raise InvalidTagError(self.value)
        _set(self, cleaned)


@dataclass(frozen=True)
class Birthday:
    value: date

    def __post_init__(self) -> None:
        if self.value.year < MIN_BIRTH_YEAR:
            raise InvalidBirthdayError(self.value.isoformat())

    @classmethod
    def parse(cls, raw: str, today: date) -> Birthday:
        """Parse DD.MM.YYYY; the date may not be in the future."""
        try:
            parsed = datetime.strptime(raw.strip(), BIRTHDAY_FORMAT).date()
        except ValueError as exc:
            raise InvalidBirthdayError(raw) from exc
        if parsed > today:
            raise InvalidBirthdayError(raw)
        return cls(parsed)

    def format(self) -> str:
        return self.value.strftime(BIRTHDAY_FORMAT)
