#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
"""Write the test vectors of the signed document format.

Each vector is a file in vectors/signed-document/, listed in the manifest
vectors/signed-document/vectors.txt with the check it is run through and
the result every implementation reports for it. Run with --check to
compare the files on disk with the ones this script writes.
"""

import argparse
import pathlib
import sys

DOCUMENT_MAX_LENGTH = 65536
LINE_MAX_LENGTH = 8192

DIRECTORY = pathlib.Path(__file__).resolve().parent / "signed-document"

MANIFEST_HEADER = """\
# SPDX-License-Identifier: CC-BY-4.0
# Copyright (C) 2026 Szymon Wilczek
#
# Test vectors of draft-wilczek-eola-signed-document. The license line
# covers this file and every file it lists. Written by vectors/generate.py;
# edit the script, not this file.
#
# Each line: <file> <check> <result>. The check "document" parses the file
# as a document; the result is "ok" or the name of the error code of the
# first processing rule the file breaks.
"""


def field_line_of_length(name, length):
    """Return a field line of exactly length octets, LF included."""
    value_length = length - len(name) - 2
    return f"{name} {'v' * value_length}\n".encode()


def document_of_length(length):
    """Return a valid document of exactly length octets."""
    type_line = b"EOLA1 padding\n"
    remaining = length - len(type_line)
    lines = []
    while remaining > 0:
        line_length = min(LINE_MAX_LENGTH, remaining)
        if 0 < remaining - line_length < 6:
            line_length -= 6
        lines.append(field_line_of_length("pad", line_length))
        remaining -= line_length
    document = type_line + b"".join(lines)
    assert len(document) == length
    return document


VECTORS = [
    # Documents that every receiver accepts.
    ("valid-type-line-only", b"EOLA1 heartbeat\n", "ok"),
    (
        "valid-fields",
        b"EOLA1 heartbeat\n"
        b"game_id 9f86d081884c7d659a2feaa0c55ad015\n"
        b"sequence 42\n"
        b"note two  spaces inside, punctuation !\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~\n",
        "ok",
    ),
    (
        "valid-repeated-field",
        b"EOLA1 directory\nserver a.example\nserver b.example\n",
        "ok",
    ),
    ("valid-name-digits-underscore", b"EOLA1 type_2\nkey_3_x 0\n", "ok"),
    ("valid-one-octet-value", b"EOLA1 a\nb c\n", "ok"),
    (
        "valid-line-at-limit",
        b"EOLA1 limit\n" + field_line_of_length("long", LINE_MAX_LENGTH),
        "ok",
    ),
    (
        "valid-document-at-limit",
        document_of_length(DOCUMENT_MAX_LENGTH),
        "ok",
    ),
    # Rule 1: document size.
    (
        "document-too-large",
        document_of_length(DOCUMENT_MAX_LENGTH + 1),
        "document_too_large",
    ),
    (
        "document-too-large-before-character",
        document_of_length(DOCUMENT_MAX_LENGTH)[:-1] + b"\r\n",
        "document_too_large",
    ),
    # Rule 2: octets.
    (
        "document-character-carriage-return",
        b"EOLA1 heartbeat\r\nsequence 1\r\n",
        "document_character",
    ),
    (
        "document-character-tab",
        b"EOLA1 heartbeat\nsequence\t1\n",
        "document_character",
    ),
    (
        "document-character-nul",
        b"EOLA1 heartbeat\nsequence 1\x00\n",
        "document_character",
    ),
    (
        "document-character-delete",
        b"EOLA1 heartbeat\nsequence 1\x7f\n",
        "document_character",
    ),
    (
        "document-character-utf8",
        "EOLA1 heartbeat\nnote zażółć\n".encode(),
        "document_character",
    ),
    (
        "document-character-before-unterminated",
        b"EOLA1 heartbeat\r",
        "document_character",
    ),
    # Rule 3: the document ends with LF.
    ("document-unterminated-empty", b"", "document_unterminated"),
    (
        "document-unterminated-last-line",
        b"EOLA1 heartbeat\nsequence 1",
        "document_unterminated",
    ),
    (
        "document-unterminated-before-line",
        b"EOLA1 heartbeat\n\nsequence 1",
        "document_unterminated",
    ),
    # Rule 4: line length.
    (
        "line-too-long-field",
        b"EOLA1 limit\n" + field_line_of_length("long", LINE_MAX_LENGTH + 1),
        "line_too_long",
    ),
    (
        "line-too-long-type-line",
        b"EOLA1 " + b"t" * (LINE_MAX_LENGTH - 6) + b"\n",
        "line_too_long",
    ),
    (
        "line-too-long-before-trailing-space",
        b"EOLA1 limit\n"
        + field_line_of_length("long", LINE_MAX_LENGTH + 1)[:-2]
        + b" \n",
        "line_too_long",
    ),
    # Rule 5: empty lines.
    ("line-empty-first", b"\nEOLA1 heartbeat\n", "line_empty"),
    (
        "line-empty-between-fields",
        b"EOLA1 heartbeat\nsequence 1\n\nnote x\n",
        "line_empty",
    ),
    ("line-empty-last", b"EOLA1 heartbeat\nsequence 1\n\n", "line_empty"),
    (
        "line-empty-before-later-line-too-long",
        b"EOLA1 limit\n\n" + field_line_of_length("long", LINE_MAX_LENGTH + 1),
        "line_empty",
    ),
    # Rule 6: trailing space.
    (
        "line-trailing-space-type-line",
        b"EOLA1 heartbeat \n",
        "line_trailing_space",
    ),
    (
        "line-trailing-space-field",
        b"EOLA1 heartbeat\nsequence 1 \n",
        "line_trailing_space",
    ),
    (
        "line-trailing-space-name-only",
        b"EOLA1 heartbeat\nsequence \n",
        "line_trailing_space",
    ),
    ("line-trailing-space-only", b"EOLA1 heartbeat\n \n", "line_trailing_space"),
    # Rule 7: the type line starts with EOLA and a digit.
    ("type-line-magic-lowercase", b"eola1 heartbeat\n", "type_line_magic"),
    ("type-line-magic-no-digit", b"EOLA heartbeat\n", "type_line_magic"),
    ("type-line-magic-field-first", b"sequence 1\n", "type_line_magic"),
    ("type-line-magic-short", b"EOL\n", "type_line_magic"),
    ("type-line-magic-leading-space", b" EOLA1 heartbeat\n", "type_line_magic"),
    # Rule 8: the version is 1.
    ("type-line-version-2", b"EOLA2 heartbeat\n", "type_line_version"),
    ("type-line-version-0", b"EOLA0 heartbeat\n", "type_line_version"),
    ("type-line-version-10", b"EOLA10 heartbeat\n", "type_line_version"),
    ("type-line-version-01", b"EOLA01 heartbeat\n", "type_line_version"),
    # Rule 9: one space and a name follow EOLA1.
    ("type-line-document-type-missing", b"EOLA1\n", "type_line_document_type"),
    (
        "type-line-document-type-no-space",
        b"EOLA1heartbeat\n",
        "type_line_document_type",
    ),
    (
        "type-line-document-type-two-spaces",
        b"EOLA1  heartbeat\n",
        "type_line_document_type",
    ),
    (
        "type-line-document-type-uppercase",
        b"EOLA1 Heartbeat\n",
        "type_line_document_type",
    ),
    (
        "type-line-document-type-inner-uppercase",
        b"EOLA1 heartBeat\n",
        "type_line_document_type",
    ),
    (
        "type-line-document-type-leading-digit",
        b"EOLA1 1heartbeat\n",
        "type_line_document_type",
    ),
    (
        "type-line-document-type-inner-space",
        b"EOLA1 heart beat\n",
        "type_line_document_type",
    ),
    (
        "type-line-document-type-hyphen",
        b"EOLA1 heart-beat\n",
        "type_line_document_type",
    ),
    (
        "type-line-document-type-before-field-error",
        b"EOLA1 Heartbeat\nSequence 1\n",
        "type_line_document_type",
    ),
    # Rule 10: field names.
    (
        "field-name-uppercase",
        b"EOLA1 heartbeat\nSequence 1\n",
        "field_name",
    ),
    (
        "field-name-inner-uppercase",
        b"EOLA1 heartbeat\nseQuence 1\n",
        "field_name",
    ),
    ("field-name-leading-digit", b"EOLA1 heartbeat\n1st x\n", "field_name"),
    (
        "field-name-leading-underscore",
        b"EOLA1 heartbeat\n_sequence 1\n",
        "field_name",
    ),
    ("field-name-hyphen", b"EOLA1 heartbeat\ngame-id x\n", "field_name"),
    ("field-name-empty", b"EOLA1 heartbeat\n sequence 1\n", "field_name"),
    (
        "field-name-before-no-value",
        b"EOLA1 heartbeat\nSequence\n",
        "field_name",
    ),
    # Rule 11: a space follows the field name.
    ("field-no-value", b"EOLA1 heartbeat\nsequence\n", "field_no_value"),
    (
        "field-no-value-after-valid-field",
        b"EOLA1 heartbeat\nsequence 1\nrevoked\n",
        "field_no_value",
    ),
    # Rule 12: one space separates the name and the value.
    (
        "field-separator-two-spaces",
        b"EOLA1 heartbeat\nsequence  1\n",
        "field_separator",
    ),
    (
        "field-separator-only-spaces",
        b"EOLA1 heartbeat\nsequence   x\n",
        "field_separator",
    ),
]


def expected_files():
    """Return the file names and contents this script writes."""
    files = {}
    manifest = [MANIFEST_HEADER]
    names = set()
    for name, content, result in VECTORS:
        assert name not in names, name
        names.add(name)
        file_name = name + ".eola"
        files[file_name] = content
        manifest.append(f"{file_name} document {result}\n")
    files["vectors.txt"] = "".join(manifest).encode()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="report files that differ from the generated ones",
    )
    arguments = parser.parse_args()

    files = expected_files()
    if arguments.check:
        on_disk = {path.name for path in DIRECTORY.iterdir()}
        differing = sorted(
            name
            for name in files
            if not (DIRECTORY / name).is_file()
            or (DIRECTORY / name).read_bytes() != files[name]
        )
        extra = sorted(on_disk - set(files))
        for name in differing:
            print(f"differs from the generated file: {name}")
        for name in extra:
            print(f"not written by the generator: {name}")
        return 1 if differing or extra else 0

    DIRECTORY.mkdir(exist_ok=True)
    for name, content in files.items():
        (DIRECTORY / name).write_bytes(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
