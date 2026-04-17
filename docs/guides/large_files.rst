Large files and ``max_span_lines``
==================================

``file_re`` is designed around a single dial for memory usage:
``max_span_lines``. The rest of the API is deliberately identical to
:mod:`re`, so the only choice you need to make is how wide a match can
reasonably span.

The three modes
---------------

``max_span_lines=None`` (default)
    The whole file is read into memory and scanned as one string. This is
    the full :mod:`re`-equivalent mode: a pattern can match anywhere,
    including across the entire file. Memory cost is proportional to the
    file size. Use this for files that comfortably fit in RAM.

``max_span_lines=1``
    The file is streamed line by line. A match cannot cross a ``\n``.
    Memory cost is O(longest line). This is the fastest path for big
    files when the pattern is single-line.

``max_span_lines=N`` (``N > 1``)
    The file is streamed through a sliding ``N``-line window. A match may
    span at most ``N`` lines. Memory cost is roughly O(N x average line
    length). This is the recommended path for multi-GB log files where
    individual events span a known, bounded number of lines.

Memory trade-offs
-----------------

Consider a 50 GB log where events are typically 3-5 lines long.

- ``None`` would require ~50 GB of RAM. Not viable.
- ``1`` is cheap but will miss any event whose record crosses a newline.
- ``5`` keeps memory flat at a few kilobytes and captures the multi-line
  events correctly.

The choice is entirely about the pattern, not the file:

.. code-block:: python

   from file_re import file_re

   # Single-line pattern: go as tight as possible.
   for m in file_re.finditer(r"\bERROR\b", "huge.log", max_span_lines=1):
       handle(m)

   # Multi-line event that is known to span at most 5 lines.
   pattern = r"BEGIN TXN\n(?:.*\n){0,3}END TXN"
   for m in file_re.finditer(pattern, "huge.log", max_span_lines=5):
       handle(m)

Behavior when a match would exceed the window
---------------------------------------------

In windowed mode, the scanner only sees ``N`` consecutive lines at a
time. A match that would genuinely span more than ``N`` lines is simply
never visible to the regex engine and will not be reported. If you
suspect events can span more lines than you expect, measure the worst
case before sizing the window.

Search returns the first match
------------------------------

In windowed mode, :meth:`~file_re.core.file_re_cls.search` returns the
first match the scanner encounters as the window slides forward. This
matches the semantics of :func:`re.search` against the full concatenated
text. If you need the longest match, iterate and pick it yourself:

.. code-block:: python

   from file_re import file_re

   longest = max(
       file_re.finditer(r"(hi\n)+", "logs.txt", max_span_lines=10),
       key=lambda m: m.end() - m.start(),
       default=None,
   )

.. note::

   This is a breaking change from ``file_re`` 1.x, which attempted to
   return a "longer" match by continuing to scan after the first hit.
   See :doc:`migration_1_to_2` for details.

Multiprocessing over huge files
-------------------------------

For files in the 10 GB-100 GB range, the practical pattern is to split
the file into ranges and fan out across a pool of processes. Each
worker holds a bounded window (for example ``max_span_lines=5``) so
total resident memory stays flat no matter how large the file.

.. code-block:: python

   import os
   from concurrent.futures import ProcessPoolExecutor
   from pathlib import Path

   from file_re import file_re

   PATTERN = r"BEGIN TXN\n(?:.*\n){0,3}END TXN"

   def count_matches(shard: Path) -> int:
       total = 0
       for _ in file_re.finditer(PATTERN, shard, max_span_lines=5):
           total += 1
       return total

   def run(shards: list[Path]) -> int:
       with ProcessPoolExecutor(max_workers=16) as pool:
           return sum(pool.map(count_matches, shards))

   if __name__ == "__main__":
       shards = sorted(Path("/var/log/app").glob("*.log.gz"))
       print(run(shards))

A few notes on this pattern:

- Shard at natural file boundaries (per-hour logs, per-host logs,
  rotated files). Splitting a single file mid-stream requires custom
  code to avoid tearing events across shard boundaries.
- ``file_re`` releases the GIL while reading and matching, so a thread
  pool also works for IO-heavy workloads. A process pool is still the
  right choice when the bottleneck is the regex itself.
- Wheels are built with the Rust ``regex`` crate's standard tuning, so
  DFA-friendly patterns (no backreferences, no lookarounds) get the
  best throughput.

Compressed files
----------------

All three modes work transparently on ``.gz`` and ``.xz`` files. The
decompression cost is paid per-worker, so with the multiprocessing
pattern above, compressed logs scale roughly linearly with worker
count.
