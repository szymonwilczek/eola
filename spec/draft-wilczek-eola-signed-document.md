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
  - Ed25519
author:
  -
    fullname: Szymon Wilczek
    email: swilczek.lx@gmail.com

normative:
  RFC20:
  RFC5234:
  RFC7405:
  RFC8032:

informative:
  EDDSA-VARIANTS:
    title: Taming the many EdDSAs
    author:
      - ins: K. Chalkias
        name: Konstantinos Chalkias
      - ins: F. Garillot
        name: François Garillot
      - ins: V. Nikolaenko
        name: Valeria Nikolaenko
    date: 2020
    seriesinfo:
      DOI: 10.1007/978-3-030-64357-7_4
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
strict subset of ASCII, with fixed size limits, and the hexadecimal and
decimal encodings of field values, and the Ed25519 signature that ends
every document. It defines the order in which a receiver checks a
document, a value, and a signature, and the error code it reports for
each rule they break.

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
encodings of field values, the signature of a document, the processing
rules a receiver applies, and their error codes. The document types, their
fields, the order of those fields, and the encoding of each value are
defined by the EOLA document that specifies each type.

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

Signed message:
: The octets of a document that its signature covers ({{signature}}).

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
{{framing}} and is within its limits. The receiver then checks its
signature with the rules of {{signature-processing}}, and only then the
fields as the specification of the document type requires.

The order of the rules makes the error code of a document independent of
the implementation that reports it: every receiver reports the same
code for the same bytes, and the test vectors of EOLA check that code.

# Field Values {#values}

The specification of a document type gives the encoding of each of its
field values: text, a hexadecimal value of a stated number of octets, or
a decimal value.

~~~ abnf
hex-value     = 1*hex-octet
hex-octet     = 2( DIGIT / %x61-66 )

decimal-value = "0" / ( %x31-39 *DIGIT )
~~~

A hexadecimal value encodes each octet as two lowercase hexadecimal
digits, the most significant first. A field of n octets holds exactly 2n
digits. Uppercase digits, a prefix such as "0x", and separators are not
part of the encoding.

A decimal value encodes an unsigned integer from 0 to 2^64-1,
18446744073709551615, with no sign and no leading zero.

Each value has exactly one encoding, so a value read from a document and
encoded again gives the octets of the document.

## Value Processing Rules

A receiver MUST check a field value against the rules of its encoding,
in the order given, and MUST reject the document at the first rule the
value breaks, with the error code of that rule. The receiver checks the
values of the signer and signature fields as {{signature-processing}}
states, and the values of the other fields after the document passes
rule 24, in the order of the fields.

For a hexadecimal value of n octets:

{: start="13"}
13. The value matches the rule hex-value. Otherwise: value_hex.
14. The value holds exactly 2n octets. Otherwise: value_hex_length.

For a decimal value:

{: start="15"}
15. The value matches the rule decimal-value. Otherwise:
    value_decimal.
16. The integer it encodes is at most 18446744073709551615. Otherwise:
    value_decimal_range.

# Signature {#signature}

Every document of EOLA is signed. The last two fields of a signed
document are the field signer, which holds the public key that signed
it, and the field signature, which holds the signature:

~~~ abnf
signed-document = type-line *field-line signer-line signature-line

signer-line     = %s"signer" SP 32hex-octet LF
signature-line  = %s"signature" SP 64hex-octet LF
~~~

The signature is an Ed25519 signature {{RFC8032}}. The value of the
signer field is the 32 octets of the public key, encoded as Section
5.1.2 of {{RFC8032}} gives, and the value of the signature field is the
64 octets of the signature of Section 5.1.6 of {{RFC8032}}; both are
hexadecimal values ({{values}}).

The signed message is every octet of the document from its first octet
up to, and including, the LF that ends the signer line: the whole
document except its signature line. The type line and the signer line
are therefore signed.

The field names signer and signature are reserved: a document contains
each of them exactly once, in the positions above, and the specification
of a document type defines neither. A signed document thus ends at its
signature line, and a receiver splits it into the signed message and the
signature in exactly one way.

This document fixes the signature algorithm, and no field names it: the
party that creates a document cannot choose the algorithm a receiver
verifies it with. Ed25519 is used without a context, as Ed25519 and not
Ed25519ctx or Ed25519ph. Every signed message starts with the type line,
"EOLA1", SP, its document type, and LF, so a signature that is valid for
a document of one type is not valid for a document of another type. A
key that signs EOLA documents MUST NOT sign any other message.

## Signature Processing Rules {#signature-processing}

A receiver knows, before it processes a document, the document type it
expects and the public key it expects the document to be signed with.
The specification of each document type states how the receiver obtains
that key.

After rules 1 to 12, the receiver MUST apply the rules below, in the
order given, and MUST reject the document at the first rule it breaks
with the error code of that rule:

{: start="17"}
17. The document type is the type the receiver expects. Otherwise:
    document_type_unexpected.
18. A field of the document is named signature. Otherwise:
    signature_missing.
19. The last field is the only field named signature. Otherwise:
    signature_position.
20. A field of the document is named signer. Otherwise: signer_missing.
21. The field before the last is the only field named signer.
    Otherwise: signer_position.

The receiver then applies rules 13 and 14 to the value of the signer
field, as a hexadecimal value of 32 octets, and then to the value of the
signature field, as a hexadecimal value of 64 octets.

{: start="22"}
22. The value of the signer field is a public key that a signature
    binds to its holder, as {{signer-keys}} defines. Otherwise:
    signer_key_invalid.
23. The value of the signer field is the public key the receiver
    expects. Otherwise: signer_unexpected.
24. The signature is valid for the signed message and the public key,
    as Section 5.1.7 of {{RFC8032}} verifies it with the choices below.
    Otherwise: signature_invalid.

Section 5.1.7 of {{RFC8032}} leaves a verifier some choices, and
implementations of Ed25519 make them differently {{EDDSA-VARIANTS}}.
For rule 24 a receiver makes them as follows, so that every receiver
accepts and rejects the same signatures:

- It rejects a signature whose S, the integer of the last 32 octets of
  the signature, is not less than L, the order of the base point.
- It decodes the public key A and the point R, the first 32 octets of the
  signature, as Section 5.1.3 of {{RFC8032}} gives, and rejects the
  signature when either decoding fails. An encoding whose y-coordinate is
  not less than p, or whose x-coordinate is 0 with its sign bit set, fails
  to decode.
- It checks the equation \[S\]B = R + \[k\]A without the cofactor 8.

A document that passes rule 24 is signed with the public key the
receiver expects. The receiver does not act on any field of a document,
other than the type line, before the document passes rule 24.

## Signer Keys {#signer-keys}

A public key breaks rule 22 when its 32 octets are any of the
following:

- An encoding whose y-coordinate, its low 255 bits, is not less than p.
  Such an encoding is not the encoding of Section 5.1.2 of {{RFC8032}},
  and some implementations decode it to the point of y mod p.
- An encoding with an x-coordinate of 0 and the sign bit set. Decoding
  fails for it, and some implementations decode it to the point with
  the sign bit clear.
- The encoding of a point whose order divides 8, the cofactor. For such
  a key A, \[k\]A is the identity whenever k is a multiple of 8, so that
  anyone can make, for any message and without a private key, a
  signature that the equation of rule 24 accepts, by trying on average
  at most 8 values of R. These are the eight encodings, in hexadecimal:

~~~
0000000000000000000000000000000000000000000000000000000000000000
0000000000000000000000000000000000000000000000000000000000000080
0100000000000000000000000000000000000000000000000000000000000000
26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc05
26e8958fc2b227b045c3f489f2ef98f0d5dfac05d3c63339b13802886d53fc85
c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a
c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac03fa
ecffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff7f
~~~

The public key of every private key of Section 5.1.5 of {{RFC8032}} is a
point of order L, so rule 22 rejects no key that a signer generates. A
key that is not the encoding of a point of the curve passes rule 22 and
fails to decode at rule 24.

# Error Codes {#error-codes}

An error code has a name, used in the specifications and test vectors,
and a number, used by implementations that report codes as integers.
{{error-code-table}} lists the codes of this document: the numbers from
101 report the framing, those from 201 report field values, and those
from 301 report the signature. The
numbers 1 to 99 are left to each implementation for errors that do not
depend on the document, such as an invalid argument to a function. The
number 0 means that no rule is broken.

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
| 113    | document_type_unexpected | 17   |
| 201    | value_hex                | 13   |
| 202    | value_hex_length         | 14   |
| 203    | value_decimal            | 15   |
| 204    | value_decimal_range      | 16   |
| 301    | signature_missing        | 18   |
| 302    | signature_position       | 19   |
| 303    | signer_missing           | 20   |
| 304    | signer_position          | 21   |
| 305    | signer_key_invalid       | 22   |
| 306    | signer_unexpected        | 23   |
| 307    | signature_invalid        | 24   |
{: #error-code-table title="Error Codes"}

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

A value with more than one encoding would let a party change the octets
of a signed document without changing what a receiver reads from it,
for example by writing a hexadecimal value in uppercase. The single
encoding of each value rules this out, and a receiver that accepts a
document reads the same values as any other receiver.

Rejecting control octets and octets above %x7E keeps a document free of
characters that display differently in different editors, so a person
who checks a document by reading it sees every octet the receiver
processes.

The signed message is every octet of the document but the signature
line, so a change to any octet a receiver reads, the type line and the
signer line included, makes the signature invalid. Because the reserved
fields stand only at the end, a receiver never chooses which octets the
signature covers.

A receiver trusts a document because its signer is the key the receiver
expects (rule 23), never because the document names a key. The signer
field states the key a document claims to be signed with, so that a
document signed with another key is reported as signer_unexpected and
not only as an invalid signature.

A receiver acts on no field of a document before the signature is valid,
so an unsigned or forged document never reaches the code that interprets
a document type.

A signature made with a key of small order binds no one: anyone forges
one for that key. Rule 22 rejects a document that names such a key
before the key is compared with the key the receiver expects. A
receiver given such a key, by mistake or by a dishonest publisher,
thus accepts no document: a document that names the key breaks rule
22, and a document that names another key breaks rule 23. It never
accepts a document that the publisher can later claim to be forged.

The choices of {{signature-processing}} remove the differences between
implementations of Ed25519: without them, one receiver could accept a
signature that another rejects, and a party could send each receiver a
document that only that receiver accepts.

Ed25519 is not resistant to an attacker with a cryptographically
relevant quantum computer. Documents in this format are expected to be
verified decades after they are signed, so such an attacker could forge,
in particular, an end-of-life message and open an escrow early. This
revision of the draft does not address that risk.

# IANA Considerations

This document has no IANA actions.

--- back

# Change Log
{:numbered="false"}

draft-wilczek-eola-signed-document-00:
: Initial version: framing, limits, value encodings, the Ed25519
  signature, processing rules, and error codes.
