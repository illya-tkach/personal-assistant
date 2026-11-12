from personal_assistant.domain.sorting import ukrainian_sort_key


def test_ukrainian_alphabet_order() -> None:
    words = ["Яна", "Ірина", "Євген", "Ґанна", "Андрій", "Гліб", "їжак", "Ілля"]
    assert sorted(words, key=ukrainian_sort_key) == [
        "Андрій", "Гліб", "Ґанна", "Євген", "Ілля", "Ірина", "їжак", "Яна",
    ]  # fmt: skip


def test_case_insensitive() -> None:
    assert ukrainian_sort_key("Іван") == ukrainian_sort_key("іван")


def test_latin_before_cyrillic_and_digits_first() -> None:
    assert sorted(["Яна", "Bob", "2pac"], key=ukrainian_sort_key) == ["2pac", "Bob", "Яна"]
