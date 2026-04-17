import json
import re
import sys
from pathlib import Path

import pytest

from file_re import file_re
from utils import read_file

ROOT = Path(__file__).parent

file_types = [
    "simple_file.txt",
    "simple_file.txt.gz",
    "simple_file.txt.xz",
]


@pytest.mark.parametrize("file_name", file_types)
def test_search_groups_number(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    match = file_re.search(r"(\d{3})-(\d{3})-(\d{4})", simple_file)
    assert match
    assert match.group(0) == "123-456-7890"
    assert match.group(1) == "123"
    assert match.group(2) == "456"
    assert match.group(3) == "7890"
    assert match.group(0, 1, 2) == ("123-456-7890", "123", "456")


@pytest.mark.parametrize("file_name", file_types)
def test_search_name_groups_and_number(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    match = file_re.search(r"(?P<username>[\w\.-]+)@(?P<domain>[\w]+)\.\w+", simple_file)
    assert match
    assert match.group(0) == "user1@example.com"
    assert match.groupdict() == {"username": "user1", "domain": "example"}
    assert match.groups() == ("user1", "example")
    assert match.group("username") == "user1"
    assert match.group("domain") == "example"
    assert match.group(1, "domain") == ("user1", "example")
    assert match.group(1, 2) == ("user1", "example")


@pytest.mark.parametrize("file_name", file_types)
def test_greedy_match(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(r"<.*>", simple_file)
    assert match
    assert match.group(0) == "<div>Some content</div><div>Another content</div>"

    match = file_re.search(r"<.*?>", simple_file)
    assert match
    assert match.group(0) == "<div>"


@pytest.mark.parametrize("file_name", file_types)
def test_no_match(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    match = file_re.search(r"nonexistentpattern", simple_file)
    assert match is None


@pytest.mark.parametrize("file_name", file_types)
def test_case_sensitive_match(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(r"somemixedcaseline", simple_file)
    assert match is None

    match = file_re.search(r"(?i)somemixedcaseline", simple_file)
    assert match
    assert match.group(0) == "someMixedCaseLINE"


@pytest.mark.parametrize("file_name", file_types)
def test_search_default_spans_lines(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    json_match = file_re.search(r"\{[^{]+\{[^}]+\}\r?\n\}", simple_file)
    assert json_match
    json_dict = json.loads(json_match.group(0))
    assert json_dict["address"]["street"] == "123 Elm Street"


@pytest.mark.parametrize("file_name", file_types)
def test_search_single_line_does_not_cross_newline(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    json_match = file_re.search(
        r"\{[^{]+\{[^}]+\}\r?\n\}", simple_file, max_span_lines=1
    )
    assert json_match is None


@pytest.mark.parametrize("file_name", file_types)
def test_search_default_mode_functionality(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(r"(\d{3})-(\d{3})-(\d{4})", simple_file)
    assert match
    assert match.group(0, 1, 2, 3) == ("123-456-7890", "123", "456", "7890")

    match = file_re.search(
        r"(?P<username>[\w\.-]+)@(?P<domain>[\w]+)\.\w+", simple_file
    )
    assert match
    assert match.group(0, "username", "domain") == (
        "user1@example.com",
        "user1",
        "example",
    )

    match = file_re.search(r"<.*>", simple_file)
    assert match
    assert match.group(0) == "<div>Some content</div><div>Another content</div>"

    match = file_re.search(r"<.*?>", simple_file)
    assert match
    assert match.group(0) == "<div>"

    match = file_re.search(r"somemixedcaseline", simple_file)
    assert match is None

    match = file_re.search(r"(?i)somemixedcaseline", simple_file)
    assert match
    assert match.group(0) == "someMixedCaseLINE"


@pytest.mark.parametrize("file_name", file_types)
def test_check_span(file_name):
    if sys.platform.startswith("win") and file_name == "simple_file.txt":
        pytest.skip("Skipping test_check_span for simple_file.txt on Windows platform")

    simple_file = Path(ROOT, "resources", file_name)

    match_file_re = file_re.search(
        r"Regex can be complex, but it is very powerful",
        simple_file,
        max_span_lines=1,
    )
    assert match_file_re is not None
    file_str = read_file(simple_file)
    match = re.search(
        r"Regex can be complex, but it is very powerful",
        file_str,
    )
    assert match_file_re.span() == match.span()

    match_file_re = file_re.search(r"\{[^{]+\{[^}]+\}\r?\n\}", simple_file)
    assert match_file_re is not None
    file_str = read_file(simple_file)
    match = re.search(r"\{[^{]+\{[^}]+\}\r?\n\}", file_str)
    assert match_file_re.span() == match.span()


@pytest.mark.parametrize("file_name", file_types)
def test_search_max_span_lines_must_be_positive(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    with pytest.raises(ValueError):
        file_re.search(r"foo", simple_file, max_span_lines=0)
    with pytest.raises(ValueError):
        file_re.search(r"foo", simple_file, max_span_lines=-1)


def test_search_utf8_offsets():
    utf8_file = Path(ROOT, "resources", "utf8_sample.txt")

    match_file_re = file_re.search(r"café", utf8_file)
    file_str = read_file(utf8_file)
    match_re = re.search(r"café", file_str)

    assert match_file_re is not None
    assert match_re is not None
    assert match_file_re.group(0) == match_re.group(0)
    assert match_file_re.span() == match_re.span()
