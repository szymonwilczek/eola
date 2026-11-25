# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
#
# Configuration for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

project = "EOLA"
author = "Szymon Wilczek"
copyright = "2026, Szymon Wilczek"  # noqa: A001 - Sphinx-reserved name

extensions: list[str] = []

source_suffix = {".rst": "restructuredtext"}
root_doc = "index"
language = "en"
exclude_patterns = ["_build"]
smartquotes = False

try:
    import sphinx_rtd_theme  # noqa: F401

    html_theme = "sphinx_rtd_theme"
except ImportError:
    html_theme = "alabaster"

html_title = "EOLA"
html_show_sourcelink = True
