import re
from pathlib import Path

import pytest

from file_re import file_re

ROOT = Path(__file__).parent

file_types = [
    "simple_file.txt",
    "simple_file.txt.gz",
    "simple_file.txt.xz",
]


@pytest.mark.parametrize("file_name", file_types)
def test_ignorecase_flag(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(r"somemixedcaseline", simple_file)
    assert match is None

    match = file_re.search(r"somemixedcaseline", simple_file, flags=re.IGNORECASE)
    assert match is not None
    assert match.group(0) == "someMixedCaseLINE"


@pytest.mark.parametrize("file_name", file_types)
def test_dotall_flag_allows_dot_to_match_newline(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match_no_dotall = file_re.search(r'"name": "John Doe",.+"age": 30', simple_file)
    assert match_no_dotall is None

    match = file_re.search(
        r'"name": "John Doe",.+"age": 30', simple_file, flags=re.DOTALL
    )
    assert match is not None
    assert "John Doe" in match.group(0)
    assert "30" in match.group(0)


@pytest.mark.parametrize("file_name", file_types)
def test_multiline_flag_anchors_line_boundaries(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(r"^lowercaseonly$", simple_file, flags=re.MULTILINE)
    assert match is not None
    assert match.group(0) == "lowercaseonly"

    matches = file_re.findall(r"^user\d@example\.com", simple_file, flags=re.MULTILINE)
    assert len(matches) == 4


@pytest.mark.parametrize("file_name", file_types)
def test_verbose_flag_ignores_whitespace_and_comments(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    pattern = r"""
        (\d{3})   # area code
        -
        (\d{3})   # prefix
        -
        (\d{4})   # line number
    """
    match = file_re.search(pattern, simple_file, flags=re.VERBOSE)
    assert match is not None
    assert match.group(0) == "123-456-7890"
    assert match.group(1, 2, 3) == ("123", "456", "7890")


@pytest.mark.parametrize("file_name", file_types)
def test_combined_flags(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(
        r'"NAME": "JOHN DOE",.+"AGE": 30',
        simple_file,
        flags=re.IGNORECASE | re.DOTALL,
    )
    assert match is not None
    assert "John Doe" in match.group(0)


def test_locale_flag_raises_value_error():
    simple_file = Path(ROOT, "resources", "simple_file.txt")
    with pytest.raises(ValueError):
        file_re.search(r"foo", simple_file, flags=re.LOCALE)


def test_ascii_flag_warns():
    simple_file = Path(ROOT, "resources", "simple_file.txt")
    with pytest.warns(UserWarning):
        file_re.search(r"foo", simple_file, flags=re.ASCII)


def test_debug_flag_warns():
    simple_file = Path(ROOT, "resources", "simple_file.txt")
    with pytest.warns(UserWarning):
        file_re.search(r"foo", simple_file, flags=re.DEBUG)


def test_crlf_streaming_end_anchor():
    crlf_file = Path(ROOT, "resources", "crlf_sample.txt")

    match = file_re.search(
        r"foo$", crlf_file, flags=re.MULTILINE, max_span_lines=1
    )
    assert match is not None
    assert match.group(0) == "foo"

    matches = file_re.findall(
        r"foo$", crlf_file, flags=re.MULTILINE, max_span_lines=1
    )
    assert matches == ["foo", "foo"]

    matches = file_re.findall(
        r"foo$", crlf_file, flags=re.MULTILINE, max_span_lines=2
    )
    assert matches == ["foo", "foo"]
