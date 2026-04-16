import pytest
from lib.text import keyword_to_title, slugify


# ---------------------------------------------------------------------------
# slugify
# ---------------------------------------------------------------------------

def test_slugify_basic():
    assert slugify("Hello World") == "hello-world"


def test_slugify_strips_punctuation():
    assert slugify("best car!") == "best-car"


def test_slugify_collapses_spaces():
    assert slugify("a  b   c") == "a-b-c"


def test_slugify_replaces_underscores():
    assert slugify("foo_bar") == "foo-bar"


def test_slugify_strips_leading_trailing_hyphens():
    assert slugify("-hello-") == "hello"


def test_slugify_lowercases():
    assert slugify("HybridCar") == "hybridcar"


def test_slugify_empty_string():
    assert slugify("") == ""


def test_slugify_preserves_unicode_word_chars():
    # Python's \w matches unicode letters, so accented chars are preserved
    result = slugify("café")
    assert result == "café"


def test_slugify_numbers_preserved():
    assert slugify("Toyota 2024") == "toyota-2024"


# ---------------------------------------------------------------------------
# keyword_to_title
# ---------------------------------------------------------------------------

def test_keyword_to_title_capitalizes_first():
    assert keyword_to_title("hybrid battery") == "Hybrid Battery"


def test_keyword_to_title_stop_words_lowercase():
    assert keyword_to_title("best oil for a hybrid") == "Best Oil for a Hybrid"


def test_keyword_to_title_first_word_always_capitalized():
    # "the" is a stop word but must be capitalized at position 0
    assert keyword_to_title("the best hybrid") == "The Best Hybrid"


def test_keyword_to_title_single_word():
    assert keyword_to_title("hybrid") == "Hybrid"


def test_keyword_to_title_all_stops_except_first():
    # "a and the" — first word capitalised, rest are stops
    assert keyword_to_title("a and the") == "A and the"


def test_keyword_to_title_non_stop_words_all_capitalized():
    assert keyword_to_title("hybrid vehicle maintenance guide") == "Hybrid Vehicle Maintenance Guide"
