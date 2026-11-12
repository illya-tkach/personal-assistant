from __future__ import annotations

from datetime import date, datetime, timezone

import pytest


class FixedClock:
    """Test clock that always returns the same moment."""

    def __init__(self, now: datetime) -> None:
        self._now = now

    def now(self) -> datetime:
        return self._now

    def today(self) -> date:
        return self._now.date()


@pytest.fixture
def clock() -> FixedClock:
    return FixedClock(datetime(2026, 11, 12, 10, 0, tzinfo=timezone.utc))
