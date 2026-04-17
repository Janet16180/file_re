from pathlib import Path

import pytest

from file_re import Match, file_re

ROOT = Path(__file__).parent

file_types = [
    "simple_file.txt",
    "simple_file.txt.gz",
    "simple_file.txt.xz",
]


@pytest.mark.parametrize("file_name", file_types)
def test_match_returns_match_at_start_of_file(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    m = file_re.match(r"Welcome to the file_re library", simple_file)
    assert isinstance(m, Match)
    assert m.group(0) == "Welcome to the file_re library"
    assert m.start() == 0


@pytest.mark.parametrize("file_name", file_types)
def test_match_returns_none_when_not_at_start(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    m = file_re.match(r"This library", simple_file)
    assert m is None


@pytest.mark.parametrize("file_name", file_types)
def test_match_with_groups(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    m = file_re.match(r"(Welcome) to (the file_re library)", simple_file)
    assert m is not None
    assert m.group(1) == "Welcome"
    assert m.group(2) == "the file_re library"


@pytest.mark.parametrize("file_name", file_types)
@pytest.mark.parametrize("max_span_lines", [None, 1, 5])
def test_match_under_all_max_span_lines_modes(file_name, max_span_lines):
    simple_file = Path(ROOT, "resources", file_name)

    m = file_re.match(
        r"Welcome to the file_re library",
        simple_file,
        max_span_lines=max_span_lines,
    )
    assert m is not None
    assert m.group(0) == "Welcome to the file_re library"


def test_match_with_flags():
    simple_file = Path(ROOT, "resources", "simple_file.txt")

    import re

    m = file_re.match(r"WELCOME TO THE FILE_RE LIBRARY", simple_file, flags=re.IGNORECASE)
    assert m is not None
    assert m.group(0).lower() == "welcome to the file_re library"


def test_match_max_span_lines_must_be_positive():
    simple_file = Path(ROOT, "resources", "simple_file.txt")
    with pytest.raises(ValueError):
        file_re.match(r"Welcome", simple_file, max_span_lines=0)
