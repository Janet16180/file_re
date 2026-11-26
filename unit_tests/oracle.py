"""
Reference implementation of file_re's matching rules, built on :mod:`re`.

``re`` is used as the single-match engine; this module only adds the
iteration and ``max_span_lines`` rules, written the slow obvious way, so
tests can compare ``file_re`` against it on arbitrary inputs.

Rules (see ``file_re/src/scanner.rs``):

* Matches are reported left to right and do not overlap. After an empty
  match the scan resumes one character later.
* With ``max_span_lines=n``, a match starting on line ``L`` must end
  before the line terminator of line ``L + n - 1``.
* ``\\r\\n`` is read as ``\\n``, like Python's text mode.
"""

import re
from typing import Iterator, List, Optional


def normalize(raw: bytes) -> str:
    return raw.decode("utf-8").replace("\r\n", "\n")


def _line_end(text: str, pos: int) -> int:
    end = text.find("\n", pos)
    return len(text) if end < 0 else end


def _window_limit(text: str, pos: int, n: int) -> int:
    limit = pos
    for _ in range(n):
        limit = text.find("\n", limit)
        if limit < 0:
            return len(text)
        limit += 1
    return limit - 1


def _next_match(
    pattern: "re.Pattern[str]", text: str, pos: int, n: Optional[int]
) -> Optional["re.Match[str]"]:
    if n is None:
        return pattern.search(text, pos)
    while pos <= len(text):
        line_end = _line_end(text, pos)
        m = pattern.search(text, pos, _window_limit(text, pos, n))
        if m and m.start() <= line_end:
            return m
        pos = line_end + 1
    return None


def finditer(
    pattern: "re.Pattern[str]", text: str, n: Optional[int] = None
) -> Iterator["re.Match[str]"]:
    pos = 0
    while pos <= len(text):
        m = _next_match(pattern, text, pos, n)
        if m is None:
            return
        yield m
        pos = m.end() if m.end() > m.start() else m.end() + 1


def search(pattern, text, n=None):
    return next(finditer(pattern, text, n), None)


def match(pattern, text, n=None):
    if n is None:
        return pattern.match(text)
    return pattern.match(text, 0, _window_limit(text, 0, n))


def findall(pattern, text, n=None) -> List:
    out = []
    for m in finditer(pattern, text, n):
        if pattern.groups == 0:
            out.append(m.group(0))
        else:
            out.append(m.groups())
    return out
