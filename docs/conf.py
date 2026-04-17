"""Sphinx configuration for file_re documentation."""

from __future__ import annotations

from datetime import date
from importlib import metadata

project = "file_re"
author = "file_re contributors"
copyright = f"{date.today().year}, {author}"

release = metadata.version("file_re")
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

html_theme = "sphinx_rtd_theme"
html_title = f"file_re {release}"
html_static_path: list[str] = []

html_theme_options = {
    "navigation_depth": 3,
    "collapse_navigation": False,
    "sticky_navigation": True,
    "style_external_links": True,
}

pygments_style = "sphinx"

nitpicky = False
