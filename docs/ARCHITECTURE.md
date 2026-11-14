# Архітектура персонального помічника

Документ описує, як влаштований код: пакети, ключові класи, залежності між шарами і
шлях однієї команди від введення до збереження. Як встановити й запустити програму,
описано в [README](../README.md).

## Зміст

1. [Загальна ідея](#1-загальна-ідея)
2. [Структура пакетів](#2-структура-пакетів)
3. [Залежності між шарами](#3-залежності-між-шарами)
4. [Домен](#4-домен)
5. [Застосунок: сервіси й порти](#5-застосунок-сервіси-й-порти)
6. [Інфраструктура: сховища](#6-інфраструктура-сховища)
7. [Презентація: CLI](#7-презентація-cli)
8. [Як усе збирається: main.py](#8-як-усе-збирається-mainpy)
9. [Шлях однієї команди](#9-шлях-однієї-команди)
10. [Обробка помилок](#10-обробка-помилок)
11. [Тести](#11-тести)
12. [Як розширювати](#12-як-розширювати)

## 1. Загальна ідея

Проєкт побудований як **шарова архітектура «порти й адаптери»** (hexagonal architecture):

- **Домен** містить сутності й правила, наприклад «телефон складається з 10 цифр» чи
  «ім'я контакту унікальне». Він нічого не знає ні про файли, ні про консоль.
- **Застосунок** містить сценарії використання (додати контакт, знайти нотатки за тегом)
  і **порти**: інтерфейси, через які сценарії звертаються до зовнішнього світу.
- **Інфраструктура** містить **адаптери**, тобто реалізації портів: JSON-файли, SQLite,
  пам'ять, системний годинник.
- **Презентація** — це консольний інтерфейс: питає користувача, викликає сервіси,
  показує результат.

Залежності спрямовані **лише всередину**, до домену. Тому сховище можна замінити, не
чіпаючи бізнес-логіки, а домен і сервіси тестуються без файлів і консолі.

## 2. Структура пакетів

```
src/personal_assistant/
├── main.py                      composition root: створює й з'єднує всі об'єкти
│
├── domain/                      ── ДОМЕН (без I/O) ──
│   ├── contact.py               Contact, ContactId: телефони, дні народження, пошук
│   ├── note.py                  Note, NewNote: текст, теги, час створення й зміни
│   ├── value_objects.py         Name, Phone, Email, Address, Tag, Birthday: валідація в конструкторі
│   ├── errors.py                ієрархія DomainError
│   └── sorting.py               ukrainian_sort_key: сортування за українською абеткою
│
├── application/                 ── ЗАСТОСУНОК ──
│   ├── ports.py                 ContactRepository, NoteRepository, Clock (typing.Protocol)
│   ├── contact_service.py       ContactService, ContactData, UpcomingBirthday
│   └── note_service.py          NoteService
│
├── infrastructure/              ── ІНФРАСТРУКТУРА ──
│   ├── factory.py               Settings, StorageBundle, STORAGE_BACKENDS, create_storage
│   ├── clock.py                 SystemClock: реальна дата й час
│   ├── paths.py                 resolve_data_dir: каталог даних
│   └── storage/
│       ├── memory/
│       │   └── repositories.py  InMemoryContactRepository, InMemoryNoteRepository
│       ├── json/
│       │   ├── file.py          JsonFile: атомарний запис, карантин пошкодженого файлу
│       │   ├── contact_repository.py   JsonContactRepository
│       │   └── note_repository.py      JsonNoteRepository
│       └── sqlite/
│           ├── database.py      SqliteDatabase: з'єднання, схема, storage_errors
│           ├── contact_repository.py   SqliteContactRepository
│           └── note_repository.py      SqliteNoteRepository
│
└── presentation/                ── ПРЕЗЕНТАЦІЯ (CLI) ──
    ├── cli.py                   AssistantCLI: цикл команд, перетворення помилок на повідомлення
    ├── registry.py              Command, CommandRegistry, CommandContext, Outcome
    ├── messages.py              усі тексти українською, ERROR_MESSAGES
    ├── commands/
    │   ├── __init__.py          build_registry()
    │   ├── contacts.py          add-contact, list-contacts, search-contacts, edit-contact, delete-contact, birthdays
    │   ├── notes.py             add-note, list-notes, search-notes, edit-note, delete-note, search-tag, notes-by-tag
    │   ├── system.py            help, exit / close
    │   └── _common.py           дрібні допоміжні функції для обробників
    └── io/
        ├── prompts.py           Prompter: покрокові запитання з повтором при помилці
        ├── parsers.py           розбір відповідей: телефони й теги через кому, числа, дати
        └── views.py             таблиці rich для контактів, нотаток, днів народження, help
```

## 3. Залежності між шарами

```mermaid
flowchart TD
    main["main.py<br/><i>composition root</i>"]

    subgraph presentation["presentation"]
        cli["cli · registry · commands"]
        io["io: prompts · parsers · views"]
        msg["messages"]
    end

    subgraph application["application"]
        services["ContactService · NoteService"]
        ports["ports: ContactRepository · NoteRepository · Clock"]
    end

    subgraph infrastructure["infrastructure"]
        factory["factory · clock · paths"]
        storage["storage: json · sqlite · memory"]
    end

    subgraph domain["domain"]
        entities["Contact · Note · value objects · errors · sorting"]
    end

    main --> presentation
    main --> application
    main --> infrastructure

    presentation --> application
    presentation --> domain
    services --> ports
    application --> domain
    infrastructure -. "реалізує" .-> ports
    infrastructure --> domain
```

Правила:

| Шар | Може імпортувати | Не може імпортувати |
|---|---|---|
| `domain` | лише стандартну бібліотеку | будь-який інший шар, `rich`, `prompt_toolkit` |
| `application` | `domain` | `infrastructure`, `presentation` |
| `infrastructure` | `domain`, `application.ports` | `presentation`, сервіси |
| `presentation` | `domain`, `application` | `infrastructure` |
| `main.py` | усе | — |

Ключовий момент: **сервіси залежать від портів, а не від конкретних сховищ**. Хто саме
реалізує порт (JSON, SQLite чи пам'ять), вирішує лише `main.py` через `factory.py`.
Це інверсія залежностей (принцип **D** із SOLID).

## 4. Домен

### Сутності та value objects

```mermaid
classDiagram
    direction LR

    class Contact {
        +ContactId id
        +Name name
        +list~Phone~ phones
        +Email email [optional]
        +Address address [optional]
        +Birthday birthday [optional]
        +create(name, phones, email, address, birthday)$ Contact
        +add_phone(phone)
        +remove_phone(phone)
        +set_phones(phones)
        +next_birthday(today) date
        +days_until_birthday(today) int
        +age_on_next_birthday(today) int
        +matches(query) bool
    }

    class NewNote {
        <<frozen>>
        +str text
        +frozenset~Tag~ tags
        +datetime created_at
    }

    class Note {
        +int id
        +str text
        +frozenset~Tag~ tags
        +datetime created_at
        +datetime updated_at
        +from_draft(note_id, draft)$ Note
        +edit_text(text, now)
        +set_tags(tags, now)
        +matches(query) bool
        +has_all_tags(tags) bool
    }

    class Name {
        <<value object>>
        +str value
    }
    class Phone {
        <<value object>>
        +str value
        +digits() str
    }
    class Email {
        <<value object>>
        +str value
    }
    class Address {
        <<value object>>
        +str value
    }
    class Tag {
        <<value object>>
        +str value
    }
    class Birthday {
        <<value object>>
        +date value
        +parse(raw, today)$ Birthday
        +format() str
    }

    Contact *-- "1" Name
    Contact *-- "0..*" Phone
    Contact *-- "0..1" Email
    Contact *-- "0..1" Address
    Contact *-- "0..1" Birthday
    Note *-- "0..*" Tag
    NewNote *-- "0..*" Tag
    NewNote ..> Note : from_draft()
```

- **Value objects** (`value_objects.py`) — незмінні `frozen dataclass`. Значення
  перевіряється в `__post_init__`, і в разі помилки конструктор кидає відповідний
  `ValidationError`. Тобто **невалідний `Phone` неможливо створити**. Тому решта коду
  не перевіряє дані повторно, а `Prompter` просто передає конструктор як парсер.
- **`Contact`** — змінна сутність з ідентифікатором `ContactId` (UUID). Вона сама знає,
  коли наступний день народження, скільки років виповниться і чи підходить контакт під
  пошуковий запит.
- **`NewNote` і `Note`.** Нотатка отримує `id` лише після збереження: сховище видає
  номер, який ніколи не повторюється. Тому сервіс створює чернетку `NewNote`, а
  репозиторій повертає вже повну `Note`.
- **`sorting.ukrainian_sort_key`** сортує імена й теги за українською абеткою. Звичайний
  `sorted` ставить «і, ї, є, ґ» не на свої місця, а `locale` поводиться по-різному на
  різних ОС.

### Ієрархія помилок

```mermaid
classDiagram
    direction TB
    Exception <|-- DomainError
    DomainError <|-- ValidationError
    DomainError <|-- NotFoundError
    DomainError <|-- DuplicateContactError
    DomainError <|-- StorageError

    ValidationError <|-- InvalidNameError
    ValidationError <|-- InvalidPhoneError
    ValidationError <|-- InvalidEmailError
    ValidationError <|-- InvalidBirthdayError
    ValidationError <|-- InvalidAddressError
    ValidationError <|-- InvalidTagError
    ValidationError <|-- InvalidNoteTextError
    ValidationError <|-- InvalidDaysError
    ValidationError <|-- InvalidNumberError

    NotFoundError <|-- ContactNotFoundError
    NotFoundError <|-- NoteNotFoundError
    NotFoundError <|-- PhoneNotFoundError

    StorageError <|-- UnknownStorageBackendError

    class InvalidNumberError {
        <<presentation.io.parsers>>
    }
```

Помилки несуть **лише деталь** (наприклад, невалідне значення), а не текст для
користувача. Український текст до кожного класу визначено в
`presentation/messages.py::ERROR_MESSAGES`. Так домен не залежить від мови інтерфейсу.

## 5. Застосунок: сервіси й порти

```mermaid
classDiagram
    direction LR

    class ContactRepository {
        <<Protocol>>
        +add(contact)
        +get(contact_id) Contact
        +find_by_name(name) Contact
        +list_all() list~Contact~
        +update(contact)
        +delete(contact_id)
    }
    class NoteRepository {
        <<Protocol>>
        +add(draft: NewNote) Note
        +get(note_id) Note
        +list_all() list~Note~
        +update(note)
        +delete(note_id)
    }
    class Clock {
        <<Protocol>>
        +now() datetime
        +today() date
    }

    class ContactService {
        +add(data: ContactData) Contact
        +get(name) Contact
        +list_all() list~Contact~
        +search(query) list~Contact~
        +update(name, data) Contact
        +delete(name)
        +upcoming_birthdays(days) list~UpcomingBirthday~
    }
    class NoteService {
        +add(text, tags) Note
        +get(note_id) Note
        +list_all() list~Note~
        +search(query) list~Note~
        +update(note_id, text, tags) Note
        +delete(note_id)
        +find_by_tags(tags) list~Note~
        +group_by_tags() dict
    }
    class ContactData {
        <<frozen>>
        name, phones, email, address, birthday
    }
    class UpcomingBirthday {
        <<frozen>>
        contact, date, days_until, age
    }

    ContactService --> ContactRepository
    ContactService --> Clock
    NoteService --> NoteRepository
    NoteService --> Clock
    ContactService ..> ContactData : приймає
    ContactService ..> UpcomingBirthday : повертає
```

- **Порти** описані як `typing.Protocol` (структурна типізація). Адаптери не
  успадковують протокол: достатньо мати методи з потрібними сигнатурами, а mypy
  (`--strict`) перевіряє відповідність там, де адаптер передають у сервіс.
- Репозиторії працюють **на рівні окремих записів** (add/get/update/delete), а не
  «завантажити й зберегти весь файл». Завдяки цьому один інтерфейс однаково природно
  лягає і на JSON-файл, і на SQL-таблицю.
- **`Clock`** — теж порт. Сервіси не викликають `datetime.now()` напряму, тому в тестах
  «сьогодні» зафіксовано (`FixedClock`, 12.11.2026), і тести днів народження
  детерміновані.
- Сервіси відповідають за сценарії: сортування результатів, пошук, перевірку діапазону
  днів (0–365), групування нотаток за тегами.

## 6. Інфраструктура: сховища

### Адаптери портів

```mermaid
classDiagram
    direction TB

    class ContactRepository {
        <<Protocol>>
    }
    class NoteRepository {
        <<Protocol>>
    }

    class InMemoryContactRepository {
        -dict _contacts
        #_commit(state)
    }
    class InMemoryNoteRepository {
        -dict _notes
        -int _next_id
        #_commit(state, next_id)
    }
    class JsonContactRepository {
        +Path quarantined
        #_load()
        #_commit(state)
    }
    class JsonNoteRepository {
        +Path quarantined
        #_load()
        #_commit(state, next_id)
    }
    class JsonFile {
        +read() dict
        +write(data)
        +quarantine() Path
    }
    class SqliteDatabase {
        +Connection connection
        +close()
    }
    class SqliteContactRepository
    class SqliteNoteRepository

    ContactRepository <|.. InMemoryContactRepository
    ContactRepository <|.. SqliteContactRepository
    NoteRepository <|.. InMemoryNoteRepository
    NoteRepository <|.. SqliteNoteRepository

    InMemoryContactRepository <|-- JsonContactRepository
    InMemoryNoteRepository <|-- JsonNoteRepository
    JsonContactRepository --> JsonFile
    JsonNoteRepository --> JsonFile
    SqliteContactRepository --> SqliteDatabase
    SqliteNoteRepository --> SqliteDatabase
```

Три бекенди, і кожен реалізує обидва порти:

| Бекенд | Де лежать дані | Особливості |
|---|---|---|
| `json` (за замовчуванням) | `~/.personal_assistant/contacts.json`, `notes.json` | атомарний запис, карантин пошкоджених файлів |
| `sqlite` | `~/.personal_assistant/assistant.db` | `sqlite3` зі стандартної бібліотеки, без ORM; одне з'єднання на весь запуск |
| `memory` | лише в пам'яті | нічого не зберігає; використовується в тестах і як база для JSON |

Бекенд обирається змінною `PERSONAL_ASSISTANT_STORAGE`, каталог даних —
змінною `PERSONAL_ASSISTANT_HOME`.

**Як JSON спирається на in-memory.** In-memory репозиторій ніколи не змінює свій стан
напряму: він готує нову копію стану і передає її в `_commit(state)`. JSON-репозиторій
перевизначає `_commit`: спершу записує файл, і лише якщо запис вдався, викликає
`super()._commit(state)`. Тому, якщо диск видав помилку, дані в пам'яті не
розходяться з файлом.

### Завантаження й запис JSON

```mermaid
flowchart TD
    start(["JsonContactRepository(JsonFile)"]) --> read["JsonFile.read()"]
    read -->|файлу немає| empty["порожній стан"]
    read -->|OSError| storage_err["StorageError → програма повідомляє й завершується"]
    read -->|дані прочитано| parse["contact_from_dict для кожного запису<br/>(value objects перевіряють значення)"]
    parse -->|усе коректно| ok["стан у пам'яті"]
    read -->|"CorruptFileError: зіпсований JSON"| quarantine
    parse -->|"немає ключа, невалідне значення<br/>(LOAD_ERRORS)"| quarantine["JsonFile.quarantine()<br/>contacts.json → contacts.corrupt-#lt;час#gt;.json"]
    quarantine --> empty2["порожній стан +<br/>StorageBundle.quarantined"]
    empty2 --> warn["main.py показує жовте попередження"]
```

Запис атомарний: дані пишуться в тимчасовий файл у тому самому каталозі, далі
`fsync` і `os.replace`. Якщо програма впаде посеред запису, старий файл лишиться цілим.

Формат файлу:

```json
{
  "version": 1,
  "items": [
    {
      "id": "3f2a…",
      "name": "Олена",
      "phones": ["0501234567"],
      "email": "olena@example.com",
      "address": null,
      "birthday": "1990-11-20"
    }
  ]
}
```

### Схема SQLite

```mermaid
erDiagram
    contacts ||--o{ contact_phones : має
    notes ||--o{ note_tags : має

    contacts {
        TEXT id PK
        TEXT name
        TEXT name_key UK "casefold імені, гарантує унікальність"
        TEXT email
        TEXT address
        TEXT birthday "ISO-дата"
    }
    contact_phones {
        TEXT contact_id FK
        TEXT phone
        INTEGER position "порядок телефонів"
    }
    notes {
        INTEGER id PK "AUTOINCREMENT, id не повторюються"
        TEXT text
        TEXT created_at
        TEXT updated_at
    }
    note_tags {
        INTEGER note_id FK
        TEXT tag
    }
```

Зовнішні ключі мають `ON DELETE CASCADE`. Порушення `UNIQUE(name_key)`
перетворюється на `DuplicateContactError`, будь-яка інша помилка `sqlite3` — на
`StorageError` (через `storage_errors()`).

### Фабрика

`factory.py` зіставляє назву бекенду з функцією-будівником:

```python
STORAGE_BACKENDS = {"json": _json_storage, "sqlite": _sqlite_storage, "memory": _memory_storage}
```

Будівник повертає `StorageBundle`: обидва репозиторії, список файлів, відправлених у
карантин, і функцію `close`. Невідома назва бекенду дає `UnknownStorageBackendError`.

## 7. Презентація: CLI

```mermaid
classDiagram
    direction LR

    class AssistantCLI {
        +run()
        +handle_line(line) Outcome
    }
    class CommandRegistry {
        +register(command)
        +get(name) Command
        +names() list
        +commands() list
        +suggest(name) list
    }
    class Command {
        <<frozen>>
        +str name
        +str description
        +Handler handler
        +tuple aliases
    }
    class CommandContext {
        +ContactService contacts
        +NoteService notes
        +Prompter prompter
        +Console console
        +Clock clock
        +CommandRegistry registry
    }
    class Prompter {
        +ask(label, parser) T
        +ask_optional(label, parser) T
        +ask_edit(label, parser, current, current_display) T
        +confirm(question) bool
    }
    class Outcome {
        <<enum>>
        CONTINUE
        EXIT
    }

    AssistantCLI --> CommandRegistry
    AssistantCLI --> CommandContext
    CommandRegistry o-- "*" Command
    Command ..> CommandContext : handler(ctx)
    Command ..> Outcome : повертає
    CommandContext --> Prompter
```

- **Команди без аргументів.** Користувач вводить лише назву, наприклад `add-contact`, а
  обробник питає поля по одному через `Prompter`. Якщо введене значення не проходить
  перевірку, `Prompter` показує помилку і питає знову.
- **Парсер — це будь-яка функція `str → T`.** Найчастіше це конструктор value object
  (`Name`, `Email`) або функція з `io/parsers.py` (`parse_phones`, `parse_tags`,
  `parse_days`).
- **Обробник команди** робить три кроки: питає дані, викликає сервіс, друкує результат
  через `views`. Бізнес-логіки в ньому немає.
- **`CommandRegistry`** зберігає команди та їхні псевдоніми (`exit` / `close`) і пропонує
  схожі назви через `difflib`, якщо команду введено з помилкою.
- **Тексти** зібрано в `messages.py`, а користувацькі дані виводяться лише через
  `rich.text.Text`, тобто буквально. Тому ім'я на кшталт `[red]Олег` не зламає
  розмітку Rich.

## 8. Як усе збирається: main.py

`main.py` — **composition root**: єдине місце, яке знає всі шари й створює конкретні
об'єкти.

```mermaid
sequenceDiagram
    autonumber
    participant M as main()
    participant F as factory
    participant S as Services
    participant C as AssistantCLI

    M->>F: create_storage(Settings.from_env(os.environ))
    F-->>M: StorageBundle(contacts, notes, quarantined, close)
    alt сховище не відкрилось
        M->>M: друкує помилку, exit code 1
    end
    M->>M: попередження про файли в карантині
    M->>S: ContactService(storage.contacts, SystemClock())<br/>NoteService(storage.notes, SystemClock())
    M->>M: build_registry(), Prompter, CommandContext
    M->>C: AssistantCLI(registry, context, read_command).run()
    C-->>M: користувач ввів exit або Ctrl+D
    M->>F: storage.close()
```

## 9. Шлях однієї команди

Як приклад візьмемо `add-contact` з JSON-сховищем:

```mermaid
sequenceDiagram
    autonumber
    actor U as Користувач
    participant CLI as AssistantCLI
    participant H as add_contact()
    participant P as Prompter
    participant VO as Name / Email / …
    participant CS as ContactService
    participant R as JsonContactRepository
    participant JF as JsonFile

    U->>CLI: add-contact
    CLI->>H: handler(ctx)
    H->>P: ask("Ім'я", Name)
    P->>U: Ім'я:
    U-->>P: Олена
    P->>VO: Name("Олена")
    VO-->>P: Name ✓
    Note over P,VO: невалідне значення → ValidationError →<br/>Prompter показує помилку й питає знову
    H->>P: ask_optional(телефони, email, адреса, день народження)
    H->>CS: add(ContactData)
    CS->>CS: Contact.create(...)
    CS->>R: add(contact)
    R->>R: перевірка унікальності імені
    R->>JF: write({version, items})
    JF-->>R: атомарно записано
    R->>R: super()._commit(state)
    CS-->>H: Contact
    H->>U: ✓ Контакт «Олена» додано
    H-->>CLI: Outcome.CONTINUE
```

## 10. Обробка помилок

Помилки не перехоплюються там, де виникли: вони піднімаються до
**`AssistantCLI.handle_line`**, єдиного місця, де виняток стає повідомленням:

```mermaid
flowchart LR
    h["handler(ctx)"] --> q{виняток?}
    q -->|немає| ok["Outcome"]
    q -->|DomainError| m["messages.error_message(exc)<br/>✗ червоне повідомлення"]
    q -->|KeyboardInterrupt / EOFError| c["«Скасовано»"]
    q -->|будь-який інший| g["«Сталася неочікувана помилка»"]
    m & c & g --> cont["Outcome.CONTINUE: програма працює далі"]
```

`ValidationError` під час введення ловить сам `Prompter` і питає знову. До
`handle_line` такі помилки доходять, лише коли їх кидає сервіс (наприклад,
`DuplicateContactError`).

## 11. Тести

```
tests/
├── conftest.py              FixedClock: «сьогодні» = 12.11.2026
├── domain/                  value objects, Contact, Note, сортування
├── application/             сервіси на in-memory репозиторіях
├── contract/                один набір тестів для всіх бекендів (json, sqlite, memory)
├── infrastructure/          особливості JSON (карантин, атомарність), SQLite, фабрика
└── presentation/            CLI зі сценарієм відповідей (фікстура harness), безпека розмітки
```

**Контрактні тести** (`tests/contract/`) доводять, що бекенди взаємозамінні: ті самі
тести проганяються для кожного з них. Фікстура повертає фабрику. Якщо викликати її
вдруге, сховище відкриється знову, і так перевіряється, що дані переживають
перезапуск.

## 12. Як розширювати

**Новий бекенд сховища** (наприклад, PostgreSQL):

1. Пакет `infrastructure/storage/postgres/` із класами, що реалізують
   `ContactRepository` і `NoteRepository` і кидають лише доменні помилки.
2. Функція-будівник і запис у `STORAGE_BACKENDS` у `infrastructure/factory.py`.
3. Бекенд у `BACKENDS` і обох фабриках у `tests/contract/conftest.py`.

Домен, сервіси й CLI не змінюються.

**Нова команда:**

1. Функція-обробник `def my_command(ctx: CommandContext) -> Outcome` у
   відповідному файлі `presentation/commands/`.
2. Запис `Command("my-command", messages.HELP_MY_COMMAND, my_command)` у кортежі
   `*_COMMANDS` цього файлу.
3. Тексти запитань і результатів у `messages.py`.

**Нова доменна помилка:** клас у `domain/errors.py` і запис у
`messages.ERROR_MESSAGES`.
