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

   The check ``document`` parses the file as a document, ``hex:<n>``
   decodes it as a hexadecimal value of *n* octets, and ``decimal`` as a
   decimal value. ``verify:<type>:<key>`` verifies it as a signed document
   of the document type *type*, signed with the Ed25519 public key *key*
   in hexadecimal. The result is ``ok``, or the name of the error code of
   the first processing rule the file breaks. For a valid file, both
   implementations also write the parsed document or the decoded value
   back in text form and compare it with the file.

``vectors/<format>/test-keys.txt``
   The Ed25519 keys that sign the vectors, one per line as
   ``<name> <seed> <public key>`` in hexadecimal. Their private keys are
   published, so they sign nothing but test vectors.

``vectors/generate.py``
   The generator. It writes every vector and every manifest, so the
   vectors are reviewed as the script. It signs with its own Ed25519 of
   RFC 8032, checked against the test vectors of the RFC, so that a vector
   that no library would produce, such as a signature for a key that is
   not canonical, is written as easily as a valid one. ``--check`` reports files that
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
and an invalid vector does not. A vector whose error code comes from a rule
the grammar does not state, a size limit, the length of a hexadecimal
value, the range of a decimal value, the document type or key a receiver
expects, the uniqueness of a reserved field name, or the signature
itself, is skipped. The ABNF parser is
pinned in ``spec/requirements.txt``.
