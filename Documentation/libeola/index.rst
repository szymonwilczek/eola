.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

=====================
The libeola C library
=====================

libeola is the C11 implementation of EOLA for clients, games and servers.
It parses documents in the buffer of the caller: no function allocates
memory, and a parsed document points into the octets it was parsed from.

Building and testing
====================

.. code-block:: console

   $ make -C libeola
   $ make -C libeola check

``make -C libeola`` builds the static library ``libeola/build/release/libeola.a``.
The targets of ``libeola/Makefile``:

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

``CLANG_FORMAT``
   The formatter of ``format`` and ``format-check``. Default:
   ``clang-format``.

``VALGRIND``
   The valgrind of ``check-valgrind``. Default: ``valgrind``.

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

   status = eola_document_parse(text, text_length, &document);
   if (status != EOLA_STATUS_OK) {
           fprintf(stderr, "rejected: %s\n", eola_status_name(status));
           return -1;
   }
   while (eola_document_next_field(&document, &cursor, &field))
           printf("%.*s = %.*s\n", (int)field.name_length, field.name,
                  (int)field.value_length, field.value);

Every function returns an ``enum eola_status``. The codes from 100 up are
the error codes of the specification, with its numbers, and
``eola_status_name()`` returns the name the specification gives them.

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

Files
=====

``libeola/include/eola/``
   The public headers.

``libeola/src/``
   The library sources.

``libeola/tests/``
   The tests: ``vectors.c`` runs the test vectors, ``arguments.c`` checks
   the arguments the vectors do not reach.

``libeola/Makefile``
   The build and the test targets.

``.clang-format``
   The formatting of the C sources.
