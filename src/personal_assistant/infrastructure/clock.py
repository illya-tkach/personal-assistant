"""System clock implementation of the Clock port."""

from __future__ import annotations

from datetime import date, datetime


class SystemClock:
    def now(self) -> datetime:
        return datetime.now().astimezone()

    def today(self) -> date:
        return date.today()
