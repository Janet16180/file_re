Module-level functions
======================

.. currentmodule:: file_re

These module-level entry points mirror :mod:`re` and are thin adapters
around the Rust extension. Each accepts either a :class:`str` or
:class:`pathlib.Path` as the file path and dispatches on
``max_span_lines``.

.. autoclass:: file_re.core.file_re_cls
   :members: search, match, findall, finditer, compile
   :no-show-inheritance:
