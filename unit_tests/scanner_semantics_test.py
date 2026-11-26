"""
Targeted tests for the chunked scanner: the behaviours that changed in 3.0
and the edge cases a block-based reader has to get right.
"""

import gzip
import re
import time

import pytest

from file_re import file_re
from file_re._file_re import _set_block_size


@pytest.fixture(params=[1, 5, 256 * 1024], ids=lambda b: f"block{b}")
def block_size(request):
    previous = _set_block_size(request.param)
    yield request.param
    _set_block_size(previous)


def spans(pattern, path, flags=0, n=None):
    return [
        (m.span(), m.group())
        for m in file_re.finditer(pattern, path, flags, max_span_lines=n)
    ]


def test_window_does_not_truncate_greedy_match(tmp_path, block_size):
    path = tmp_path / "f.txt"
    path.write_text("BEGIN\nx\ny\nEND\nother\n")
    assert spans(r"BEGIN(?:\n.*){0,3}", path, n=5) == [((0, 13), "BEGIN\nx\ny\nEND")]
    assert spans(r"BEGIN\n(?:x\n)?(?:y\n)?", path, n=5) == [((0, 10), "BEGIN\nx\ny\n")]


def test_window_limits_match_to_n_lines(tmp_path, block_size):
    path = tmp_path / "f.txt"
    path.write_text("BEGIN\nx\ny\nEND\nother\n")
    # Greedy, but only two lines are visible from the line where it starts.
    assert spans(r"BEGIN(?:\n.*){0,3}", path, n=2) == [((0, 7), "BEGIN\nx")]
    # The match needs four lines, so a three-line window never sees it.
    assert spans(r"BEGIN\nx\ny\nEND", path, n=3) == []
    assert spans(r"BEGIN\nx\ny\nEND", path, n=4) == [((0, 13), "BEGIN\nx\ny\nEND")]


@pytest.mark.parametrize("n", [1, 2, 5])
def test_start_anchors_mean_start_of_file(tmp_path, block_size, n):
    path = tmp_path / "f.txt"
    path.write_text("foo 1\nbar\nfoo 2\nfoo 3\n")
    assert spans(r"^foo \d", path, n=n) == [((0, 5), "foo 1")]
    assert spans(r"\Afoo \d", path, n=n) == [((0, 5), "foo 1")]
    assert spans(r"^foo \d", path, re.MULTILINE, n=n) == [
        ((0, 5), "foo 1"),
        ((10, 15), "foo 2"),
        ((16, 21), "foo 3"),
    ]


@pytest.mark.parametrize("n", [None, 1, 3])
def test_end_anchor_means_end_of_file(tmp_path, block_size, n):
    path = tmp_path / "f.txt"
    path.write_text("a1\nb2\nc3")
    assert spans(r"\d$", path, n=n) == [((7, 8), "3")]
    assert spans(r"\d$", path, re.MULTILINE, n=n) == [
        ((1, 2), "1"),
        ((4, 5), "2"),
        ((7, 8), "3"),
    ]


@pytest.mark.parametrize("n", [None, 1, 2])
def test_empty_matches_are_not_duplicated(tmp_path, block_size, n):
    path = tmp_path / "f.txt"
    path.write_text("ab\ncd\n")
    assert [s for s, _ in spans(r"z*", path, n=n)] == [(i, i) for i in range(7)]


@pytest.mark.parametrize("n", [None, 1, 2])
def test_crlf_offsets_are_the_same_in_every_mode(tmp_path, block_size, n):
    path = tmp_path / "f.txt"
    path.write_bytes(b"ab\r\ncd\r\nef\r\n")
    # Same offsets as re on open(path).read(), which also reads \r\n as \n.
    text = path.read_text()
    expected = [(m.span(), m.group()) for m in re.finditer(r"cd|ef", text)]
    assert spans(r"cd|ef", path, n=n) == expected == [((3, 5), "cd"), ((6, 8), "ef")]
    assert spans(r"\r", path, n=n) == []


def test_offsets_count_characters_not_bytes(tmp_path, block_size):
    path = tmp_path / "f.txt"
    text = "café \U0001f600 x\n" * 50 + "needle\n"
    path.write_text(text, encoding="utf-8")
    expected = text.index("needle")
    for n in (None, 1, 3):
        m = file_re.search(r"needle", path, max_span_lines=n)
        assert m.span() == (expected, expected + 6)


def test_match_is_anchored_at_start_of_file(tmp_path, block_size):
    path = tmp_path / "f.txt"
    path.write_text("head\nbody\n")
    for n in (None, 1, 2):
        assert file_re.match(r"head", path, max_span_lines=n).span() == (0, 4)
        assert file_re.match(r"body", path, max_span_lines=n) is None
    assert file_re.match(r"head\nbody", path, max_span_lines=1) is None
    assert file_re.match(r"head\nbody", path, max_span_lines=2).span() == (0, 9)


def test_line_longer_than_block(tmp_path):
    previous = _set_block_size(16)
    try:
        path = tmp_path / "f.txt"
        path.write_text("x" * 1000 + "needle" + "y" * 1000 + "\nlast needle\n")
        assert [s for s, _ in spans(r"needle", path, n=1)] == [(1000, 1006), (2012, 2018)]
    finally:
        _set_block_size(previous)


def test_many_too_long_candidates(tmp_path, block_size):
    # Every unrestricted match spans the rest of the file, which pushes the
    # scanner onto its window-by-window path.
    path = tmp_path / "f.txt"
    path.write_text("ab\n" * 300)
    assert file_re.findall(r"[^x]+", path, max_span_lines=1) == ["ab"] * 300
    assert file_re.findall(r"a[^x]+", path, max_span_lines=2) == ["ab\nab"] * 150


def test_concatenated_gzip_members(tmp_path):
    path = tmp_path / "f.log.gz"
    with open(path, "wb") as f:
        f.write(gzip.compress(b"first ERROR\n"))
        f.write(gzip.compress(b"second ERROR\n"))
    assert len(file_re.findall(r"ERROR", path)) == 2
    assert len(file_re.findall(r"ERROR", path, max_span_lines=1)) == 2


@pytest.mark.parametrize("n", [None, 1, 4])
def test_invalid_utf8_raises_oserror(tmp_path, n):
    path = tmp_path / "f.txt"
    path.write_bytes(b"ok\nbad \xff byte\n")
    with pytest.raises(OSError):
        file_re.findall(r"byte", path, max_span_lines=n)


def test_finditer_whole_file_is_linear(tmp_path):
    # 2.x recounted characters from the start of the file for every match,
    # which made this take minutes.
    path = tmp_path / "f.txt"
    path.write_text("some padding text ERROR more padding\n" * 200_000)
    started = time.perf_counter()
    count = sum(1 for _ in file_re.finditer(r"ERROR", path))
    assert count == 200_000
    assert time.perf_counter() - started < 10
