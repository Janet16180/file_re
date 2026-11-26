"""
Run CPython's own regex test table through ``file_re``.

Each ``(pattern, string)`` pair from ``Lib/test/re_tests.py`` is written to a
file and scanned in whole-file mode; the result must equal what :mod:`re`
produces for the same string. Patterns the Rust engine does not support
(backreferences, lookarounds, ...) are skipped, and the test asserts that
the supported share does not silently shrink.
"""

import ast
import re
import warnings
from pathlib import Path

import oracle
from file_re import file_re

TABLE = Path(__file__).parent / "resources" / "cpython_re_tests.py"


def load_table():
    """Yield ``(pattern, string)`` for every entry CPython expects to compile."""
    tree = ast.parse(TABLE.read_text(encoding="utf-8"))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if getattr(node.targets[0], "id", None) != "tests":
            continue
        for item in node.value.elts:
            if not isinstance(item, ast.Tuple) or len(item.elts) < 3:
                continue
            outcome = item.elts[2]
            if not isinstance(outcome, ast.Name) or outcome.id == "SYNTAX_ERROR":
                continue
            try:
                yield ast.literal_eval(item.elts[0]), ast.literal_eval(item.elts[1])
            except ValueError:
                # A handful of entries build their string with an expression.
                continue


def _snapshot(m):
    return (m.span(), m.group(0), m.groups())


def test_cpython_re_table(tmp_path):
    path = tmp_path / "input.txt"
    compared = 0
    unsupported = 0
    failures = []

    for pattern, text in load_table():
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                expected_re = re.compile(pattern)
            except re.error:
                continue
            try:
                compiled = file_re.compile(pattern)
            except ValueError:
                unsupported += 1
                continue

        path.write_bytes(text.encode("utf-8"))
        expected = [_snapshot(m) for m in oracle.finditer(expected_re, text)]
        got = [_snapshot(m) for m in compiled.finditer(path)]
        compared += 1
        if got != expected:
            failures.append((pattern, text, expected, got))

    assert not failures, failures[:5]
    # Guard against the table or the engine changing under us: when this was
    # written, 314 entries were supported and 45 were not.
    assert compared >= 300
    assert unsupported <= 60
