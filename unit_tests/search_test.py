import pytest
from pathlib import Path
from file_re import file_re

ROOT = Path(__file__).parent

file_types = [
    ("simple_file.txt"),
    ("simple_file.txt.gz"),
    ("simple_file.txt.xz"),
]

@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_search_groups_number(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    match = file_re.search(r"(\d{3})-(\d{3})-(\d{4})", simple_file)
    assert match
    assert match.group(0) == "123-456-7890"
    assert match.group(1) == "123"
    assert match.group(2) == "456"
    assert match.group(3) == "7890"
    assert match.group(0, 1, 2) == ("123-456-7890", "123", "456")

@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_search_name_groups_and_number(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    match = file_re.search(r"(?P<username>[\w\.-]+)@(?P<domain>[\w]+)\.\w+", simple_file)
    assert match
    assert match.group(0) == "user@example.com"
    assert match.groupdict() == {"username": "user", "domain": "example"}
    assert match.groups() == ("user", "example")
    assert match.group("username") == "user"
    assert match.group("domain") == "example"
    assert match.group(1, "domain") == ("user", "example")
    assert match.group(1, 2) == ("user", "example")

@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_greedy_match(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    # Try non-greedy match
    match = file_re.search(r"<.*>", simple_file)
    assert match
    assert match.group(0) == "<div>Some content</div><div>Another content</div>"

    # Try greey match
    match = file_re.search(r"<.*?>", simple_file)
    assert match
    assert match.group(0) == "<div>"


@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_no_match(file_name):
    simple_file = Path(ROOT, "resources", file_name)
    match = file_re.search(r"nonexistentpattern", simple_file)
    assert match is None


@pytest.mark.parametrize(
    "file_name",
    file_types
)
def test_case_sensitive_match(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    # Case-sensitive pattern
    match = file_re.search(r"somemixedcaseline", simple_file)
    assert match is None

    # Case-insensitive pattern
    match = file_re.search(r"(?i)somemixedcaseline", simple_file)
    assert match
    assert match.group(0) == "someMixedCaseLINE"

