"""Rich renderables for command output. Functions build, they never print."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text

from personal_assistant.application.contact_service import UpcomingBirthday
from personal_assistant.domain.contact import Contact
from personal_assistant.domain.note import Note
from personal_assistant.domain.value_objects import Tag
from personal_assistant.presentation import messages
from personal_assistant.presentation.registry import Command

DATETIME_FORMAT = "%d.%m.%Y %H:%M"
DATE_FORMAT = "%d.%m.%Y"


def nothing_found() -> Text:
    return Text(messages.NOTHING_FOUND, style="yellow")


def cell(value: str) -> Text:
    """User data is always rendered literally, never parsed as Rich markup."""
    return Text(value)


def format_tags(tags: frozenset[Tag]) -> str:
    return ", ".join(f"#{tag.value}" for tag in sorted(tags))


def contacts_table(contacts: Sequence[Contact]) -> RenderableType:
    if not contacts:
        return nothing_found()
    table = Table(title=messages.TITLE_CONTACTS, show_lines=True)
    for column in (
        messages.COL_NAME,
        messages.COL_PHONES,
        messages.COL_EMAIL,
        messages.COL_ADDRESS,
        messages.COL_BIRTHDAY,
    ):
        table.add_column(column)
    for contact in contacts:
        table.add_row(
            cell(contact.name.value),
            cell("\n".join(phone.value for phone in contact.phones)),
            cell(contact.email.value if contact.email else ""),
            cell(contact.address.value if contact.address else ""),
            cell(contact.birthday.format() if contact.birthday else ""),
        )
    return table


def birthdays_table(items: Sequence[UpcomingBirthday], days: int) -> RenderableType:
    if not items:
        return Text(messages.NO_BIRTHDAYS.format(days=days), style="yellow")
    table = Table(title=messages.TITLE_BIRTHDAYS)
    for column in (messages.COL_NAME, messages.COL_DATE, messages.COL_IN_DAYS, messages.COL_AGE):
        table.add_column(column)
    for item in items:
        when = (
            messages.TODAY
            if item.days_until == 0
            else messages.IN_DAYS.format(days=item.days_until)
        )
        table.add_row(
            cell(item.contact.name.value), item.date.strftime(DATE_FORMAT), when, str(item.age)
        )
    return table


def notes_table(notes: Sequence[Note], title: str | Text = messages.TITLE_NOTES) -> RenderableType:
    if not notes:
        return nothing_found()
    table = Table(title=title, show_lines=True)
    table.add_column(messages.COL_ID, justify="right")
    table.add_column(messages.COL_TEXT)
    table.add_column(messages.COL_TAGS)
    table.add_column(messages.COL_CREATED)
    for note in notes:
        table.add_row(
            str(note.id),
            cell(note.text),
            cell(format_tags(note.tags)),
            note.created_at.strftime(DATETIME_FORMAT),
        )
    return table


def notes_by_tag_view(groups: Mapping[Tag | None, Sequence[Note]]) -> RenderableType:
    if not groups:
        return nothing_found()
    return Group(
        *(
            notes_table(notes, title=cell(f"#{tag.value}" if tag else messages.UNTAGGED))
            for tag, notes in groups.items()
        )
    )


def help_table(commands: Sequence[Command]) -> RenderableType:
    table = Table(title=messages.TITLE_HELP)
    table.add_column(messages.COL_COMMAND, style="bold cyan")
    table.add_column(messages.COL_DESCRIPTION)
    for command in commands:
        table.add_row(command.name, command.description)
    return table
