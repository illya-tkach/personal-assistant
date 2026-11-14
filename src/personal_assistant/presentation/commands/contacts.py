"""Contact command handlers: ask, call the service, show the result. No business logic."""

from __future__ import annotations

from personal_assistant.application.contact_service import ContactData
from personal_assistant.domain.value_objects import Address, Email, Name
from personal_assistant.presentation import messages
from personal_assistant.presentation.commands._common import info, success, text
from personal_assistant.presentation.io import views
from personal_assistant.presentation.io.parsers import birthday_parser, parse_days, parse_phones
from personal_assistant.presentation.registry import Command, CommandContext, Outcome


def add_contact(ctx: CommandContext) -> Outcome:
    ask = ctx.prompter
    data = ContactData(
        name=ask.ask(messages.ASK_NAME, Name),
        phones=ask.ask_optional(messages.ASK_PHONES, parse_phones) or (),
        email=ask.ask_optional(messages.ASK_EMAIL, Email),
        address=ask.ask_optional(messages.ASK_ADDRESS, Address),
        birthday=ask.ask_optional(messages.ASK_BIRTHDAY, birthday_parser(ctx.clock.today())),
    )
    contact = ctx.contacts.add(data)
    success(ctx, messages.CONTACT_ADDED.format(name=contact.name.value))
    return Outcome.CONTINUE


def list_contacts(ctx: CommandContext) -> Outcome:
    ctx.console.print(views.contacts_table(ctx.contacts.list_all()))
    return Outcome.CONTINUE


def search_contacts(ctx: CommandContext) -> Outcome:
    query = ctx.prompter.ask(messages.ASK_QUERY, text)
    ctx.console.print(views.contacts_table(ctx.contacts.search(query)))
    return Outcome.CONTINUE


def edit_contact(ctx: CommandContext) -> Outcome:
    ask = ctx.prompter
    contact = ctx.contacts.get(ask.ask(messages.ASK_CONTACT_NAME, text))
    info(ctx, messages.EDIT_HINT)
    email, address, birthday = contact.email, contact.address, contact.birthday
    data = ContactData(
        name=ask.ask_edit(
            messages.ASK_NEW_NAME, Name, contact.name, contact.name.value, clearable=False
        )
        or contact.name,
        phones=ask.ask_edit(
            messages.ASK_PHONES_EDIT,
            parse_phones,
            tuple(contact.phones),
            ", ".join(phone.value for phone in contact.phones),
        )
        or (),
        email=ask.ask_edit(messages.ASK_EMAIL_EDIT, Email, email, email.value if email else ""),
        address=ask.ask_edit(
            messages.ASK_ADDRESS_EDIT, Address, address, address.value if address else ""
        ),
        birthday=ask.ask_edit(
            messages.ASK_BIRTHDAY_EDIT,
            birthday_parser(ctx.clock.today()),
            birthday,
            birthday.format() if birthday else "",
        ),
    )
    updated = ctx.contacts.update(contact.name.value, data)
    success(ctx, messages.CONTACT_UPDATED.format(name=updated.name.value))
    return Outcome.CONTINUE


def delete_contact(ctx: CommandContext) -> Outcome:
    contact = ctx.contacts.get(ctx.prompter.ask(messages.ASK_CONTACT_NAME, text))
    if not ctx.prompter.confirm(messages.CONFIRM_DELETE_CONTACT.format(name=contact.name.value)):
        info(ctx, messages.CANCELLED)
        return Outcome.CONTINUE
    ctx.contacts.delete(contact.name.value)
    success(ctx, messages.CONTACT_DELETED.format(name=contact.name.value))
    return Outcome.CONTINUE


def birthdays(ctx: CommandContext) -> Outcome:
    days = ctx.prompter.ask(messages.ASK_DAYS, parse_days)
    ctx.console.print(views.birthdays_table(ctx.contacts.upcoming_birthdays(days), days))
    return Outcome.CONTINUE


CONTACT_COMMANDS = (
    Command("add-contact", messages.HELP_ADD_CONTACT, add_contact),
    Command("list-contacts", messages.HELP_LIST_CONTACTS, list_contacts),
    Command("search-contacts", messages.HELP_SEARCH_CONTACTS, search_contacts),
    Command("edit-contact", messages.HELP_EDIT_CONTACT, edit_contact),
    Command("delete-contact", messages.HELP_DELETE_CONTACT, delete_contact),
    Command("birthdays", messages.HELP_BIRTHDAYS, birthdays),
)
