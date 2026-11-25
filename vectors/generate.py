#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (C) 2026 Szymon Wilczek
"""Write the test vectors of the signed document format.

Each vector is a file in vectors/signed-document/, listed in the manifest
vectors/signed-document/vectors.txt with the check it is run through and
the result every implementation reports for it. The signed vectors are
signed with the test keys of vectors/signed-document/test-keys.txt. Run
with --check to compare the files on disk with the ones this script
writes.
"""

import argparse
import hashlib
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
# as a document, "hex:<n>" decodes it as a hexadecimal value of n octets,
# and "decimal" as a decimal value. The check "verify:<type>:<key>"
# verifies the file as a signed document of the document type <type>,
# signed by the Ed25519 public key <key> in hexadecimal. The result is "ok"
# or the name of the error code of the first processing rule the file
# breaks.
"""

TEST_KEYS_HEADER = """\
# SPDX-License-Identifier: CC-BY-4.0
# Copyright (C) 2026 Szymon Wilczek
#
# Ed25519 test keys of the signed vectors of
# draft-wilczek-eola-signed-document. Their private keys are public: they
# sign nothing but test vectors. Written by vectors/generate.py; edit the
# script, not this file.
#
# Each line: <name> <seed> <public key>, in hexadecimal. The seed is the
# private key of RFC 8032, Section 5.1.5.
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


# Field values: (name, check, value, result). The check "hex:<n>" decodes
# the file as a hexadecimal value of n octets, "decimal" as a decimal value.
VALUE_VECTORS = [
    ("value-hex-valid-one-octet", "hex:1", b"00", "ok"),
    ("value-hex-valid-four-octets", "hex:4", b"9f86d081", "ok"),
    (
        "value-hex-valid-thirty-two-octets",
        "hex:32",
        b"9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
        "ok",
    ),
    ("value-hex-valid-all-digits", "hex:8", b"0123456789abcdef", "ok"),
    ("value-hex-uppercase", "hex:4", b"9F86D081", "value_hex"),
    ("value-hex-odd-length", "hex:4", b"9f86d08", "value_hex"),
    ("value-hex-non-digit", "hex:4", b"9f86d0g1", "value_hex"),
    ("value-hex-prefix", "hex:4", b"0x9f86d0", "value_hex"),
    ("value-hex-separator", "hex:4", b"9f86 d081", "value_hex"),
    ("value-hex-empty", "hex:4", b"", "value_hex"),
    ("value-hex-uppercase-wrong-length", "hex:4", b"9F86", "value_hex"),
    ("value-hex-short", "hex:4", b"9f86d0", "value_hex_length"),
    ("value-hex-long", "hex:4", b"9f86d08100", "value_hex_length"),
    ("value-decimal-valid-zero", "decimal", b"0", "ok"),
    ("value-decimal-valid", "decimal", b"42", "ok"),
    (
        "value-decimal-valid-maximum",
        "decimal",
        b"18446744073709551615",
        "ok",
    ),
    ("value-decimal-leading-zero", "decimal", b"007", "value_decimal"),
    ("value-decimal-zeros", "decimal", b"00", "value_decimal"),
    ("value-decimal-sign", "decimal", b"-1", "value_decimal"),
    ("value-decimal-plus", "decimal", b"+1", "value_decimal"),
    ("value-decimal-separator", "decimal", b"1 000", "value_decimal"),
    ("value-decimal-exponent", "decimal", b"1e3", "value_decimal"),
    ("value-decimal-hex", "decimal", b"0x10", "value_decimal"),
    ("value-decimal-empty", "decimal", b"", "value_decimal"),
    (
        "value-decimal-leading-zero-over-range",
        "decimal",
        b"018446744073709551616",
        "value_decimal",
    ),
    (
        "value-decimal-over-range",
        "decimal",
        b"18446744073709551616",
        "value_decimal_range",
    ),
    (
        "value-decimal-over-range-twenty-digits",
        "decimal",
        b"99999999999999999999",
        "value_decimal_range",
    ),
    (
        "value-decimal-over-range-twenty-one-digits",
        "decimal",
        b"100000000000000000000",
        "value_decimal_range",
    ),
]


# Ed25519 of RFC 8032, Section 5.1, for the signed vectors: written to be
# read against the RFC, not to be fast or to run in constant time.
# It signs only the public test keys below.
P = 2**255 - 19
L = 2**252 + 27742317777372353535851937790883648493
D = -121665 * pow(121666, -1, P) % P
SQRT_MINUS_ONE = pow(2, (P - 1) // 4, P)
IDENTITY = (0, 1)


def point_add(first, second):
    """Return the sum of two points in affine coordinates."""
    x1, y1 = first
    x2, y2 = second
    product = D * x1 * x2 * y1 * y2 % P
    x = (x1 * y2 + x2 * y1) * pow(1 + product, -1, P) % P
    y = (y1 * y2 + x1 * x2) * pow(1 - product, -1, P) % P
    return x, y


def point_multiply(scalar, point):
    """Return the point multiplied by a nonnegative scalar."""
    result = IDENTITY
    while scalar:
        if scalar & 1:
            result = point_add(result, point)
        point = point_add(point, point)
        scalar >>= 1
    return result


def point_decode(encoded):
    """Return the point of an encoding, as RFC 8032, Section 5.1.3."""
    value = int.from_bytes(encoded, "little")
    y, sign = value & ((1 << 255) - 1), value >> 255
    assert y < P
    u, v = (y * y - 1) % P, (D * y * y + 1) % P
    x = u * pow(v, 3, P) * pow(u * pow(v, 7, P), (P - 5) // 8, P) % P
    if (v * x * x - u) % P != 0:
        x = x * SQRT_MINUS_ONE % P
    assert (v * x * x - u) % P == 0, "not a point of the curve"
    assert x != 0 or sign == 0
    return (P - x if x & 1 != sign else x), y


def point_encode(point, y_offset=0):
    """Return the encoding of a point, as RFC 8032, Section 5.1.2.

    A y_offset of P writes the y-coordinate plus P: an encoding that is
    not canonical, for the vectors that must reject one.
    """
    x, y = point
    return ((y + y_offset) | (x & 1) << 255).to_bytes(32, "little")


BASE = point_decode(
    bytes.fromhex(
        "5866666666666666666666666666666666666666666666666666666666666666"
    )
)

# A point of order 8, from the list of points of small order.
ORDER_EIGHT = point_decode(
    bytes.fromhex(
        "c7176a703d4dd84fba3c0b760d10670f2a2053fa2c39ccc64ec7fd7792ac037a"
    )
)
assert point_multiply(8, ORDER_EIGHT) == IDENTITY
assert point_multiply(4, ORDER_EIGHT) != IDENTITY


def sha512_integer(*parts):
    """Return SHA-512 of the concatenated parts as a little-endian integer."""
    return int.from_bytes(hashlib.sha512(b"".join(parts)).digest(), "little")


def expand_seed(seed):
    """Return the secret scalar and the prefix of a seed."""
    digest = hashlib.sha512(seed).digest()
    scalar = int.from_bytes(digest[:32], "little")
    scalar &= (1 << 254) - 8
    scalar |= 1 << 254
    return scalar, digest[32:]


def public_key(seed):
    """Return the public key of a seed."""
    return point_encode(point_multiply(expand_seed(seed)[0], BASE))


def challenge(encoded_r, key, message):
    """Return the scalar k of RFC 8032, Section 5.1.6, step 5."""
    return sha512_integer(encoded_r, key, message) % L


def sign(seed, message):
    """Return the Ed25519 signature of a message, RFC 8032, Section 5.1.6."""
    scalar, prefix = expand_seed(seed)
    key = public_key(seed)
    nonce = sha512_integer(prefix, message) % L
    encoded_r = point_encode(point_multiply(nonce, BASE))
    s = (nonce + challenge(encoded_r, key, message) * scalar) % L
    return encoded_r + s.to_bytes(32, "little")


# Tests 1 and 2 of RFC 8032, Section 7.1.
for _seed, _key, _message, _signature in [
    (
        "9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60",
        "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a",
        "",
        (
            "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555"
            "fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
        ),
    ),
    (
        "4ccd089b28ff96da9db6c346ec114e0f5b8a319f35aba624da8cf6ed4fb8a6fb",
        "3d4017c3e843895a92b70aa74d1b7ebc9c982ccf2ec4968cc0cd55f12af4660c",
        "72",
        (
            "92a009a9f0d4cab8720e820b5f642540a2b27b5416503f8fb3762223ebdb69da0"
            "85ac1e43e15996e458f3613d0f11d8c387b2eaeb4302aeeb00d291612bb0c00"
        ),
    ),
]:
    assert public_key(bytes.fromhex(_seed)).hex() == _key
    assert sign(bytes.fromhex(_seed), bytes.fromhex(_message)).hex() == _signature


TEST_SEEDS = {
    name: hashlib.sha256(b"EOLA test key " + name.encode()).digest()
    for name in ("publisher", "other")
}
PUBLISHER = public_key(TEST_SEEDS["publisher"])
OTHER = public_key(TEST_SEEDS["other"])

HEARTBEAT = b"EOLA1 heartbeat\nsequence 42\n"
SIGNER_LINE_LENGTH = len("signer \n") + 64
SIGNATURE_LINE_LENGTH = len("signature \n") + 128


def signer_line(key):
    return b"signer " + key.hex().encode() + b"\n"


def signature_line(signature):
    return b"signature " + signature.hex().encode() + b"\n"


def signed(body, key_name="publisher"):
    """Return body with the signer and signature lines of a test key."""
    seed = TEST_SEEDS[key_name]
    message = body + signer_line(public_key(seed))
    return message + signature_line(sign(seed, message))


def flip_bit(octets, index):
    """Return octets with the low bit of the octet at index flipped."""
    changed = bytearray(octets)
    changed[index] ^= 1
    return bytes(changed)


def with_bad_signature(document):
    """Return a signed document whose last signature digit is changed."""
    last = document[-2:-1]
    return document[:-2] + (b"1" if last == b"0" else b"0") + b"\n"


def point_decode_lenient(encoded):
    """Return the point of an encoding as a lenient decoder reads it.

    The y-coordinate is taken mod p, and the sign bit of x = 0 is ignored.
    """
    value = int.from_bytes(encoded, "little")
    x, y = point_decode(((value & ((1 << 255) - 1)) % P).to_bytes(32, "little"))
    return (P - x if x & 1 != value >> 255 and x != 0 else x), y


def forged_for_key(key, body):
    """Return a document signed for a key of small order, with no secret.

    R = [s]B and S = s satisfy the equation of RFC 8032 for a key A with
    [k]A the identity. The nonce s is the first from 12345 that gives such
    a k for the message.
    """
    message = body + signer_line(key)
    point_a = point_decode_lenient(key)
    nonce = 12345
    while True:
        encoded_r = point_encode(point_multiply(nonce, BASE))
        k = challenge(encoded_r, key, message)
        if point_multiply(k, point_a) == IDENTITY:
            break
        nonce += 1
    return message + signature_line(encoded_r + nonce.to_bytes(32, "little"))


def signed_with_r(body, point_r, y_offset=0):
    """Return a document of the publisher signed with a chosen R."""
    scalar = expand_seed(TEST_SEEDS["publisher"])[0]
    message = body + signer_line(PUBLISHER)
    encoded_r = point_encode(point_r, y_offset)
    nonce = 0 if point_r == IDENTITY else 777
    s = (nonce + challenge(encoded_r, PUBLISHER, message) * scalar) % L
    return message + signature_line(encoded_r + s.to_bytes(32, "little"))


def off_curve_key():
    """Return the encoding with the smallest y that is not on the curve."""
    for y in range(2, P):
        try:
            point_decode(y.to_bytes(32, "little"))
        except AssertionError:
            return y.to_bytes(32, "little")
    raise AssertionError


def verify_check(document_type, key):
    return f"verify:{document_type}:{key.hex()}"


def signed_vectors():
    """Return the signed vectors as (name, check, content, result)."""
    valid = signed(HEARTBEAT)
    valid_signature = bytes.fromhex(valid.split(b" ")[-1].decode())
    with_signer = HEARTBEAT + signer_line(PUBLISHER)
    heartbeat = verify_check("heartbeat", PUBLISHER)
    largest_body = document_of_length(
        DOCUMENT_MAX_LENGTH - SIGNER_LINE_LENGTH - SIGNATURE_LINE_LENGTH
    )
    noncanonical_identity = point_encode(IDENTITY, P)
    # y = p, the point (sqrt(-1), 0) of order 4: the smallest y that is
    # not less than p.
    y_is_p = P.to_bytes(32, "little")
    # x = 0 with the sign bit set: y = 1, the identity, and y = p - 1, the
    # point of order 2.
    negative_zero = bytes.fromhex("01" + "00" * 30 + "80")
    negative_zero_order_two = bytes.fromhex("ec" + "ff" * 31)
    off_curve = off_curve_key()

    vectors = [
        # Signed documents that every receiver accepts.
        ("signed-valid", heartbeat, valid, "ok"),
        (
            "signed-valid-no-other-field",
            heartbeat,
            signed(b"EOLA1 heartbeat\n"),
            "ok",
        ),
        (
            "signed-valid-largest",
            verify_check("padding", PUBLISHER),
            signed(largest_body),
            "ok",
        ),
        # The framing is checked before the signature.
        (
            "signed-line-trailing-space",
            heartbeat,
            signed(b"EOLA1 heartbeat\nsequence 42 \n"),
            "line_trailing_space",
        ),
        # Rule 17: the document type is the one the receiver expects.
        (
            "signed-document-type-unexpected",
            verify_check("passport", PUBLISHER),
            valid,
            "document_type_unexpected",
        ),
        (
            "signed-document-type-unexpected-prefix",
            heartbeat,
            signed(b"EOLA1 heart\nsequence 42\n"),
            "document_type_unexpected",
        ),
        (
            "signed-document-type-unexpected-longer",
            heartbeat,
            signed(b"EOLA1 heartbeat_v2\nsequence 42\n"),
            "document_type_unexpected",
        ),
        (
            "signed-document-type-unexpected-bad-signature",
            verify_check("passport", PUBLISHER),
            with_bad_signature(valid),
            "document_type_unexpected",
        ),
        # Rule 18: a field is named signature.
        (
            "signed-signature-missing-no-field",
            heartbeat,
            b"EOLA1 heartbeat\n",
            "signature_missing",
        ),
        (
            "signed-signature-missing-signer-last",
            heartbeat,
            with_signer,
            "signature_missing",
        ),
        (
            "signed-signature-missing-similar-name",
            heartbeat,
            with_signer + b"signatures " + valid_signature.hex().encode() + b"\n",
            "signature_missing",
        ),
        # Rule 19: the last field is the only field named signature.
        (
            "signed-signature-position-twice",
            heartbeat,
            valid + signature_line(valid_signature),
            "signature_position",
        ),
        (
            "signed-signature-position-field-after",
            heartbeat,
            valid + b"sequence 43\n",
            "signature_position",
        ),
        (
            "signed-signature-position-earlier",
            heartbeat,
            signed(HEARTBEAT + b"signature 00\n"),
            "signature_position",
        ),
        (
            "signed-signature-position-signer-after",
            heartbeat,
            HEARTBEAT + signature_line(valid_signature) + signer_line(PUBLISHER),
            "signature_position",
        ),
        # Rule 20: a field is named signer.
        (
            "signed-signer-missing",
            heartbeat,
            HEARTBEAT + signature_line(valid_signature),
            "signer_missing",
        ),
        (
            "signed-signer-missing-similar-name",
            heartbeat,
            HEARTBEAT
            + b"signers "
            + PUBLISHER.hex().encode()
            + b"\n"
            + signature_line(valid_signature),
            "signer_missing",
        ),
        # Rule 21: the field before the last is the only field named signer.
        (
            "signed-signer-position-twice",
            heartbeat,
            signed(HEARTBEAT + signer_line(PUBLISHER)),
            "signer_position",
        ),
        (
            "signed-signer-position-earlier",
            heartbeat,
            with_signer + b"sequence 43\n" + signature_line(valid_signature),
            "signer_position",
        ),
        # Rules 13 and 14, for the signer value and then the signature value.
        (
            "signed-signer-value-uppercase",
            heartbeat,
            HEARTBEAT
            + b"signer "
            + PUBLISHER.hex().upper().encode()
            + b"\n"
            + signature_line(valid_signature),
            "value_hex",
        ),
        (
            "signed-signer-value-short",
            heartbeat,
            HEARTBEAT + signer_line(PUBLISHER[:31]) + signature_line(valid_signature),
            "value_hex_length",
        ),
        (
            "signed-signature-value-uppercase",
            heartbeat,
            with_signer
            + b"signature "
            + valid_signature.hex().upper().encode()
            + b"\n",
            "value_hex",
        ),
        (
            "signed-signature-value-long",
            heartbeat,
            with_signer + signature_line(valid_signature + b"\x00"),
            "value_hex_length",
        ),
        (
            "signed-signer-value-before-signature-value",
            heartbeat,
            HEARTBEAT
            + signer_line(PUBLISHER[:31])
            + b"signature "
            + valid_signature.hex().upper().encode()
            + b"\n",
            "value_hex_length",
        ),
        # Rule 22: the signer is the key the receiver expects.
        (
            "signed-signer-unexpected",
            heartbeat,
            signed(HEARTBEAT, "other"),
            "signer_unexpected",
        ),
        (
            "signed-signer-unexpected-bad-signature",
            heartbeat,
            with_bad_signature(signed(HEARTBEAT, "other")),
            "signer_unexpected",
        ),
        # Rule 23: the signature is valid for the signed octets.
        (
            "signed-signature-invalid-field",
            heartbeat,
            valid.replace(b"sequence 42", b"sequence 43"),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-type",
            heartbeat,
            signed(b"EOLA1 passport\nsequence 42\n").replace(
                b"passport", b"heartbeat"
            ),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-signer-line",
            heartbeat,
            with_signer
            + signature_line(
                sign(TEST_SEEDS["publisher"], HEARTBEAT + signer_line(OTHER))
            ),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-signer-line-unsigned",
            heartbeat,
            with_signer + signature_line(sign(TEST_SEEDS["publisher"], HEARTBEAT)),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-r",
            heartbeat,
            with_signer + signature_line(flip_bit(valid_signature, 0)),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-s",
            heartbeat,
            with_signer + signature_line(flip_bit(valid_signature, 32)),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-s-plus-l",
            heartbeat,
            with_signer
            + signature_line(
                valid_signature[:32]
                + (int.from_bytes(valid_signature[32:], "little") + L).to_bytes(
                    32, "little"
                )
            ),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-s-l",
            heartbeat,
            with_signer
            + signature_line(valid_signature[:32] + L.to_bytes(32, "little")),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-s-maximum",
            heartbeat,
            with_signer + signature_line(valid_signature[:32] + b"\xff" * 32),
            "signature_invalid",
        ),
        # R is the identity written with y + p: valid if R were decoded
        # without the canonical check.
        (
            "signed-signature-invalid-r-noncanonical",
            heartbeat,
            signed_with_r(HEARTBEAT, IDENTITY, P),
            "signature_invalid",
        ),
        # R has a component of order 8: valid for the equation with the
        # cofactor, not for the equation without it.
        (
            "signed-signature-invalid-r-mixed-order",
            heartbeat,
            signed_with_r(
                HEARTBEAT, point_add(point_multiply(777, BASE), ORDER_EIGHT)
            ),
            "signature_invalid",
        ),
        # Keys that are not the canonical encoding of a point: a forged
        # signature is valid for them if they were decoded without the
        # canonical check.
        (
            "signed-signature-invalid-key-noncanonical",
            verify_check("heartbeat", noncanonical_identity),
            forged_for_key(noncanonical_identity, HEARTBEAT),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-key-noncanonical-p",
            verify_check("heartbeat", y_is_p),
            forged_for_key(y_is_p, HEARTBEAT),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-key-negative-zero",
            verify_check("heartbeat", negative_zero),
            forged_for_key(negative_zero, HEARTBEAT),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-key-negative-zero-order-two",
            verify_check("heartbeat", negative_zero_order_two),
            forged_for_key(negative_zero_order_two, HEARTBEAT),
            "signature_invalid",
        ),
        (
            "signed-signature-invalid-key-off-curve",
            verify_check("heartbeat", off_curve),
            HEARTBEAT
            + signer_line(off_curve)
            + signature_line(valid_signature),
            "signature_invalid",
        ),
    ]
    return vectors


def expected_files():
    """Return the file names and contents this script writes."""
    files = {}
    manifest = [MANIFEST_HEADER]
    names = set()
    vectors = [
        (name, "document", content, result) for name, content, result in VECTORS
    ]
    for name, check, content, result in vectors + VALUE_VECTORS + signed_vectors():
        assert name not in names, name
        names.add(name)
        file_name = name + ".eola"
        files[file_name] = content
        manifest.append(f"{file_name} {check} {result}\n")
    files["vectors.txt"] = "".join(manifest).encode()
    files["test-keys.txt"] = (
        TEST_KEYS_HEADER
        + "".join(
            f"{name} {seed.hex()} {public_key(seed).hex()}\n"
            for name, seed in TEST_SEEDS.items()
        )
    ).encode()
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
