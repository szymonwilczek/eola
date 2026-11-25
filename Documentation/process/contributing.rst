.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

============
Contributing
============

Changes land on the ``eola-next`` integration branch, through a pull
request. ``main`` carries released code only; :doc:`branching` describes
both branches. This page sets out what a commit and a pull request carry.

External contracts
==================

The specification is the reference for every implementation in the tree. A
change to an external contract updates the specification, its test vectors
and the documentation in the same commit as the code. External contracts
include document formats, error codes, the C and Go APIs, and command-line
flags.

Commits
========

One logical change per commit. Each commit builds and passes the tests on
its own, and an unrelated refactor goes in a commit of its own.

Subject
-------

The subject starts with a bare prefix naming the area it changes::

    spec: heartbeat: define the expiry field
    libeola: reject a document with trailing bytes
    docs: publisher: describe key rotation
    libeola/go: agree on the error code for a revoked key
    ci: build against OpenSSL 4

A second prefix after ``": "`` names a submodule (``docs: publisher:``). A
slash joins two areas a commit changes together (``libeola/go:``). A
Conventional Commits scope such as ``fix(spec):`` is not used.

Subjects, pull request titles and branch names are at most 75 columns.

Body
----

The body is prose, in lines of at most 75 columns. Its first paragraph
describes what is wrong or missing and why it matters; the next one says
what the commit changes, and why this way. A reproducer that does not
belong in the tests follows as an indented block of the commands and their
output.

The body ends with the sign-off after one blank line.

Sign-off and signature
----------------------

Every commit carries a Developer Certificate of Origin trailer,
``Signed-off-by: Name <email>``, added by ``git commit -s``. The sign-off
certifies that the contribution may be submitted under the project's
licenses.

Every commit is also signed with GPG or SSH (``git commit -S``, or
``commit.gpgsign`` set to ``true``), so that GitHub marks it verified.

Reporting issues
================

A defect or a proposed change is reported as a GitHub issue. A suspected
vulnerability never goes into a public issue; :doc:`security-bugs` describes
the private channel.

Pull requests
=============

A pull request opens against ``eola-next`` and carries:

* one focused change set,
* tests for the behaviour it changes,
* documentation updates for changed behaviour,
* no generated build artifacts,
* no private keys, local logs or credentials.

Tagging a release and merging ``eola-next`` into ``main`` are maintainer
actions.
