import re
from pathlib import Path

import pytest

from file_re import Match, Pattern, file_re

ROOT = Path(__file__).parent

file_types = [
    "simple_file.txt",
    "simple_file.txt.gz",
    "simple_file.txt.xz",
]


@pytest.mark.parametrize("file_name", file_types)
def test_compile_returns_pattern_and_search(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    pattern = file_re.compile(r"(\d{3})-(\d{3})-(\d{4})")

    assert isinstance(pattern, Pattern)

    match = pattern.search(simple_file)
    assert isinstance(match, Match)
    assert match.group(0) == "123-456-7890"


@pytest.mark.parametrize("file_name", file_types)
def test_pattern_match(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    pattern = file_re.compile(r"Welcome")

    match = pattern.match(simple_file)
    assert match is not None
    assert match.start() == 0

    no_match_pattern = file_re.compile(r"This library")
    assert no_match_pattern.match(simple_file) is None


@pytest.mark.parametrize("file_name", file_types)
def test_pattern_findall(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    pattern = file_re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    )

    emails = pattern.findall(simple_file)
    assert len(emails) == 4
    assert set(emails) == {f"user{i}@example.com" for i in range(1, 5)}


@pytest.mark.parametrize("file_name", file_types)
def test_pattern_finditer(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    pattern = file_re.compile(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"
    )

    matches = list(pattern.finditer(simple_file))
    assert len(matches) == 4
    assert all(isinstance(m, Match) for m in matches)


def test_pattern_accessors_return_originals():
    pattern = file_re.compile(r"(\d{3})-\w+", flags=re.IGNORECASE)

    assert pattern.pattern == r"(\d{3})-\w+"
    assert pattern.flags == re.IGNORECASE


def test_pattern_repr_includes_source():
    pattern = file_re.compile(r"hello_world")

    representation = repr(pattern)
    assert "hello_world" in representation


def test_compile_invalid_regex_raises_value_error():
    with pytest.raises(ValueError):
        file_re.compile(r"(")


def test_compile_with_flags_applies_them():
    simple_file = Path(ROOT, "resources", "simple_file.txt")
    pattern = file_re.compile(r"somemixedcaseline", flags=re.IGNORECASE)

    match = pattern.search(simple_file)
    assert match is not None
    assert match.group(0) == "someMixedCaseLINE"


def test_pattern_max_span_lines_must_be_positive():
    simple_file = Path(ROOT, "resources", "simple_file.txt")
    pattern = file_re.compile(r"foo")
    with pytest.raises(ValueError):
        pattern.search(simple_file, max_span_lines=0)
    with pytest.raises(ValueError):
        pattern.findall(simple_file, max_span_lines=-1)


def test_compile_locale_flag_raises():
    with pytest.raises(ValueError):
        file_re.compile(r"foo", flags=re.LOCALE)
