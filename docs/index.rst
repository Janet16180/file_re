file_re
=======

``file_re`` is a Rust-backed Python library for running regular expressions
over large files. It mirrors the public surface of :mod:`re` and adds a
single ``max_span_lines`` parameter that controls how much of the file is
held in memory, so the same API scales from small configuration files to
50 GB compressed logs.

Highlights
----------

- ``search``, ``match``, ``findall``, ``finditer``, and ``compile`` with the
  same shape as :mod:`re`.
- A ``max_span_lines`` knob: ``None`` for full-file scans, ``1`` for
  line-by-line streaming, and ``N`` for a sliding N-line window.
- Transparent ``.gz`` and ``.xz`` decompression.
- Proper :class:`re.Match` semantics, including ``None`` for
  non-participating groups.
- GIL is released during IO and regex work, so ``file_re`` plays well with
  ``multiprocessing`` and threaded pipelines.

.. toctree::
   :maxdepth: 2
   :caption: Getting started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: Guides

   guides/large_files
   guides/flags
   guides/migration_1_to_2

.. toctree::
   :maxdepth: 2
   :caption: API reference

   api/file_re
   api/pattern
   api/match

Indices and tables
------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
