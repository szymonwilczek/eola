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

A ``v*`` tag runs ``.github/workflows/release.yml``. It refuses a tag that
does not match ``VERSION`` or is not on ``eola-next``, renders the
specification drafts and publishes a GitHub release with:

* ``eola-<version>.tar.gz``, the source of the tag from ``git archive``,
* each specification draft as RFCXML, plain text and HTML,
* ``SHA256SUMS``, the SHA-256 of each of these files,
* ``SHA256SUMS.cosign.bundle``, a keyless cosign signature of
  ``SHA256SUMS``.

The notes are the message of the tagged commit. A ``0.y.z`` release and a
release candidate are published as pre-releases. To check the files of a
release, verify the manifest and then the files against it::

    $ cosign verify-blob \
          --bundle SHA256SUMS.cosign.bundle \
          --certificate-identity-regexp \
            '^https://github\.com/szymonwilczek/eola/\.github/workflows/release\.yml@refs/tags/v' \
          --certificate-oidc-issuer https://token.actions.githubusercontent.com \
          SHA256SUMS
    $ sha256sum -c SHA256SUMS

A valid signature says that the release workflow, run for a ``v`` tag,
produced the manifest.

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
site at ``https://eola.szymon-wilczek.me/``:

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
