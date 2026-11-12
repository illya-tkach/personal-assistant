"""All user-facing text (Ukrainian) and the mapping from domain errors to messages."""

from __future__ import annotations

from personal_assistant.domain.errors import (
    ContactNotFoundError,
    DomainError,
    DuplicateContactError,
    InvalidAddressError,
    InvalidBirthdayError,
    InvalidDaysError,
    InvalidEmailError,
    InvalidNameError,
    InvalidNoteTextError,
    InvalidPhoneError,
    InvalidTagError,
    NoteNotFoundError,
    NotFoundError,
    PhoneNotFoundError,
    StorageError,
    UnknownStorageBackendError,
    ValidationError,
)
from personal_assistant.presentation.parsers import InvalidNumberError

WELCOME = "Вітаю! Я ваш персональний помічник. Введіть help, щоб побачити список команд."
GOODBYE = "До побачення!"
PROMPT = ">>> "
UNKNOWN_COMMAND = "Невідома команда. Можливо, ви мали на увазі: {suggestions}"
UNKNOWN_COMMAND_NO_SUGGESTIONS = "Невідома команда. Введіть help, щоб побачити список команд"
UNEXPECTED_ERROR = "Сталася неочікувана помилка: {error}"
CANCELLED = "Скасовано"
REQUIRED_FIELD = "Це поле обов'язкове"
EDIT_HINT = "Enter — залишити без змін, «-» — очистити поле"
NOTHING_FOUND = "Нічого не знайдено"
STORAGE_QUARANTINED = (
    "Файл даних пошкоджено, його збережено як {path}. Роботу продовжено з порожнім списком."
)
STORAGE_START_FAILED = "Не вдалося відкрити сховище даних: {error}"

# Prompts
ASK_NAME = "Ім'я"
ASK_NEW_NAME = "Ім'я"
ASK_PHONES = "Телефони через кому (Enter — пропустити)"
ASK_PHONES_EDIT = "Телефони через кому"
ASK_EMAIL = "Email (Enter — пропустити)"
ASK_EMAIL_EDIT = "Email"
ASK_ADDRESS = "Адреса (Enter — пропустити)"
ASK_ADDRESS_EDIT = "Адреса"
ASK_BIRTHDAY = "День народження ДД.ММ.РРРР (Enter — пропустити)"
ASK_BIRTHDAY_EDIT = "День народження ДД.ММ.РРРР"
ASK_CONTACT_NAME = "Ім'я контакту"
ASK_QUERY = "Що шукаємо"
ASK_DAYS = "Через скільки днів (0–365)"
ASK_NOTE_TEXT = "Текст нотатки"
ASK_NOTE_TEXT_EDIT = "Текст нотатки"
ASK_TAGS = "Теги через кому (Enter — пропустити)"
ASK_TAGS_EDIT = "Теги через кому"
ASK_TAGS_SEARCH = "Теги через кому"
ASK_NOTE_ID = "ID нотатки"
CONFIRM_DELETE_CONTACT = "Видалити контакт «{name}»? (y/n)"
CONFIRM_DELETE_NOTE = "Видалити нотатку #{id}? (y/n)"

# Results
CONTACT_ADDED = "✓ Контакт «{name}» додано"
CONTACT_UPDATED = "✓ Контакт «{name}» оновлено"
CONTACT_DELETED = "✓ Контакт «{name}» видалено"
NOTE_ADDED = "✓ Нотатку #{id} додано"
NOTE_UPDATED = "✓ Нотатку #{id} оновлено"
NOTE_DELETED = "✓ Нотатку #{id} видалено"
NO_BIRTHDAYS = "Немає днів народження в найближчі {days} дн."
UNTAGGED = "без тегів"

# Table headers
COL_NAME = "Ім'я"
COL_PHONES = "Телефони"
COL_EMAIL = "Email"
COL_ADDRESS = "Адреса"
COL_BIRTHDAY = "День народження"
COL_DATE = "Дата"
COL_IN_DAYS = "Через"
COL_AGE = "Виповниться"
COL_ID = "ID"
COL_TEXT = "Текст"
COL_TAGS = "Теги"
COL_CREATED = "Створено"
COL_COMMAND = "Команда"
COL_DESCRIPTION = "Опис"
IN_DAYS = "{days} дн."
TODAY = "сьогодні"
TITLE_CONTACTS = "Контакти"
TITLE_BIRTHDAYS = "Дні народження"
TITLE_NOTES = "Нотатки"
TITLE_HELP = "Доступні команди"

# Command descriptions
HELP_HELP = "Показати список команд"
HELP_EXIT = "Вийти з програми (також close)"
HELP_ADD_CONTACT = "Додати контакт"
HELP_LIST_CONTACTS = "Показати всі контакти"
HELP_SEARCH_CONTACTS = "Знайти контакти за ім'ям, телефоном, email, адресою чи датою"
HELP_EDIT_CONTACT = "Редагувати контакт"
HELP_DELETE_CONTACT = "Видалити контакт"
HELP_BIRTHDAYS = "Дні народження через задану кількість днів"
HELP_ADD_NOTE = "Додати нотатку"
HELP_LIST_NOTES = "Показати всі нотатки"
HELP_SEARCH_NOTES = "Знайти нотатки за текстом або тегом"
HELP_EDIT_NOTE = "Редагувати нотатку"
HELP_DELETE_NOTE = "Видалити нотатку"
HELP_SEARCH_TAG = "Знайти нотатки, що мають усі задані теги"
HELP_NOTES_BY_TAG = "Нотатки, згруповані за тегами"

ERROR_MESSAGES: dict[type[DomainError], str] = {
    DomainError: "Помилка: {detail}",
    ValidationError: "Некоректне значення",
    InvalidNameError: "Ім'я має бути непорожнім і не довшим за 50 символів",
    InvalidPhoneError: "Некоректний номер телефону. Формат: +380XXXXXXXXX або 0XXXXXXXXX",
    InvalidEmailError: "Некоректний email. Приклад: ivan@mail.com",
    InvalidBirthdayError: (
        "Некоректна дата. Формат: ДД.ММ.РРРР, не в майбутньому й не раніше 1900 року"
    ),
    InvalidAddressError: "Адреса має бути непорожньою і не довшою за 200 символів",
    InvalidTagError: "Тег — одне слово без пробілів, до 30 символів (наприклад: робота)",
    InvalidNoteTextError: "Текст нотатки не може бути порожнім",
    InvalidDaysError: "Кількість днів має бути від 0 до 365",
    InvalidNumberError: "Введіть ціле число в допустимих межах",
    NotFoundError: "Не знайдено",
    ContactNotFoundError: "Контакт «{detail}» не знайдено",
    NoteNotFoundError: "Нотатку #{detail} не знайдено",
    PhoneNotFoundError: "Телефон {detail} не знайдено",
    DuplicateContactError: "Контакт з ім'ям «{detail}» уже існує",
    StorageError: "Помилка сховища даних: {detail}",
    UnknownStorageBackendError: (
        "Невідомий тип сховища «{detail}». Доступні: json, sqlite, memory"
    ),
}


def error_message(exc: DomainError) -> str:
    """Message for the most specific registered class in the exception's MRO."""
    for cls in type(exc).__mro__:
        template = ERROR_MESSAGES.get(cls)
        if template is not None:
            return template.format(detail=exc)
    return str(exc)  # pragma: no cover - DomainError is always registered
