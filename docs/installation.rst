Installation
============

``file_re`` ships pre-built wheels for CPython 3.9 through 3.13 across the
major platforms.

From PyPI
---------

.. code-block:: console

   pip install file_re

Supported platforms
-------------------

- Linux (``manylinux`` x86_64 / aarch64, ``musllinux`` x86_64)
- macOS (x86_64 and Apple Silicon)
- Windows (x86_64)

Python requirements
-------------------

- CPython 3.9 or newer.
- PyPy is supported on platforms where wheels are published.

Building from source
--------------------

Building from source requires a recent stable Rust toolchain (see
`rustup.rs <https://rustup.rs>`_) and `maturin
<https://www.maturin.rs>`_:

.. code-block:: console

   git clone https://github.com/Janet16180/file_re.git
   cd file_re/file_re
   pip install maturin
   maturin develop --release

Development install
-------------------

To run the test suite against a local build:

.. code-block:: console

   cd file_re
   pip install -r requirements.txt
   maturin develop --release
   pytest unit_tests/
