.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

=============================
Branch model and release flow
=============================

EOLA has two long-lived branches. ``eola-next`` is the integration branch,
where every change lands first. ``main`` carries released code and
specification drafts only. Release candidates are tagged on ``eola-next``,
releases on ``main``::

    feature branch --PR--> eola-next --PR, merge commit--> main
                           v*-rc tags                      v* tags

Integration branch
==================

Pull requests open against ``eola-next``. Release candidates are tagged here
as ``v<version>-rc<n>``.

Stable branch
=============

``main`` changes only through a pull request from ``eola-next``, merged as a
merge commit so the commits keep the hashes they had on ``eola-next``. The
maintainer opens and merges it and tags the release on ``main``.

Published documentation
=======================

``.github/workflows/documentation-deploy.yml`` builds the documentation of
both branches on every push to either and publishes them as one GitHub Pages
site at ``https://szymonwilczek.github.io/eola/``:

stable
   Built from ``main``, at the site root. Until ``main`` carries a
   documentation tree, the root links to the development channel.

development
   Built from ``eola-next``, under ``/eola-next/``. Every page carries a
   banner naming the channel and is kept out of search results.

Each channel carries the specification drafts of its branch under
``spec/``, rendered as HTML and plain text, and their patent declarations
under ``spec/owfa/``.

The version label of each channel is the branch name and the short hash of
the commit it was built from. A local build is labelled ``local``.
