/* SPDX-License-Identifier: MIT */
/* Copyright (C) 2026 Szymon Wilczek */
/*
 * Status codes of libeola. EOLA_STATUS_OK is 0. The codes from 100 up are
 * the error codes of the EOLA specifications, with the numbers given there;
 * the codes from 1 to 99 report errors that do not depend on a document.
 */
#ifndef EOLA_STATUS_H
#define EOLA_STATUS_H

/**
 * enum eola_status - result of a libeola function
 * @EOLA_STATUS_OK: the function succeeded
 * @EOLA_STATUS_INVALID_ARGUMENT: an argument is outside what the function
 *	accepts, as the Return section of the function lists
 * @EOLA_STATUS_CRYPTO_FAILURE: OpenSSL failed for a reason other than the
 *	document, for example to allocate memory; the document is neither
 *	accepted nor rejected
 * @EOLA_STATUS_DOCUMENT_TOO_LARGE: document_too_large
 * @EOLA_STATUS_DOCUMENT_CHARACTER: document_character
 * @EOLA_STATUS_DOCUMENT_UNTERMINATED: document_unterminated
 * @EOLA_STATUS_LINE_TOO_LONG: line_too_long
 * @EOLA_STATUS_LINE_EMPTY: line_empty
 * @EOLA_STATUS_LINE_TRAILING_SPACE: line_trailing_space
 * @EOLA_STATUS_TYPE_LINE_MAGIC: type_line_magic
 * @EOLA_STATUS_TYPE_LINE_VERSION: type_line_version
 * @EOLA_STATUS_TYPE_LINE_DOCUMENT_TYPE: type_line_document_type
 * @EOLA_STATUS_FIELD_NAME: field_name
 * @EOLA_STATUS_FIELD_NO_VALUE: field_no_value
 * @EOLA_STATUS_FIELD_SEPARATOR: field_separator
 * @EOLA_STATUS_DOCUMENT_TYPE_UNEXPECTED: document_type_unexpected
 * @EOLA_STATUS_VALUE_HEX: value_hex
 * @EOLA_STATUS_VALUE_HEX_LENGTH: value_hex_length
 * @EOLA_STATUS_VALUE_DECIMAL: value_decimal
 * @EOLA_STATUS_VALUE_DECIMAL_RANGE: value_decimal_range
 * @EOLA_STATUS_SIGNATURE_MISSING: signature_missing
 * @EOLA_STATUS_SIGNATURE_POSITION: signature_position
 * @EOLA_STATUS_SIGNER_MISSING: signer_missing
 * @EOLA_STATUS_SIGNER_POSITION: signer_position
 * @EOLA_STATUS_SIGNER_KEY_INVALID: signer_key_invalid
 * @EOLA_STATUS_SIGNER_UNEXPECTED: signer_unexpected
 * @EOLA_STATUS_SIGNATURE_INVALID: signature_invalid
 *
 * The description of each error code is in the Error Codes section of
 * draft-wilczek-eola-signed-document.
 */
enum eola_status {
	EOLA_STATUS_OK = 0,
	EOLA_STATUS_INVALID_ARGUMENT = 1,
	EOLA_STATUS_CRYPTO_FAILURE = 2,
	EOLA_STATUS_DOCUMENT_TOO_LARGE = 101,
	EOLA_STATUS_DOCUMENT_CHARACTER = 102,
	EOLA_STATUS_DOCUMENT_UNTERMINATED = 103,
	EOLA_STATUS_LINE_TOO_LONG = 104,
	EOLA_STATUS_LINE_EMPTY = 105,
	EOLA_STATUS_LINE_TRAILING_SPACE = 106,
	EOLA_STATUS_TYPE_LINE_MAGIC = 107,
	EOLA_STATUS_TYPE_LINE_VERSION = 108,
	EOLA_STATUS_TYPE_LINE_DOCUMENT_TYPE = 109,
	EOLA_STATUS_FIELD_NAME = 110,
	EOLA_STATUS_FIELD_NO_VALUE = 111,
	EOLA_STATUS_FIELD_SEPARATOR = 112,
	EOLA_STATUS_DOCUMENT_TYPE_UNEXPECTED = 113,
	EOLA_STATUS_VALUE_HEX = 201,
	EOLA_STATUS_VALUE_HEX_LENGTH = 202,
	EOLA_STATUS_VALUE_DECIMAL = 203,
	EOLA_STATUS_VALUE_DECIMAL_RANGE = 204,
	EOLA_STATUS_SIGNATURE_MISSING = 301,
	EOLA_STATUS_SIGNATURE_POSITION = 302,
	EOLA_STATUS_SIGNER_MISSING = 303,
	EOLA_STATUS_SIGNER_POSITION = 304,
	EOLA_STATUS_SIGNER_KEY_INVALID = 305,
	EOLA_STATUS_SIGNER_UNEXPECTED = 306,
	EOLA_STATUS_SIGNATURE_INVALID = 307,
};

/**
 * eola_status_name() - name of a status code
 * @status: the status code
 *
 * Return: the name of @status as the EOLA specifications and test vectors
 * write it, "ok" for EOLA_STATUS_OK, "invalid_argument" for
 * EOLA_STATUS_INVALID_ARGUMENT, "crypto_failure" for
 * EOLA_STATUS_CRYPTO_FAILURE, or NULL for a value that is not a status
 * code. The string is static.
 */
const char *eola_status_name(enum eola_status status);

#endif /* EOLA_STATUS_H */
