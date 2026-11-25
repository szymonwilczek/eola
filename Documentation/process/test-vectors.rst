.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

============
Test vectors
============

The test vectors under ``vectors/`` are the shared contract of the
implementations: libeola and the Go packages run the same files and report
the same result for each. For every format there is at least one valid
document and one invalid document for each error code of the format.

Layout
======

``vectors/<format>/``
   The vectors of one format, named after its draft, for example
   ``vectors/signed-document/`` for
   ``draft-wilczek-eola-signed-document``. Each vector is a file of exact
   octets, ``<name>.eola``.

``vectors/<format>/vectors.txt``
   The manifest. Each line other than a comment is

   .. code-block:: text

      <file> <check> <result>

   The check ``document`` parses the file as a document. The result is
   ``ok``, or the name of the error code of the first processing rule the
   file breaks.

``vectors/generate.py``
   The generator. It writes every vector and every manifest, so the
   vectors are reviewed as the script. ``--check`` reports files that
   differ from what it writes, and files it does not write.

A vector holds octets the format rejects, such as carriage returns,
trailing spaces and blank lines. ``.gitattributes`` stores the ``.eola``
files as they are and exempts them from the whitespace checks. A vector
carries no license line; the ``CC-BY-4.0`` line of its manifest covers it.

Changing the vectors
====================

A change to a format changes its vectors in the same commit: the draft,
the generator, the regenerated files, and both implementations.

.. code-block:: console

   $ vectors/generate.py
   $ vectors/generate.py --check
   $ make -C libeola check
   $ (cd go && go test ./...)

Grammar check
=============

``make -C spec check`` runs ``spec/check-grammar.py``. It loads the ABNF
blocks of each draft as one grammar and fails when the grammar references a
rule it does not define, other than the core rules of RFC 5234. It then
parses every vector of the draft with the grammar: a valid vector matches,
and an invalid vector does not. A vector whose error code comes from a size
limit is skipped, since the grammar states no limits. The ABNF parser is
pinned in ``spec/requirements.txt``.
