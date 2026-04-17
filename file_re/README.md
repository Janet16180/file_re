# file_re

`file_re` is a Rust-backed Python library for running regular expressions
over large files. It mirrors the public surface of Python's `re` module
and adds a single `max_span_lines` parameter that controls how much of
the file is held in memory — the same API scales from small configuration
files to 50 GB compressed logs.

- **Documentation:** <https://file-re.readthedocs.io>
- **Source:** <https://github.com/Janet16180/file_re>

## Install

```bash
pip install file_re
```

Wheels are published for CPython 3.9 through 3.13 on Linux, macOS, and
Windows.

## At a glance

```python
from file_re import file_re

# Same shape as Python's re module.
match = file_re.search(r"ERROR: (?P<msg>.+)", "server.log")
if match:
    print(match.group("msg"))

# Transparent .gz and .xz support.
phones = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", "contacts.txt.gz")

# Lazy iteration with bounded memory.
for m in file_re.finditer(r"\bERROR\b", "huge.log", max_span_lines=1):
    print(m.span(), m.group())
```

### `max_span_lines` in one line

- `None` (default) — load the whole file, full `re`-equivalent semantics.
- `1` — stream line by line; a match cannot cross a newline.
- `N > 1` — sliding N-line window; a match may span at most N lines.

### Supported API

- `file_re.search`, `file_re.match`, `file_re.findall`, `file_re.finditer`
- `file_re.compile(pattern, flags=0)` returning a reusable `Pattern`
- `flags` keyword accepting `re.IGNORECASE`, `re.MULTILINE`, `re.DOTALL`,
  `re.VERBOSE`, `re.UNICODE`, and `re.ASCII` (with Rust-specific
  divergence notes in the docs)

See the full [documentation](https://file-re.readthedocs.io) for the
large-file guide, flag parity details, and the 1.x to 2.0 migration
guide.

## License

MIT. See the repository for the full text.
