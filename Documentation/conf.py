# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
#
# Configuration for the Sphinx documentation builder.
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os

project = "EOLA"
author = "Szymon Wilczek"
copyright = "2026, Szymon Wilczek"  # noqa: A001 - Sphinx-reserved name

# The site serves two channels: "stable", built from main at the site root,
# and "dev", built from eola-next under /eola-next/. The deploy workflow
# sets the channel and the version label; a local build is the stable
# channel labelled "local".
channel = os.environ.get("EOLA_DOCS_CHANNEL", "").strip() or "stable"
release = os.environ.get("EOLA_DOCS_VERSION", "").strip() or "local"
version = release

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

html_title = f"EOLA {release}"
html_show_sourcelink = True
templates_path = ["_templates"]

# Both channels name the stable root as canonical, so a search engine
# sends readers to the documentation of the released code.
site_url = "https://szymonwilczek.github.io/eola/"
html_baseurl = site_url
html_context = {
    "eola_channel": channel,
    "eola_stable_url": site_url,
    "eola_dev_url": f"{site_url}eola-next/",
}
