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
def test_finditer_yields_match_objects(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    it = file_re.finditer(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", simple_file
    )

    first = next(it)
    assert isinstance(first, Match)
    assert first.group(0) == "user1@example.com"


@pytest.mark.parametrize("file_name", file_types)
def test_finditer_is_lazy_and_exhaustible(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    it = file_re.finditer(
        r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", simple_file
    )

    collected = []
    for m in it:
        collected.append(m.group(0))

    assert collected == [f"user{i}@example.com" for i in range(1, 5)]

    with pytest.raises(StopIteration):
        next(it)


@pytest.mark.parametrize("file_name", file_types)
@pytest.mark.parametrize("max_span_lines", [None, 1, 3])
def test_finditer_works_under_all_modes(file_name, max_span_lines):
    simple_file = Path(ROOT, "resources", file_name)

    matches = list(
        file_re.finditer(
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            simple_file,
            max_span_lines=max_span_lines,
        )
    )

    assert len(matches) == 4
    assert {m.group(0) for m in matches} == {
        f"user{i}@example.com" for i in range(1, 5)
    }


@pytest.mark.parametrize("file_name", file_types)
def test_finditer_matches_findall_shape(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    pattern = r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"

    findall_results = file_re.findall(pattern, simple_file)
    finditer_results = [m.group(0) for m in file_re.finditer(pattern, simple_file)]

    assert findall_results == finditer_results


@pytest.mark.parametrize("file_name", file_types)
def test_finditer_independent_instances(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    it1 = file_re.finditer(r"\d{3}-\d{3}-\d{4}", simple_file)
    it2 = file_re.finditer(r"\d{3}-\d{3}-\d{4}", simple_file)

    first_from_each = (next(it1).group(0), next(it2).group(0))
    assert first_from_each == ("123-456-7890", "123-456-7890")


@pytest.mark.parametrize("file_name", file_types)
def test_finditer_window_mode_matches(file_name):
    simple_file = Path(ROOT, "resources", file_name)

    matches = list(
        file_re.finditer(
            r"\{[^{]+\{[^}]+\}\r?\n\}", simple_file, max_span_lines=20
        )
    )
    assert len(matches) == 2


def test_finditer_max_span_lines_must_be_positive():
    simple_file = Path(ROOT, "resources", "simple_file.txt")
    with pytest.raises(ValueError):
        file_re.finditer(r"foo", simple_file, max_span_lines=0)


def test_windowed_finditer_no_overlapping_matches():
    """
    Regression test: windowed finditer/findall must not return matches that
    overlap each other (must match `re.findall` non-overlap semantics).
    See task #8 / commit fixing overlap in the sliding-window engine.
    """
    resource = Path(ROOT, "resources", "simple_file.txt")
    pattern = r'\{[^{]+\{[^}]+\}\r?\n\}'

    results = list(file_re.finditer(pattern, resource, max_span_lines=20))
    assert len(results) == 2

    for a, b in zip(results, results[1:]):
        assert b.start() >= a.end(), (
            f"overlap: {a.span()} then {b.span()}"
        )

    import re as stdlib_re
    content = resource.read_text(encoding="utf-8")
    re_results = stdlib_re.findall(pattern, content)
    assert len(re_results) == len(results)
