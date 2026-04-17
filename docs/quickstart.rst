Quickstart
==========

``file_re`` mirrors the shape of :mod:`re`, so existing regex patterns and
call sites translate directly. The one new concept is
``max_span_lines``, which controls how much of the file is held in memory
while scanning.

Basic search
------------

.. code-block:: python

   from pathlib import Path
   from file_re import file_re

   log = Path("server.log")

   match = file_re.search(r"ERROR: (?P<msg>.+)", log)
   if match:
       print(match.group("msg"))

``file_re.search`` returns an :class:`~file_re.Match` or ``None``, just
like :func:`re.search`.

Capture groups and named groups
-------------------------------

.. code-block:: python

   from file_re import file_re

   match = file_re.search(
       r"(?P<user>[\w.\-]+)@(?P<domain>[\w.\-]+)",
       "contacts.txt",
   )
   if match:
       print(match.group("user"), match.group("domain"))
       print(match.groupdict())
       print(match.groups())

Non-participating groups are reported as ``None`` (matching :mod:`re`).

findall and finditer
--------------------

.. code-block:: python

   from file_re import file_re

   phones = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", "contacts.txt")

   for match in file_re.finditer(r"\bERROR\b", "server.log"):
       print(match.span(), match.group())

``finditer`` yields matches lazily and is the recommended choice when the
number of matches is large or unknown.

Compiled patterns
-----------------

For patterns reused across many files, compile once and reuse:

.. code-block:: python

   import re
   from file_re import file_re

   pattern = file_re.compile(r"error: (\w+)", flags=re.IGNORECASE)

   for log in ("server1.log", "server2.log", "server3.log"):
       for match in pattern.finditer(log):
           handle(match)

Flags
-----

``file_re`` accepts the same flag bitmask as :mod:`re`:

.. code-block:: python

   import re
   from file_re import file_re

   match = file_re.search(r"error", "server.log", flags=re.IGNORECASE | re.MULTILINE)

See :doc:`guides/flags` for details and divergences from :mod:`re`.

Compressed files
----------------

``.gz`` and ``.xz`` files are decoded transparently — no special call is
needed:

.. code-block:: python

   from file_re import file_re

   matches = file_re.findall(r"(\d{3})-(\d{3})-(\d{4})", "logs/2026-04.log.gz")

Large files
-----------

For files that do not fit comfortably in memory, pass
``max_span_lines``:

.. code-block:: python

   from file_re import file_re

   # Stream line by line. Matches cannot cross a newline.
   for match in file_re.finditer(r"ERROR", "huge.log", max_span_lines=1):
       handle(match)

   # Slide a 5-line window. Patterns may span up to 5 lines.
   for match in file_re.finditer(
       r"BEGIN TXN\n(?:.*\n){0,3}END TXN",
       "huge.log",
       max_span_lines=5,
   ):
       handle(match)

See :doc:`guides/large_files` for the full guide, including the
multiprocessing pattern used for 50 GB log scans.
