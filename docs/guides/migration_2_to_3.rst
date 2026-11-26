Migrating from 2.x to 3.0
=========================

3.0 replaces the streaming engine. Instead of reading one line at a time
and re-scanning a sliding window, ``file_re`` now reads the file in large
blocks and searches each block in place. The API is unchanged; this guide
lists the results that can differ from 2.x.

Window mode no longer cuts matches short
----------------------------------------

2.x reported a match as soon as the window first contained it, before the
following lines had been read. A greedy multi-line pattern could therefore
come back truncated:

.. code-block:: python

   # File: "BEGIN\nx\ny\nEND\n"
   file_re.search(r"BEGIN(?:\n.*){0,3}", path, max_span_lines=5)
   # 2.x: 'BEGIN'
   # 3.0: 'BEGIN\nx\ny\nEND'

3.0 decides a match only once every line it could reach has been read.
The rule is now exact: a match that starts on line ``L`` may extend up to,
but not including, the line terminator of line ``L + max_span_lines - 1``.

Anchors refer to the file, not to the window
--------------------------------------------

In 2.x streaming modes, ``^`` and ``\A`` matched at the start of every
line or window and ``$`` matched at the end of every line, even without
:data:`re.MULTILINE`. In 3.0 they mean the same thing in every mode:
without :data:`re.MULTILINE`, ``^`` and ``\A`` match only at the start of
the file and ``$`` only at its end.

If you relied on the old behavior, add the flag:

.. code-block:: python

   # 2.x
   file_re.findall(r"^ERROR.*$", path, max_span_lines=1)

   # 3.0
   file_re.findall(r"^ERROR.*$", path, flags=re.MULTILINE, max_span_lines=1)

``\r\n`` is read as ``\n`` in every mode
----------------------------------------

2.x stripped ``\r\n`` in streaming modes but not in whole-file mode (on
Linux and macOS), so the same match had different offsets depending on
``max_span_lines``. 3.0 always reads ``\r\n`` as ``\n``, like Python's
text mode does. Offsets now agree across modes and with
``re.search(pattern, open(path).read())``.

A pattern that matches ``\r`` explicitly will no longer find it before a
newline. A lone ``\r`` that is not followed by ``\n`` is left alone.

Empty matches
-------------

``findall`` and ``finditer`` now follow the same rule in every mode: an
empty match is allowed directly after a non-empty one, and the scan
resumes one character after an empty match. 2.x could report the same
empty match twice in window mode, and its whole-file ``findall`` skipped
an empty match that touched the previous match.

Concatenated gzip members
-------------------------

``.gz`` files made of several concatenated members (for example logs
that were compressed and appended) are now read to the end. 2.x stopped
after the first member.

Performance
-----------

- Streaming modes are several times faster, and the cost no longer grows
  with ``max_span_lines``.
- ``finditer`` and ``search`` in whole-file mode no longer recount
  characters from the start of the file for every match.
- For large files, ``max_span_lines`` is now faster than whole-file mode
  as well as lighter, because the read buffer is reused.
