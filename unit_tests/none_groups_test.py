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
def test_non_participating_group_is_none_in_groups(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(r"(Welcome)|(bar)", simple_file)
    assert match is not None
    assert match.group(0) == "Welcome"
    assert match.groups() == ("Welcome", None)


@pytest.mark.parametrize("file_name", file_types)
def test_non_participating_named_group_is_none_in_groupdict(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(
        r"(?P<hit>Welcome)|(?P<miss>bar)", simple_file
    )
    assert match is not None
    assert match.groupdict() == {"hit": "Welcome", "miss": None}


@pytest.mark.parametrize("file_name", file_types)
def test_none_group_access_by_index(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(r"(Welcome)|(bar)", simple_file)
    assert match is not None
    assert match.group(1) == "Welcome"
    assert match.group(2) is None


@pytest.mark.parametrize("file_name", file_types)
def test_none_group_access_by_name(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    match = file_re.search(
        r"(?P<hit>Welcome)|(?P<miss>bar)", simple_file
    )
    assert match is not None
    assert match.group("hit") == "Welcome"
    assert match.group("miss") is None


@pytest.mark.parametrize("file_name", file_types)
def test_findall_none_groups(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    results = file_re.findall(r"(Welcome)|(This library)", simple_file)
    assert ("Welcome", None) in results
    assert (None, "This library") in results


@pytest.mark.parametrize("file_name", file_types)
def test_finditer_none_groups(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    matches = list(file_re.finditer(r"(Welcome)|(This library)", simple_file))
    groups = [m.groups() for m in matches]

    assert ("Welcome", None) in groups
    assert (None, "This library") in groups
