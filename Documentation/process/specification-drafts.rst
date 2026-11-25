.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

====================
Specification drafts
====================

The specification of EOLA is a set of drafts under ``spec/``, one per part
of the protocol. Each draft is a kramdown-rfc source, ``draft-*.md``,
licensed CC-BY-4.0, and is rendered to plain text and HTML.

Building
========

.. code-block:: console

   $ pip install -r spec/requirements.txt
   $ gem install kramdown-rfc -v 1.7.43
   $ make -C spec

The rendered drafts are written to ``spec/build/``. The first build fetches
the referenced RFCs and caches them in ``spec/build/.refcache``. A warning
from xml2rfc fails the build. ``make -C spec check`` checks the ABNF of the
drafts against itself and the test vectors, as described in
:doc:`test-vectors`.

Names and versions
==================

A draft is named ``draft-wilczek-eola-<part>``, and its ``docname`` carries
the version, ``draft-wilczek-eola-<part>-<nn>``, starting at ``00``. Each
draft is versioned on its own.

Every normative change records what changed and why in the ``Change Log``
appendix of the draft, under the version that carries it. The change log is
the only place in a draft that describes earlier versions.

Patent declarations
===================

Every published version of a draft carries an Open Web Foundation Final
Specification Agreement, OWFa 1.0 (Patent Only), at
``spec/owfa/<docname>.txt``, added in the commit that publishes that
version. The file holds the original text of the agreement unchanged, with
the specification field set to the ``docname`` and the signature block
filled with the name and the ``Signed-off-by`` address of the signatory.

Files
=====

``spec/draft-*.md``
   The draft sources.

``spec/owfa/``
   The signed patent declarations, one per published draft version.

``spec/Makefile``
   The build.

``spec/check-grammar.py``
   The grammar check.

``spec/requirements.txt``
   The pinned versions of xml2rfc and of the ABNF parser.
