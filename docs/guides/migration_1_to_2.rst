Migrating from 1.x to 2.0
=========================

``file_re`` 2.0 is a breaking release. The goal was to align with
:mod:`re` as closely as a streaming file regex library reasonably can,
and to remove mode keywords that had become redundant. This guide walks
through each behavior change and shows the mechanical migration for
existing call sites.

If you are adopting 2.0, read this guide top to bottom. Most of the
changes are a rename or a default.

Minimum Python 3.9
------------------

``file_re`` 2.0 drops support for Python 3.8. CPython 3.9 through 3.13
are supported, and wheels are published for each. If you are still on
3.8, pin ``file_re < 2``.

``multiline=True`` is now the default
-------------------------------------

In 1.x, ``multiline=True`` opted into loading the whole file into
memory so patterns could span lines. This is now the default behavior
and there is no ``multiline`` keyword.

**Before (1.x):**

.. code-block:: python

   file_re.search(r"<body>[\s\S]+</body>", path, multiline=True)

**After (2.0):**

.. code-block:: python

   file_re.search(r"<body>[\s\S]+</body>", path)

The new knob that controls memory usage is ``max_span_lines``, which
defaults to ``None`` (load the whole file). See
:doc:`large_files` for how to pick a value for streaming scans.

``num_lines=N`` is now ``max_span_lines=N``
-------------------------------------------

The sliding-window mode has been renamed for clarity. Replace the
keyword; the semantics of the ``N`` value are the same.

**Before (1.x):**

.. code-block:: python

   file_re.search(r"hi\nword", path, num_lines=2)
   file_re.findall(r"hi\nworld", path, num_lines=2)

**After (2.0):**

.. code-block:: python

   file_re.search(r"hi\nword", path, max_span_lines=2)
   file_re.findall(r"hi\nworld", path, max_span_lines=2)

``max_span_lines=1`` now explicitly selects the line-by-line streaming
mode. In 1.x the "default mode" was implicitly line-by-line; in 2.0
that behavior is reached by passing ``max_span_lines=1`` explicitly.

``search()`` in window mode now returns the first match
-------------------------------------------------------

1.x tried to return a "longer" match by continuing to scan for
``num_lines`` additional lines after a hit. The comparison logic was
incorrect (it compared absolute ``end`` offsets rather than match
length), so the behavior was effectively "usually the first match, but
occasionally a later one." 2.0 replaces this with the same contract
as :func:`re.search` against the full concatenated text: the first
match wins.

If you relied on 1.x returning the longest match, iterate explicitly:

.. code-block:: python

   from file_re import file_re

   longest = max(
       file_re.finditer(r"(hi\n)+", path, max_span_lines=3),
       key=lambda m: m.end() - m.start(),
       default=None,
   )

``Match.groups`` now contains ``None`` for non-participating groups
-------------------------------------------------------------------

To match :class:`re.Match`, a capture group that did not participate in
the match is now ``None`` in ``Match.groups()`` and
``Match.groupdict()``. In 1.x it was the empty string ``""``.

**Before (1.x):**

.. code-block:: python

   m = file_re.search(r"(foo)|(bar)", "foo")
   m.groups()  # ('foo', '')

**After (2.0):**

.. code-block:: python

   m = file_re.search(r"(foo)|(bar)", "foo")
   m.groups()  # ('foo', None)

If your code depended on the empty-string convention, the idiomatic
replacement is ``g or ""``:

.. code-block:: python

   foo, bar = m.groups()
   foo = foo or ""
   bar = bar or ""

Flag changes
------------

:data:`re.LOCALE` now raises :class:`ValueError`. The Rust ``regex``
crate has no locale concept, and 1.x silently ignored this flag. If
you were passing it, drop it.

:data:`re.ASCII` emits a :class:`UserWarning` on first use, documenting
that Rust's equivalent (``unicode(false)``) is broader than
:mod:`re`'s. See :doc:`flags`.

:data:`re.DEBUG` emits a :class:`UserWarning` and is otherwise ignored.

All other common flags (:data:`re.IGNORECASE`, :data:`re.MULTILINE`,
:data:`re.DOTALL`, :data:`re.VERBOSE`) now work as keyword arguments in
addition to the inline ``(?i)`` directives that were the only supported
form in 1.x.

New: ``finditer``, ``match``, and ``compile``
---------------------------------------------

2.0 adds three entry points that did not exist in 1.x:

- :meth:`~file_re.core.file_re_cls.finditer` — lazy iteration over
  matches. Preferred over ``findall`` for large files.
- :meth:`~file_re.core.file_re_cls.match` — anchored at start of file.
- :meth:`~file_re.core.file_re_cls.compile` — returns a
  :class:`~file_re.Pattern` for reuse across files.

.. code-block:: python

   import re
   from file_re import file_re

   pattern = file_re.compile(r"error: (\w+)", flags=re.IGNORECASE)
   for log in ("a.log", "b.log", "c.log"):
       for match in pattern.finditer(log):
           handle(match)

Streaming ``\r\n`` handling
---------------------------

1.x's streaming modes did not strip the trailing ``\r`` from Windows
line endings, so patterns ending in ``$`` or matching a final newline
could behave differently on CRLF files. 2.0 normalizes line endings in
all streaming paths. No code change is required, but results on
CRLF-encoded files may shift if you previously worked around this.
