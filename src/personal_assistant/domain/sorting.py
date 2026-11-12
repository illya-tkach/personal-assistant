"""Alphabetical ordering that follows the Ukrainian alphabet.

Unicode code points put і, ї, є, ґ after я, so plain ``sorted`` is wrong for Ukrainian.
``locale.strxfrm`` is avoided because it behaves differently across operating systems.
"""

from __future__ import annotations

UKRAINIAN_ALPHABET = "абвгґдеєжзиіїйклмнопрстуфхцчшщьюя"
_CYRILLIC_BASE = ord(UKRAINIAN_ALPHABET[0])
_POSITIONS = {letter: index for index, letter in enumerate(UKRAINIAN_ALPHABET)}


def ukrainian_sort_key(text: str) -> tuple[tuple[int, int], ...]:
    """Case-insensitive key: Ukrainian letters by alphabet position, others by code point."""
    return tuple(
        (_CYRILLIC_BASE, _POSITIONS[char]) if char in _POSITIONS else (ord(char), 0)
        for char in text.casefold()
    )
