from datetime import date
from typing import Any

import pytest

from personal_assistant.domain.contact import Contact
from personal_assistant.domain.errors import PhoneNotFoundError
from personal_assistant.domain.value_objects import Address, Birthday, Email, Name, Phone


def make(**kw: Any) -> Contact:
    return Contact.create(Name("Іван"), **kw)


def bd(iso: str) -> Birthday:
    return Birthday(date.fromisoformat(iso))


def test_create_generates_unique_ids() -> None:
    assert make().id != make().id


def test_create_dedupes_phones() -> None:
    c = make(phones=[Phone("0501234567"), Phone("+380501234567")])
    assert c.phones == [Phone("+380501234567")]


def test_add_phone_ignores_duplicate() -> None:
    c = make(phones=[Phone("0501234567")])
    c.add_phone(Phone("+380501234567"))
    assert len(c.phones) == 1


def test_add_phone_appends() -> None:
    c = make()
    c.add_phone(Phone("0501234567"))
    assert c.phones == [Phone("0501234567")]


def test_remove_phone() -> None:
    c = make(phones=[Phone("0501234567")])
    c.remove_phone(Phone("0501234567"))
    assert c.phones == []


def test_remove_missing_phone_raises() -> None:
    with pytest.raises(PhoneNotFoundError):
        make().remove_phone(Phone("0501234567"))


def test_set_phones_replaces_and_dedupes() -> None:
    c = make(phones=[Phone("0501234567")])
    c.set_phones([Phone("0671112233"), Phone("0671112233")])
    assert c.phones == [Phone("0671112233")]


def test_days_until_today_is_zero() -> None:
    assert make(birthday=bd("1990-11-12")).days_until_birthday(date(2026, 11, 12)) == 0


def test_days_until_later_this_year() -> None:
    assert make(birthday=bd("1990-11-20")).days_until_birthday(date(2026, 11, 12)) == 8


def test_days_until_wraps_new_year() -> None:
    assert make(birthday=bd("1990-01-02")).days_until_birthday(date(2026, 12, 30)) == 3


def test_feb29_in_non_leap_year_is_feb28() -> None:
    assert make(birthday=bd("2000-02-29")).next_birthday(date(2027, 2, 1)) == date(2027, 2, 28)


def test_feb29_in_leap_year_stays() -> None:
    assert make(birthday=bd("2000-02-29")).next_birthday(date(2028, 2, 1)) == date(2028, 2, 29)


def test_feb29_after_feb28_in_non_leap_year_moves_to_next_year() -> None:
    assert make(birthday=bd("2000-02-29")).next_birthday(date(2027, 3, 1)) == date(2028, 2, 29)


def test_age_on_next_birthday() -> None:
    assert make(birthday=bd("1990-01-02")).age_on_next_birthday(date(2026, 12, 30)) == 37


def test_no_birthday_returns_none() -> None:
    c = make()
    today = date(2026, 11, 12)
    assert c.days_until_birthday(today) is None
    assert c.next_birthday(today) is None
    assert c.age_on_next_birthday(today) is None


def test_matches_name_case_insensitive() -> None:
    assert Contact.create(Name("Іван Петренко")).matches("петрен")


def test_matches_phone_by_digits() -> None:
    assert make(phones=[Phone("0501234567")]).matches("050-123")


def test_matches_email_address_birthday() -> None:
    c = make(
        email=Email("ivan@mail.com"), address=Address("Київ, Хрещатик 1"), birthday=bd("1990-03-15")
    )
    assert c.matches("MAIL")
    assert c.matches("хрещатик")
    assert c.matches("15.03")


def test_query_without_digits_does_not_match_phone() -> None:
    assert not make(phones=[Phone("0501234567")]).matches("xyz")
