"""Sphinx configuration for file_re documentation."""

from __future__ import annotations

import sys
from datetime import date
from importlib import metadata
from pathlib import Path

_PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "file_re" / "python"
if str(_PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(_PACKAGE_ROOT))

import file_re  # noqa: E402

project = "file_re"
author = "file_re contributors"
copyright = f"{date.today().year}, {author}"

try:
    release = metadata.version("file_re")
except metadata.PackageNotFoundError:
    release = file_re.__version__
version = ".".join(release.split(".")[:2])

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx.ext.viewcode",
    "sphinx.ext.githubpages",
    "sphinx_autodoc_typehints",
    "myst_parser",
]

source_suffix = {
    ".rst": "restructuredtext",
    ".md": "markdown",
}

exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

templates_path = ["_templates"]

language = "en"

napoleon_numpy_docstring = True
napoleon_google_docstring = False
napoleon_include_init_with_doc = False
napoleon_use_rtype = True
napoleon_use_param = True

autodoc_default_options = {
    "members": True,
    "undoc-members": False,
    "show-inheritance": True,
    "member-order": "bysource",
}
autodoc_typehints = "signature"
autodoc_typehints_format = "short"
autodoc_preserve_defaults = True

always_document_param_types = True
typehints_fully_qualified = False
typehints_document_rtype = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

html_theme = "furo"
html_title = f"file_re {release}"
html_static_path: list[str] = []

pygments_style = "sphinx"
pygments_dark_style = "monokai"

nitpicky = False
