"""Domain error hierarchy. Errors carry no UI text; presentation maps them to messages."""

from __future__ import annotations


class DomainError(Exception):
    """Base class for every error raised by the domain and its ports."""


class ValidationError(DomainError):
    """Input does not satisfy a domain rule."""


class InvalidNameError(ValidationError):
    pass


class InvalidPhoneError(ValidationError):
    pass


class InvalidEmailError(ValidationError):
    pass


class InvalidBirthdayError(ValidationError):
    pass


class InvalidAddressError(ValidationError):
    pass


class InvalidTagError(ValidationError):
    pass


class InvalidNoteTextError(ValidationError):
    pass


class InvalidDaysError(ValidationError):
    pass


class NotFoundError(DomainError):
    """Requested record does not exist."""


class ContactNotFoundError(NotFoundError):
    pass


class NoteNotFoundError(NotFoundError):
    pass


class PhoneNotFoundError(NotFoundError):
    pass


class DuplicateContactError(DomainError):
    """A contact with the same name (case-insensitive) already exists."""


class StorageError(DomainError):
    """Persistent storage failed to read or write."""


class UnknownStorageBackendError(StorageError):
    """Configured storage backend name is not registered."""

    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.name = name
