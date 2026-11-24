.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

=======================
End-Of-Life Attestation
=======================

End-Of-Life Attestation, or EOLA, is an open protocol for keeping a game
playable after its publisher stops operating it.

A publisher signs, while it still runs the game, the material that lets
players and community servers continue without it: a heartbeat announcing
whether the official service is alive, a list of servers, and the records
players carry between them.

Documentation
=============

The documentation is under `Documentation/ <Documentation/index.rst>`_ and
is built with ``make -C Documentation html``.

Licensing
=========

Code is MIT (`LICENSE <LICENSE>`_). The specification and the test vectors
are CC-BY-4.0 (`LICENSE.CC-BY-4.0 <LICENSE.CC-BY-4.0>`_). Every published
draft of the specification carries an Open Web Foundation Final
Specification Agreement (OWFa 1.0, Patent Only) signed for that draft.
Every source file carries an ``SPDX-License-Identifier`` naming the license
that applies to it.
