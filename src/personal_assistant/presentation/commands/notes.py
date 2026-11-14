"""Note command handlers: ask, call the service, show the result. No business logic."""

from __future__ import annotations

from personal_assistant.domain.note import validate_note_text
from personal_assistant.presentation import messages
from personal_assistant.presentation.commands._common import info, success, text
from personal_assistant.presentation.io import views
from personal_assistant.presentation.io.parsers import parse_positive_int, parse_tags
from personal_assistant.presentation.registry import Command, CommandContext, Outcome


def add_note(ctx: CommandContext) -> Outcome:
    note_text = ctx.prompter.ask(messages.ASK_NOTE_TEXT, validate_note_text)
    tags = ctx.prompter.ask_optional(messages.ASK_TAGS, parse_tags) or frozenset()
    note = ctx.notes.add(note_text, tags)
    success(ctx, messages.NOTE_ADDED.format(id=note.id))
    return Outcome.CONTINUE


def list_notes(ctx: CommandContext) -> Outcome:
    ctx.console.print(views.notes_table(ctx.notes.list_all()))
    return Outcome.CONTINUE


def search_notes(ctx: CommandContext) -> Outcome:
    query = ctx.prompter.ask(messages.ASK_QUERY, text)
    ctx.console.print(views.notes_table(ctx.notes.search(query)))
    return Outcome.CONTINUE


def edit_note(ctx: CommandContext) -> Outcome:
    ask = ctx.prompter
    note = ctx.notes.get(ask.ask(messages.ASK_NOTE_ID, parse_positive_int))
    info(ctx, messages.EDIT_HINT)
    new_text = ask.ask_edit(
        messages.ASK_NOTE_TEXT_EDIT, validate_note_text, note.text, note.text, clearable=False
    )
    tags = ask.ask_edit(messages.ASK_TAGS_EDIT, parse_tags, note.tags, views.format_tags(note.tags))
    ctx.notes.update(note.id, text=new_text, tags=tags or frozenset())
    success(ctx, messages.NOTE_UPDATED.format(id=note.id))
    return Outcome.CONTINUE


def delete_note(ctx: CommandContext) -> Outcome:
    note = ctx.notes.get(ctx.prompter.ask(messages.ASK_NOTE_ID, parse_positive_int))
    if not ctx.prompter.confirm(messages.CONFIRM_DELETE_NOTE.format(id=note.id)):
        info(ctx, messages.CANCELLED)
        return Outcome.CONTINUE
    ctx.notes.delete(note.id)
    success(ctx, messages.NOTE_DELETED.format(id=note.id))
    return Outcome.CONTINUE


def search_tag(ctx: CommandContext) -> Outcome:
    tags = ctx.prompter.ask(messages.ASK_TAGS_SEARCH, parse_tags)
    ctx.console.print(views.notes_table(ctx.notes.find_by_tags(tags)))
    return Outcome.CONTINUE


def notes_by_tag(ctx: CommandContext) -> Outcome:
    ctx.console.print(views.notes_by_tag_view(ctx.notes.group_by_tags()))
    return Outcome.CONTINUE


NOTE_COMMANDS = (
    Command("add-note", messages.HELP_ADD_NOTE, add_note),
    Command("list-notes", messages.HELP_LIST_NOTES, list_notes),
    Command("search-notes", messages.HELP_SEARCH_NOTES, search_notes),
    Command("edit-note", messages.HELP_EDIT_NOTE, edit_note),
    Command("delete-note", messages.HELP_DELETE_NOTE, delete_note),
    Command("search-tag", messages.HELP_SEARCH_TAG, search_tag),
    Command("notes-by-tag", messages.HELP_NOTES_BY_TAG, notes_by_tag),
)
