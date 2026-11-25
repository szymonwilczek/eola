.. SPDX-License-Identifier: MIT
.. Copyright (C) 2026 Szymon Wilczek

===============
The Go packages
===============

The Go implementation of EOLA, for directories, trustees and tools, is
the module ``github.com/szymonwilczek/eola/go`` under ``go/``. It uses the
Go standard library only.

Packages
========

``status``
   The error codes of the specification. A ``status.Code`` is an
   ``error``; ``Name()`` returns the name the specification gives it, and
   its integer value is the number the specification gives it. A caller
   compares with ``errors.Is``:

   .. code-block:: go

      parsed, err := document.Parse(text)
      if errors.Is(err, status.LineTooLong) {
              // ...
      }

``document``
   ``document.Parse`` applies the processing rules of the signed document
   format and returns the document type and the fields in their order, or
   the ``status.Code`` of the first rule the text breaks.
   ``document.MaxDocumentLength`` and ``document.MaxLineLength`` are the
   limits of the format.

``go doc`` prints the full description of each package:

.. code-block:: console

   $ cd go
   $ go doc ./document

Testing
========

.. code-block:: console

   $ cd go
   $ go test -race ./...
   $ golangci-lint run ./...

The tests run the test vectors of ``vectors/``. ``go/.golangci.yml``
enables, besides the standard linters, gocritic, misspell, errorlint and
revive, and the gofumpt and goimports formatters.

Files
=====

``go/go.mod``
   The module and its Go version.

``go/status/``, ``go/document/``
   The packages and their tests.

``go/.golangci.yml``
   The linter configuration.
