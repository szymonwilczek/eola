.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

=====================
The libeola C library
=====================

libeola is the C11 implementation of EOLA for clients, games and servers.
It parses and verifies documents in the buffer of the caller, and a
parsed document points into the octets it was parsed from. The parser and
the value decoders allocate no memory. ``eola_document_verify()`` checks
the Ed25519 signature with libcrypto of OpenSSL, which allocates; libeola
does not sign.

Building and testing
====================

libeola needs the headers and the library of libcrypto, found with
``pkg-config``; on Debian and Ubuntu they are in ``libssl-dev`` and on
Fedora in ``openssl-devel``. The checks run against OpenSSL 3.0 of Ubuntu
24.04 and against OpenSSL 3.5, 4.0 and 4.1 built from their releases.

.. code-block:: console

   $ make -C libeola
   $ make -C libeola check

``make -C libeola`` builds the static library ``libeola/build/release/libeola.a``;
a program links it with ``-lcrypto``. The targets of ``libeola/Makefile``:

``all``
   Builds the library. The default target.

``check``
   Builds and runs the tests and the test vectors of ``vectors/``.

``check-sanitize``
   Runs the same tests built with AddressSanitizer and
   UndefinedBehaviorSanitizer, in ``libeola/build/sanitize/``. A sanitizer
   report fails the run.

``check-valgrind``
   Runs the tests under valgrind. A memory error or a leak fails the run.
   The vector test frees the state of OpenSSL before it exits, so no block
   is left reachable.

``fuzz``
   Builds the libFuzzer targets of ``libeola/fuzz/`` with clang,
   AddressSanitizer and UndefinedBehaviorSanitizer, in
   ``libeola/build/fuzz/``.

``fuzz-run``
   Seeds the corpus of each target with the test vectors and runs it for
   ``FUZZ_SECONDS`` seconds. An input that fails a target
   is saved under ``libeola/build/fuzz/crashes/``.

``format``
   Formats the C sources in place with clang-format and the repository
   ``.clang-format``.

``format-check``
   Reports every C source that ``format`` would change.

``clean``
   Removes ``libeola/build/``.

``help``
   Lists the targets and the variables.

The variables of ``libeola/Makefile``, set on the command line or in the
environment:

``CC``
   The compiler of the library and the tests. Default: ``cc``.

``CFLAGS``
   The optimization and debug flags. Default: ``-O2 -g``. The warning flags
   and ``-Werror`` are always on.

``BUILD_DIR``
   The output directory, relative to ``libeola/``. Default: ``build``; the
   paths on this page use the default.

``CLANG``
   The compiler of the fuzz targets. Default: ``clang``.

``CLANG_FORMAT``
   The formatter of ``format`` and ``format-check``. Default:
   ``clang-format``.

``VALGRIND``
   The valgrind of ``check-valgrind``. Default: ``valgrind``.

``PKG_CONFIG``
   The pkg-config that finds libcrypto. Default: ``pkg-config``.

``OPENSSL_CFLAGS``, ``OPENSSL_LIBS``
   The compiler and linker flags of libcrypto, to build against an
   OpenSSL that pkg-config does not find. Default: the output of
   ``pkg-config --cflags libcrypto`` and ``pkg-config --libs libcrypto``.

``FUZZ_SECONDS``
   The run time of each fuzz target in ``fuzz-run``, in seconds. Default:
   ``60``.

``V``
   ``V=1`` prints every command in full.

The formatting depends on the clang-format release, so the version is pinned in
``libeola/requirements.txt``:

.. code-block:: console

   $ pip install -r libeola/requirements.txt
   $ make -C libeola format-check

Using the library
=================

A program includes the headers under ``libeola/include/`` and links
``libeola.a``:

.. code-block:: c

   #include <eola/document.h>

   struct eola_document document;
   struct eola_field field;
   size_t cursor = 0;
   enum eola_status status;

   status = eola_document_verify(text, text_length, "heartbeat",
                                 publisher_key, &document);
   if (status != EOLA_STATUS_OK) {
           fprintf(stderr, "rejected: %s\n", eola_status_name(status));
           return -1;
   }
   while (eola_document_next_field(&document, &cursor, &field))
           printf("%.*s = %.*s\n", (int)field.name_length, field.name,
                  (int)field.value_length, field.value);

The caller knows the document type and the public key of the signer
before it reads the document; ``publisher_key`` is that key, 32 octets.
``eola_document_verify()`` returns ``EOLA_STATUS_OK`` only for a document
signed with it, and its fields end with ``signer`` and ``signature``.
``eola_document_parse()`` checks the framing alone, for tools that read a
document without acting on it.

A field value is decoded with ``eola_hex_value_decode()`` or
``eola_decimal_value_decode()``, as the specification of the document
type gives its encoding. Every function other than
``eola_document_next_field()`` and ``eola_status_name()`` returns an
``enum eola_status``. The codes from 100 up are
the error codes of the specification, with its numbers, and
``eola_status_name()`` returns the name the specification gives them.
``EOLA_STATUS_CRYPTO_FAILURE`` reports that OpenSSL failed, for example to
allocate memory: the document is then neither accepted nor rejected.

Status codes
============

.. kernel-doc:: libeola/include/eola/status.h

Documents
=========

.. kernel-doc:: libeola/include/eola/document.h

Limits
------

.. c:macro:: EOLA_DOCUMENT_MAX_LENGTH

   The largest document, 65536 octets.

.. c:macro:: EOLA_LINE_MAX_LENGTH

   The largest line, 8192 octets, its LF included.

.. c:macro:: EOLA_PUBLIC_KEY_LENGTH

   An Ed25519 public key, 32 octets.

.. c:macro:: EOLA_SIGNATURE_LENGTH

   An Ed25519 signature, 64 octets.

Field values
============

.. kernel-doc:: libeola/include/eola/value.h

Files
=====

``libeola/include/eola/``
   The public headers.

``libeola/src/``
   The library sources. ``signature.c`` is the only one that calls
   OpenSSL; it checks the encodings of the key and the signature on their
   octets before OpenSSL sees them.

``libeola/tests/``
   The tests: ``vectors.c`` runs the test vectors, ``arguments.c`` checks
   the arguments the vectors do not reach.

``libeola/fuzz/``
   The fuzz targets. ``document.c`` checks that every document the parser
   accepts rebuilds to its input. ``value.c`` checks that every value a
   decoder accepts encodes back to its input, and that the decimal decoder
   agrees with ``strtoull()`` on every input of digits without a leading
   zero. ``verify.c`` checks that the verifier gives the code of the parser
   for a document the parser rejects, never reports a failure of OpenSSL,
   and accepts only a parsed document that ends with the signer and
   signature fields.

``libeola/Makefile``
   The build and the test targets.

``.clang-format``
   The formatting of the C sources.
