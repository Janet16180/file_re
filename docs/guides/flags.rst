Flags
=====

``file_re`` accepts the same flag bitmask as :mod:`re`. Every entry
point that takes a ``flags`` keyword forwards it to the underlying Rust
regex engine after translation. Because ``file_re`` uses the Rust
``regex`` crate, a few flags behave differently than they do in CPython
``re`` and are documented here.

Supported flags
---------------

.. list-table::
   :header-rows: 1
   :widths: 20 30 50

   * - Python flag
     - Rust handling
     - Notes
   * - :data:`re.IGNORECASE` (``re.I``)
     - ``case_insensitive(true)``
     - Full parity with :mod:`re`.
   * - :data:`re.MULTILINE` (``re.M``)
     - ``multi_line(true)``
     - ``^`` and ``$`` match at line boundaries.
   * - :data:`re.DOTALL` (``re.S``)
     - ``dot_matches_new_line(true)``
     - ``.`` matches ``\n``.
   * - :data:`re.VERBOSE` (``re.X``)
     - ``ignore_whitespace(true)``
     - Full parity with :mod:`re`.
   * - :data:`re.UNICODE` (``re.U``)
     - Default-on; no-op.
     - Unicode character classes are always on in Rust's ``regex``.
   * - :data:`re.ASCII` (``re.A``)
     - ``unicode(false)``; emits :class:`UserWarning` on first use.
     - **Divergent**; see below.
   * - :data:`re.DEBUG`
     - Ignored; emits :class:`UserWarning`.
     - Rust ``regex`` has no equivalent debug output.
   * - :data:`re.LOCALE` (``re.L``)
     - Raises :class:`ValueError`.
     - No Rust equivalent; :mod:`re` itself discourages this flag.

Flags combine the same way as in :mod:`re`:

.. code-block:: python

   import re
   from file_re import file_re

   match = file_re.search(
       r"^error:.*$",
       "server.log",
       flags=re.IGNORECASE | re.MULTILINE,
   )

Rust-vs-Python divergences
--------------------------

``re.ASCII``
~~~~~~~~~~~~

In CPython, :data:`re.ASCII` scopes ``\w``, ``\s``, ``\d``, and ``\b``
to ASCII for the patterns that use them. The Rust ``regex`` crate has
no equivalent scoping: it only exposes an all-or-nothing
``unicode(false)`` switch that turns off Unicode interpretation for the
entire pattern. ``file_re`` translates :data:`re.ASCII` to
``unicode(false)``, which is broader than what :mod:`re` does.

In practice the results are usually equivalent for ASCII-only input,
but patterns that mix ASCII and non-ASCII character classes will not
behave identically. To surface this, ``file_re`` emits a
:class:`UserWarning` the first time ``re.ASCII`` is used in a process:

.. code-block:: text

   UserWarning: re.ASCII in file_re disables Unicode character class
   matching entirely (Rust regex semantics); this is broader than
   Python's re.ASCII.

``re.LOCALE``
~~~~~~~~~~~~~

CPython implements :data:`re.LOCALE` by consulting the current C locale
at match time for byte patterns. Rust's ``regex`` has no locale
concept and ``file_re`` does not attempt to emulate one. Passing
:data:`re.LOCALE` raises :class:`ValueError`:

.. code-block:: python

   import re
   from file_re import file_re

   file_re.search(r"\w+", "data.txt", flags=re.LOCALE)
   # ValueError: re.LOCALE is not supported by file_re.

If you have existing :mod:`re` code that uses :data:`re.LOCALE`, note
that :mod:`re` itself deprecated the flag for ``str`` patterns in
Python 3.6. The usual migration is to drop the flag and rely on the
default Unicode semantics.

``re.DEBUG``
~~~~~~~~~~~~

The Rust ``regex`` crate does not have an equivalent of :mod:`re`'s
debug print. ``file_re`` ignores :data:`re.DEBUG` and emits a
:class:`UserWarning` so the loss of behavior is visible:

.. code-block:: text

   UserWarning: re.DEBUG is not supported by file_re and is ignored.

Inline directives
-----------------

Inline flags such as ``(?i)``, ``(?m)``, ``(?s)``, and ``(?x)`` are
handled by the Rust ``regex`` crate directly and are always supported
regardless of the ``flags`` keyword. The underlying compiler uses
``RegexBuilder``, so keyword flags and inline directives compose
predictably.
