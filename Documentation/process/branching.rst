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
