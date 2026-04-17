import json
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
def test_findall(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    emails = file_re.findall(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", simple_file
    )
    assert len(emails) == 4

    expected_emails = [f"user{i}@example.com" for i in range(1, 5)]
    assert set(emails) == set(expected_emails)


@pytest.mark.parametrize("file_name", file_types)
def test_groups(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    emails = file_re.findall(
        r"([a-zA-Z0-9_.+-]+)@([a-zA-Z0-9-]+)\.[a-zA-Z0-9-.]+", simple_file
    )
    assert len(emails) == 4
    assert len(emails[0]) == 2

    expected_emails = [(f"user{i}", "example") for i in range(1, 5)]
    assert set(emails) == set(expected_emails)


@pytest.mark.parametrize("file_name", file_types)
def test_findall_default_spans_lines(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    json_matches = file_re.findall(r"\{[^{]+\{[^}]+\}\r?\n\}", simple_file)

    assert len(json_matches) == 2

    json_1, json_2 = json_matches

    json_dict = json.loads(json_1)
    assert json_dict["address"]["street"] == "123 Elm Street"

    json_dict = json.loads(json_2)
    assert json_dict["address"]["street"] == "456 Maple Avenue"


@pytest.mark.parametrize("file_name", file_types)
def test_findall_single_line_does_not_cross_newline(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    json_matches = file_re.findall(
        r"\{[^{]+\{[^}]+\}\r?\n\}", simple_file, max_span_lines=1
    )
    assert len(json_matches) == 0


@pytest.mark.parametrize("file_name", file_types)
def test_findall_max_span_lines_must_be_positive(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    with pytest.raises(ValueError):
        file_re.findall(r"foo", simple_file, max_span_lines=0)


def test_windowed_findall_no_overlapping_matches():
    """
    Regression test: windowed findall must not return matches that overlap
    each other (must match `re.findall` non-overlap semantics).
    See task #8 / commit fixing overlap in the sliding-window engine.
    """
    resource = Path(ROOT, "resources", "simple_file.txt")
    pattern = r'\{[^{]+\{[^}]+\}\r?\n\}'

    results = file_re.findall(pattern, resource, max_span_lines=20)
    assert len(results) == 2

    import re as stdlib_re
    content = resource.read_text()
    re_results = stdlib_re.findall(pattern, content)
    assert len(re_results) == len(results)
