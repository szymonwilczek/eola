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

      verified, err := document.Verify(text, "heartbeat", publisherKey)
      if errors.Is(err, status.SignatureInvalid) {
              // ...
      }

``document``
   ``document.Verify`` applies the processing rules and the signature
   processing rules of the signed document format for the document type
   and the Ed25519 public key the caller expects, and returns the document
   type and the fields in their order, or the ``status.Code`` of the first
   rule the text breaks. ``document.Sign`` adds the ``signer`` and
   ``signature`` fields of a private key to an unsigned document.
   ``document.Parse`` checks the framing alone.
   ``document.MaxDocumentLength`` and ``document.MaxLineLength`` are the
   limits of the format. ``document.DecodeHexValue`` and
   ``document.DecodeDecimalValue`` decode a field value, as the
   specification of the document type gives its encoding.

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

The tests run the test vectors of ``vectors/``, and sign each valid
signed vector again with its key of ``test-keys.txt`` to compare the
result with the vector. Three fuzz tests take the vectors as their seed
corpus: ``FuzzParse`` checks that every document ``Parse`` accepts
rebuilds to its input, ``FuzzDecodeValues`` that every value a decoder
accepts encodes back to its input and that the decimal decoder agrees
with ``strconv.ParseUint``, and ``FuzzVerify`` that ``Verify`` gives the
error of ``Parse`` for a document ``Parse`` rejects and that every
document ``Sign`` returns starts with its input and has two fields more.
Go fuzzes one test per run:

.. code-block:: console

   $ go test ./document -run '^$' -fuzz '^FuzzParse$' -fuzztime 60s

``go/.golangci.yml``
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
