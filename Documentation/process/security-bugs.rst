.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

=============
Security bugs
=============

A suspected vulnerability in EOLA is reported privately, never in a public
issue, pull request or review comment. This covers the specification, the
test vectors, the C library and the Go services, and any other path listed
under `Scope`_.

Contact
========

The primary channel is GitHub Private Vulnerability Reporting for
``github.com/szymonwilczek/eola``. It opens a private security advisory
visible only to the reporter and the maintainer.

When that channel is not available, send the report by encrypted email:

* Email: ``swilczek.lx@gmail.com``
* GPG fingerprint: ``3EE5 3281 2DF0 F36A B7A1 F178 B8E9 4407 1CB7 EB8A``

What to include
===============

* the affected component or specification section, and the version or
  commit,
* reproduction steps, a minimal proof of impact, or the documents that
  trigger it,
* the security property expected and the one observed,
* whether the report has been shared with anyone else.

Response
========

The maintainer:

* acknowledges a report within 72 hours,
* completes the initial triage within 72 hours of enough detail being
  available,
* aims to fix a critical vulnerability within 14 calendar days of
  reproducing it,
* agrees the disclosure date with the reporter when a public advisory is
  needed.

A flaw in the specification itself can take longer, since every
implementation has to change with it.

Disclosure
==========

A fix whose public review would expose an active exploit is reviewed on a
private branch. Until the advisory date, its public commits describe the
functional change and carry no exploit details. When the vulnerability
affects a released artifact or a published specification draft, the
maintainer publishes a GitHub security advisory.

Supported versions
==================

Security fixes land on ``eola-next`` and ship in the next release and the
next specification draft.

Scope
=====

In scope:

* the specification: a rule that lets a forged, replayed or altered
  document be accepted, or a guarantee it states and does not provide,
* the test vectors, when one marks an invalid document as valid,
* the C library and the Go services and tools in this repository.

Out of scope:

* LOTA, a separate project: report it through the security channel of
  ``github.com/szymonwilczek/lota``,
* detecting cheat behaviour in games,
* infrastructure operated by a publisher or a community server.
