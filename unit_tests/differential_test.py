"""
Differential tests: ``file_re`` in every mode and at several read-block
sizes must agree with the reference implementation in ``oracle.py``.

Small block sizes force the scanner to refill in the middle of lines,
matches and multi-byte characters, which is where a chunked reader can go
wrong.
"""

import random
import re

import pytest

import oracle
from file_re import file_re
from file_re._file_re import _set_block_size

MODES = [None, 1, 2, 3, 5]
BLOCK_SIZES = [1, 3, 7, 64, 256 * 1024]

TEXTS = {
    "empty": b"",
    "one_line_no_newline": b"alpha beta gamma",
    "only_newlines": b"\n\n\n",
    "log": (
        b"INFO start\nERROR: disk failed code=12\nINFO ok\n"
        b"BEGIN TXN id=1\n  step one\n  step two\nEND TXN\n"
        b"ERROR: net failed code=7\nBEGIN TXN id=2\nEND TXN\nINFO done\n"
    ),
    "no_trailing_newline": b"foo 1\nbar\nfoo 2\nfoo 3",
    "blank_lines": b"a\n\nb\n\n\nc\n",
    "utf8": "café naïve\n日本語 text\n\U0001f600 end café\n".encode(),
    "crlf": b"first foo\r\nsecond bar\r\nthird foo\r\n\r\nlast",
    "lone_cr": b"a\rb\nc\r\n",
    "long_line": b"x" * 500 + b" needle " + b"y" * 500 + b"\nshort needle\n",
    "repeated": b"ab\n" * 200,
}

PATTERNS = [
    (r"ERROR: (\w+) failed code=(\d+)", 0),
    (r"BEGIN TXN id=(\d+)\n(?:.*\n){0,3}END TXN", 0),
    (r"BEGIN(?:\n.*){0,3}", 0),
    (r"BEGIN.*END TXN", re.DOTALL),
    (r"(?P<key>\w+)=(?P<value>\d+)", 0),
    (r"foo|bar", 0),
    (r"^foo \d", 0),
    (r"^foo \d", re.MULTILINE),
    (r"\Afoo", 0),
    (r"\d$", re.MULTILINE),
    (r"^$", re.MULTILINE),
    (r"^", re.MULTILINE),
    (r"$", re.MULTILINE),
    (r"z*", 0),
    (r"a*", 0),
    (r"\b", 0),
    (r"\s+", 0),
    (r"[^x]+", 0),
    (r"\n", 0),
    (r"\n\n", 0),
    (r".+", 0),
    (r".+", re.DOTALL),
    (r"(a)|(b)", 0),
    (r"(?:ab\n)+", 0),
    (r"(?:ab\n){3}", 0),
    (r"café", 0),
    (r"\w+", 0),
    (r"[éï]", 0),
    (r"needle", 0),
    (r"x+ needle y+", 0),
    (r"FOO|Error", re.IGNORECASE),
    (r"(\w+)\s*\n\s*(\w+)", 0),
    (r"foo$", re.MULTILINE),
    (r"\r", 0),
]


def _snapshot(m):
    return None if m is None else (m.span(), m.group(0), m.groups(), m.groupdict())


def check(path, text, pattern, flags, n):
    """Compare every entry point against the oracle for one configuration."""
    compiled = re.compile(pattern, flags)
    expected = [_snapshot(m) for m in oracle.finditer(compiled, text, n)]

    got = [_snapshot(m) for m in file_re.finditer(pattern, path, flags, max_span_lines=n)]
    assert got == expected

    assert _snapshot(
        file_re.search(pattern, path, flags, max_span_lines=n)
    ) == (expected[0] if expected else None)

    assert _snapshot(
        file_re.match(pattern, path, flags, max_span_lines=n)
    ) == _snapshot(oracle.match(compiled, text, n))

    assert file_re.findall(pattern, path, flags, max_span_lines=n) == oracle.findall(
        compiled, text, n
    )


@pytest.fixture(params=BLOCK_SIZES, ids=lambda b: f"block{b}")
def block_size(request):
    previous = _set_block_size(request.param)
    yield request.param
    _set_block_size(previous)


@pytest.mark.parametrize("text_name", sorted(TEXTS))
def test_corpus_matches_oracle(tmp_path, block_size, text_name):
    raw = TEXTS[text_name]
    path = tmp_path / "input.txt"
    path.write_bytes(raw)
    text = oracle.normalize(raw)
    for pattern, flags in PATTERNS:
        for n in MODES:
            try:
                check(path, text, pattern, flags, n)
            except AssertionError as exc:
                raise AssertionError(
                    f"pattern={pattern!r} flags={flags} max_span_lines={n} "
                    f"block={block_size} text={text_name}\n{exc}"
                ) from None


# ---------------------------------------------------------------------------
# Seeded random patterns and texts.
# ---------------------------------------------------------------------------

_ATOMS = ["a", "b", "c", "é", " ", ".", r"\n", r"\s", r"\w", r"\d", "[ab]", "[^a]", "1"]
_ASSERTIONS = [r"\b", "^", r"\A"]
_QUANTIFIERS = ["", "", "", "*", "+", "?", "*?", "+?", "{1,2}", "{2}"]


def _random_piece(rng, depth):
    roll = rng.random()
    if depth < 2 and roll < 0.15:
        inner = _random_sequence(rng, depth + 1)
        return f"({inner}){rng.choice(['', '', '+', '?'])}"
    if depth < 2 and roll < 0.30:
        left = _random_sequence(rng, depth + 1)
        right = _random_sequence(rng, depth + 1)
        return f"(?:{left}|{right}){rng.choice(['', '', '+', '?', '*'])}"
    if roll < 0.38:
        return rng.choice(_ASSERTIONS)
    return rng.choice(_ATOMS) + rng.choice(_QUANTIFIERS)


def _random_sequence(rng, depth=0):
    # At least one consuming atom, so groups are never empty-only: Python
    # and Rust disagree on what a repeated empty group captures.
    pieces = [rng.choice(["a", "b", "c", r"\w", r"\d"])]
    pieces += [_random_piece(rng, depth) for _ in range(rng.randint(0, 3))]
    rng.shuffle(pieces)
    return "".join(pieces)


def _random_text(rng):
    alphabet = "aabbc 1é\n\n"
    body = "".join(rng.choice(alphabet) for _ in range(rng.randint(0, 80)))
    if rng.random() < 0.2:
        body = body.replace("\n", "\r\n")
    return body.encode("utf-8")


def _random_cases(seed, count):
    rng = random.Random(seed)
    cases = []
    while len(cases) < count:
        pattern = _random_sequence(rng)
        flags = rng.choice([0, 0, re.MULTILINE, re.DOTALL, re.IGNORECASE])
        try:
            re.compile(pattern, flags)
            file_re.compile(pattern, flags)
        except (re.error, ValueError):
            continue
        cases.append((pattern, flags, _random_text(rng)))
    return cases


@pytest.mark.parametrize("seed", range(8))
def test_random_patterns_match_oracle(tmp_path, block_size, seed):
    path = tmp_path / "input.txt"
    for pattern, flags, raw in _random_cases(seed, 150):
        path.write_bytes(raw)
        text = oracle.normalize(raw)
        n = random.Random(hash((seed, pattern, len(raw)))).choice(MODES)
        try:
            check(path, text, pattern, flags, n)
        except AssertionError as exc:
            raise AssertionError(
                f"pattern={pattern!r} flags={flags} max_span_lines={n} "
                f"block={block_size} raw={raw!r}\n{exc}"
            ) from None
