.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

=============================
Branch model and release flow
=============================

EOLA has two long-lived branches. ``eola-next`` is the integration branch,
where every change lands first. ``main`` carries released code and
specification drafts only. Releases and release candidates are tagged on
``eola-next``, and ``main`` reaches each release through a merge::

    feature branch --PR, merge commit--> eola-next --PR, merge commit--> main
                                         v* tags

Integration branch
==================

Pull requests open against ``eola-next`` and are merged as merge commits.

Releases
========

``VERSION`` in the repository root holds the version of the latest release
or release candidate, ``0.0.0`` before the first. A release is a commit on
``eola-next`` titled ``build: <version>`` that changes only ``VERSION``, and
a signed tag ``v<version>`` on that commit. A release candidate is tagged
``v<version>-rc<n>`` the same way.

Versions follow semantic versioning. Every release before the specification
is frozen is ``0.y.z`` and may change the ``EOLA1`` format, the C ABI or the
Go API. ``1.0.0`` is the first release with a frozen specification. The
release version is independent of the revision numbers of the specification
drafts and of the format version that documents carry.

Stable branch
=============

``main`` changes only through a pull request from ``eola-next``, merged as a
merge commit so the commits keep the hashes they had on ``eola-next``. The
maintainer opens it once a release is tagged, merges it, and moves
``eola-next`` to the merge, so both branches point at the same commit.

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
