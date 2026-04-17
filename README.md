# file_re

[![Documentation Status](https://readthedocs.org/projects/file-re/badge/?version=latest)](https://file-re.readthedocs.io/en/latest/)
[![PyPI version](https://img.shields.io/pypi/v/file_re.svg)](https://pypi.org/project/file_re/)

`file_re` is a Rust-backed Python library for running regular expressions
over large files. It mirrors the public surface of Python's `re` module
and adds a single `max_span_lines` parameter that controls how much of
the file is held in memory — the same API scales from small
configuration files to 50 GB compressed logs.

- **Docs:** <https://file-re.readthedocs.io>
- **PyPI:** <https://pypi.org/project/file_re/>
- **Source:** this repository

## Features

- `search`, `match`, `findall`, `finditer`, and `compile` with the
  same shape as `re`.
- A `max_span_lines` knob: `None` for full-file scans, `1` for
  line-by-line streaming, and `N` for a sliding N-line window.
- Transparent `.gz` and `.xz` decompression — no special call needed.
- Proper `re.Match` semantics, including `None` for non-participating
  groups.
- GIL released during IO and regex work, so `file_re` plays well with
  `multiprocessing` and threaded pipelines.

## Installation

```bash
pip install file_re
```

Wheels are published for CPython 3.9 through 3.13 on Linux
(`manylinux`/`musllinux`), macOS (x86_64 and arm64), and Windows.

## Quickstart

```python
from pathlib import Path
from file_re import file_re

log = Path("server.log")

# Single search, whole file in memory (re-equivalent default).
match = file_re.search(r"ERROR: (?P<msg>.+)", log)
if match:
    print(match.group("msg"))

# All phone numbers in a contacts file.
phones = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", "contacts.txt")

# Lazy iteration — preferred for large files.
for match in file_re.finditer(r"\bERROR\b", log):
    print(match.span(), match.group())
```

### Compressed files

```python
from file_re import file_re

# .gz and .xz are decoded transparently.
matches = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", "logs/2026-04.log.gz")
```

### Flags

```python
import re
from file_re import file_re

match = file_re.search(
    r"^error:.*$",
    "server.log",
    flags=re.IGNORECASE | re.MULTILINE,
)
```

`re.ASCII`, `re.DEBUG`, and `re.LOCALE` have Rust-specific semantics;
see the [flags guide](https://file-re.readthedocs.io/en/latest/guides/flags.html).

### Compiled patterns

```python
import re
from file_re import file_re

pattern = file_re.compile(r"error: (\w+)", flags=re.IGNORECASE)

for log in ("a.log", "b.log", "c.log"):
    for match in pattern.finditer(log):
        handle(match)
```

## Large files and `max_span_lines`

`max_span_lines` is the memory-usage dial. The rest of the API is the
same regardless of mode.

```python
from file_re import file_re

# Stream line by line. A match cannot cross a newline. Cheapest mode.
for match in file_re.finditer(r"\bERROR\b", "huge.log", max_span_lines=1):
    handle(match)

# Slide a 5-line window. A match may span at most 5 lines.
pattern = r"BEGIN TXN\n(?:.*\n){0,3}END TXN"
for match in file_re.finditer(pattern, "huge.log", max_span_lines=5):
    handle(match)
```

For 50 GB logs, the recommended pattern is a process pool — each worker
holds a bounded window, so total resident memory stays flat:

```python
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from file_re import file_re

PATTERN = r"BEGIN TXN\n(?:.*\n){0,3}END TXN"

def count_matches(shard: Path) -> int:
    return sum(1 for _ in file_re.finditer(PATTERN, shard, max_span_lines=5))

if __name__ == "__main__":
    shards = sorted(Path("/var/log/app").glob("*.log.gz"))
    with ProcessPoolExecutor(max_workers=16) as pool:
        print(sum(pool.map(count_matches, shards)))
```

See the [large files guide](https://file-re.readthedocs.io/en/latest/guides/large_files.html)
for details.

## Migrating from 1.x

2.0 is a breaking release: `multiline=` and `num_lines=` are replaced by
`max_span_lines`, `Match.groups` now reports `None` (not `""`) for
non-participating groups, and `search()` in window mode returns the
first match. The full migration guide is at
<https://file-re.readthedocs.io/en/latest/guides/migration_1_to_2.html>.

## Development

```bash
git clone https://github.com/Janet16180/file_re.git
cd file_re/file_re
pip install -r requirements.txt
maturin develop --release
pytest unit_tests/
```

To build the documentation locally:

```bash
pip install -r docs/requirements.txt
cd docs && make html
```

## License

See [LICENSE](LICENSE).
