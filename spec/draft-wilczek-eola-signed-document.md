---
# SPDX-License-Identifier: CC-BY-4.0
# Copyright (C) 2026 Szymon Wilczek
title: End-Of-Life Attestation (EOLA) Signed Document Format
abbrev: EOLA Signed Document Format
docname: draft-wilczek-eola-signed-document-00
category: info
ipr: none
submissiontype: independent
stand_alone: yes
keyword:
  - document format
  - ABNF
author:
  -
    fullname: Szymon Wilczek
    email: swilczek.lx@gmail.com

normative:
  RFC20:
  RFC5234:
  RFC7405:

informative:
  EOLA-ARCHITECTURE:
    title: End-Of-Life Attestation (EOLA) Architecture
    author:
      - ins: S. Wilczek
        name: Szymon Wilczek
    date: 2026-11
    seriesinfo:
      Internet-Draft: draft-wilczek-eola-architecture-00

--- abstract

This document specifies the text framing shared by every End-Of-Life
Attestation (EOLA) document: a type line followed by named fields, in a
strict subset of ASCII, with fixed size limits. It defines the order in
which a receiver checks a document and the error code it reports for
each rule a document breaks.

--- middle

# Introduction

Every document of EOLA {{EOLA-ARCHITECTURE}} that a client,
server, directory, or trustee acts on is a text document in the format
specified here. The format serves documents that are signed over their
exact bytes: a receiver accepts a document only in the one form the
grammar allows and never repairs, normalizes, or reinterprets it, so two
receivers of the same bytes reach the same result.

The format is text so that a person can read and check any document with
an ordinary text editor after the publisher of a game has stopped
operating it.

This document defines the framing of a document, its limits, the
processing rules a receiver applies, and their error codes. The document
types, their fields, and the order of those fields are defined by the
EOLA document that specifies each type.

# Conventions and Terminology

{::boilerplate bcp14-tagged}

The grammar in this document uses the Augmented Backus-Naur Form (ABNF)
notation of {{RFC5234}}, including the core rules DIGIT, LF, SP, and
VCHAR defined there, and the case-sensitive string notation %s"..." of
{{RFC7405}}. Octet values are those of US-ASCII {{RFC20}}.

Document:
: A sequence of octets in the format of {{framing}}.

Line:
: A sequence of octets in a document that ends with, and includes, the
  first LF after the end of the previous line, or after the start of the
  document.

Type line:
: The first line of a document.

Document type:
: The name in the type line.

Field:
: A line after the type line, made of a field name and a field value.

Receiver:
: An implementation that processes a document it has obtained.

# Document Framing {#framing}

A document is a type line followed by zero or more field lines:

~~~ abnf
document     = type-line *field-line

type-line    = %s"EOLA1" SP document-type LF
document-type = name

field-line   = field-name SP field-value LF
field-name   = name
field-value  = VCHAR *( *SP VCHAR )

name         = %x61-7A *( %x61-7A / DIGIT / "_" )
~~~

A name starts with a lowercase letter and continues with lowercase
letters, digits, and underscores. A field value is printable ASCII; it
can contain spaces, but it neither starts nor ends with one. A document
contains no octet other than LF, SP, and VCHAR: no carriage return, no
horizontal tab, no octet above %x7E. Every line, including the last,
ends with LF, and no line is empty.

The digit after "EOLA" is the version of the framing. Until this
document is published as version 1.0, its revisions change the framing
without changing the version. After that, a change to the framing that a
receiver of this version would accept with a different meaning uses
another version.

The document type separates the documents of EOLA from each other: a
receiver that expects one type rejects every other type, so a document
of one type is never accepted as a document of another.

A document can contain the same field name more than once. The
specification of a document type states which fields it contains, in
which order, and how often each occurs.

## Limits

A document is at most 65536 octets long. A line, including its LF, is at
most 8192 octets long. A document type can set lower limits for its own
documents.

The limits bound the memory and the work of a receiver that processes a
document from an untrusted source. A receiver can hold a whole document
in a fixed buffer.

# Processing Rules {#processing}

A receiver MUST check a document against the rules below, in the order
given, and MUST reject the document at the first rule it breaks with the
error code of that rule ({{error-codes}}). A receiver MUST NOT accept a
document that breaks any rule, and MUST NOT modify a document to make it
conform.

Rules 1 to 3 apply to the document as a whole:

1. The document is at most 65536 octets long. Otherwise:
   document_too_large.
2. Every octet of the document is LF, SP, or VCHAR. Otherwise:
   document_character.
3. The document is not empty, and its last octet is LF. Otherwise:
   document_unterminated.

The receiver then processes the lines in order, from the first to the
last, and applies rules 4 to 6 to each line, followed by rules 7 to 9 to
the type line or rules 10 to 12 to a field line:

{: start="4"}
4. The line is at most 8192 octets long, including its LF. Otherwise:
   line_too_long.
5. The line holds at least one octet before its LF. Otherwise:
   line_empty.
6. The octet before the LF of the line is not SP. Otherwise:
   line_trailing_space.

For the type line:

{: start="7"}
7. The line starts with the four octets "EOLA" followed by a DIGIT.
   Otherwise: type_line_magic.
8. The octets from the first DIGIT up to the next octet that is not a
   DIGIT, or up to the LF, are exactly "1". Otherwise:
   type_line_version.
9. The rest of the line, after "EOLA1" and before its LF, is one SP
   followed by a name. Otherwise: type_line_document_type.

For a field line, the field name is the longest sequence of octets at
the start of the line that contains no SP and no LF:

{: start="10"}
10. The field name matches the rule name of {{framing}}. Otherwise:
    field_name.
11. The field name is followed by SP. Otherwise: field_no_value.
12. The octet after that SP is not SP. Otherwise: field_separator.

A document that passes all twelve rules matches the grammar of
{{framing}} and is within its limits. The receiver then checks the
document type and the fields as the specification of that type
requires.

The order of the rules makes the error code of a document independent of
the implementation that reports it: every receiver reports the same
code for the same bytes, and the test vectors of EOLA check that code.

# Error Codes {#error-codes}

An error code has a name, used in the specifications and test vectors,
and a number, used by implementations that report codes as integers.
{{error-code-table}} lists the codes of this document. The numbers 1 to
99 are left to each implementation for errors that do not depend on the
document, such as an invalid argument to a function. The number 0 means
that no rule is broken.

| Number | Name                     | Rule |
|--------|--------------------------|------|
| 101    | document_too_large       | 1    |
| 102    | document_character       | 2    |
| 103    | document_unterminated    | 3    |
| 104    | line_too_long            | 4    |
| 105    | line_empty               | 5    |
| 106    | line_trailing_space      | 6    |
| 107    | type_line_magic          | 7    |
| 108    | type_line_version        | 8    |
| 109    | type_line_document_type  | 9    |
| 110    | field_name               | 10   |
| 111    | field_no_value           | 11   |
| 112    | field_separator          | 12   |
{: #error-code-table title="Framing Error Codes"}

# Security Considerations

A receiver processes documents from parties it does not trust: a
directory, a community server, a mirror, or a file a player supplies.
The limits of {{framing}} bound the memory and time a receiver spends on
a document, and the absence of escapes, quoting, and nesting keeps the
work of the parser linear in the length of the document, with no
recursion.

A receiver that repairs a malformed document, for example by dropping a
carriage return or a trailing space, accepts octets that differ from
those that were signed, and two receivers that repair differently reach
different results for the same document. The processing rules forbid
any such repair.

Rejecting control octets and octets above %x7E keeps a document free of
characters that display differently in different editors, so a person
who checks a document by reading it sees every octet the receiver
processes.

# IANA Considerations

This document has no IANA actions.

--- back

# Change Log
{:numbered="false"}

draft-wilczek-eola-signed-document-00:
: Initial version: framing, limits, processing rules, and error codes.
